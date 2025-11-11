"""
Eligibility Checker Service
High-level service that combines matching, ranking, and retrieval
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_processing.scheme_models import GovernmentScheme, UserProfile
from eligibility.matcher import EligibilityMatcher, SchemeMatch
from eligibility.ranker import SchemeRanker, RankedScheme, RankingStrategy
from retrieval.vector_store import QdrantVectorStore, HybridRetriever
from embeddings.bge_embedder import BGEEmbedder
from utils import load_config, get_env_variable

logger = logging.getLogger(__name__)


class EligibilityCheckerService:
    """
    Complete eligibility checking service
    Integrates matching, ranking, and vector search
    """

    def __init__(
        self,
        vector_store: Optional[QdrantVectorStore] = None,
        embedder: Optional[BGEEmbedder] = None,
        matcher: Optional[EligibilityMatcher] = None,
        ranker: Optional[SchemeRanker] = None,
        config: Optional[Dict] = None,
    ):
        """
        Initialize eligibility checker service

        Args:
            vector_store: Qdrant vector store
            embedder: BGE embedder
            matcher: Eligibility matcher
            ranker: Scheme ranker
            config: Configuration dictionary
        """
        self.config = config or load_config()

        # Initialize components if not provided
        if matcher is None:
            eligibility_config = self.config.get('eligibility', {})
            matcher = EligibilityMatcher(
                strict_mode=eligibility_config.get('strict_mode', False),
                min_match_score=eligibility_config.get('min_match_score', 0.6),
                boost_factors=eligibility_config.get('boost_factors', {}),
            )
        self.matcher = matcher

        if ranker is None:
            ranker = SchemeRanker(
                strategy=RankingStrategy.COMBINED,
                benefit_weight=0.5,
                eligibility_weight=0.3,
                ease_weight=0.2,
            )
        self.ranker = ranker

        self.vector_store = vector_store
        self.embedder = embedder

        # Cache for loaded schemes
        self._scheme_cache: Optional[List[GovernmentScheme]] = None

    def check_eligibility_for_all_schemes(
        self,
        user_profile: UserProfile,
        schemes: Optional[List[GovernmentScheme]] = None,
        rank_results: bool = True,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Check user eligibility against all schemes

        Args:
            user_profile: User's profile
            schemes: List of schemes (loads from cache/DB if not provided)
            rank_results: Whether to rank eligible schemes
            user_preferences: Optional user preferences for ranking

        Returns:
            Dictionary with eligible schemes, rankings, and summary
        """
        # Load schemes if not provided
        if schemes is None:
            schemes = self._get_all_schemes()

        logger.info(f"Checking eligibility for {len(schemes)} schemes")

        # Check eligibility for each scheme
        matches: List[SchemeMatch] = []
        for scheme in schemes:
            match = self.matcher.check_eligibility(user_profile, scheme)
            matches.append(match)

        # Separate eligible and ineligible
        eligible_matches = [m for m in matches if m.is_eligible]
        ineligible_matches = [m for m in matches if not m.is_eligible]

        logger.info(f"Found {len(eligible_matches)} eligible schemes")

        # Rank eligible schemes
        ranked_schemes = []
        if rank_results and eligible_matches:
            ranked_schemes = self.ranker.rank_schemes(
                eligible_matches,
                user_preferences=user_preferences,
            )

        # Generate summary
        summary = self._generate_summary(
            user_profile,
            eligible_matches,
            ineligible_matches,
            ranked_schemes,
        )

        return {
            'user_profile': user_profile.dict(),
            'total_schemes_checked': len(schemes),
            'eligible_schemes': len(eligible_matches),
            'ineligible_schemes': len(ineligible_matches),
            'ranked_schemes': ranked_schemes,
            'top_10_schemes': ranked_schemes[:10] if ranked_schemes else [],
            'almost_eligible': self._find_almost_eligible(ineligible_matches),
            'summary': summary,
        }

    def check_eligibility_for_scheme(
        self,
        user_profile: UserProfile,
        scheme: GovernmentScheme,
    ) -> SchemeMatch:
        """
        Check eligibility for a single scheme

        Args:
            user_profile: User's profile
            scheme: Government scheme

        Returns:
            SchemeMatch result
        """
        return self.matcher.check_eligibility(user_profile, scheme)

    def search_and_check(
        self,
        user_profile: UserProfile,
        query: str,
        top_k: int = 20,
    ) -> Dict[str, Any]:
        """
        Search for relevant schemes and check eligibility

        Args:
            user_profile: User's profile
            query: Search query
            top_k: Number of schemes to retrieve

        Returns:
            Search results with eligibility information
        """
        if self.vector_store is None or self.embedder is None:
            logger.warning("Vector search not available. Falling back to all schemes.")
            return self.check_eligibility_for_all_schemes(user_profile)

        # Generate query embedding
        query_embedding = self.embedder.encode(query)

        # Build filters from user profile
        filters = self._build_filters_from_profile(user_profile)

        # Search vector database
        results = self.vector_store.search(
            query_vector=query_embedding,
            top_k=top_k,
            filters=filters,
        )

        # Convert results to schemes
        schemes = []
        for result in results:
            try:
                scheme = self._metadata_to_scheme(result['metadata'])
                schemes.append(scheme)
            except Exception as e:
                logger.error(f"Failed to convert metadata to scheme: {e}")
                continue

        # Check eligibility
        return self.check_eligibility_for_all_schemes(
            user_profile,
            schemes=schemes,
            rank_results=True,
        )

    def get_scheme_by_id(self, scheme_id: str) -> Optional[GovernmentScheme]:
        """Get scheme by ID"""
        schemes = self._get_all_schemes()
        for scheme in schemes:
            if scheme.scheme_id == scheme_id:
                return scheme
        return None

    def get_schemes_by_category(
        self,
        category: str,
        user_profile: Optional[UserProfile] = None,
    ) -> List[GovernmentScheme]:
        """Get schemes by category, optionally filtered by eligibility"""
        schemes = self._get_all_schemes()

        # Filter by category
        filtered = [
            s for s in schemes
            if any(cat.value == category for cat in s.category)
        ]

        # Filter by eligibility if profile provided
        if user_profile:
            eligible_schemes = []
            for scheme in filtered:
                match = self.matcher.check_eligibility(user_profile, scheme)
                if match.is_eligible:
                    eligible_schemes.append(scheme)
            return eligible_schemes

        return filtered

    def _get_all_schemes(self) -> List[GovernmentScheme]:
        """Load all schemes from cache or database"""
        if self._scheme_cache is not None:
            return self._scheme_cache

        schemes = []

        # Try to load from vector database
        if self.vector_store:
            try:
                points = self.vector_store.scroll_all()
                for point in points:
                    if point['metadata'].get('type') == 'scheme':
                        try:
                            scheme = self._metadata_to_scheme(point['metadata'])
                            schemes.append(scheme)
                        except Exception as e:
                            logger.error(f"Failed to convert metadata to scheme: {e}")
                            continue
            except Exception as e:
                logger.error(f"Failed to load schemes from vector DB: {e}")

        # Fallback: Load from JSON files
        if not schemes:
            schemes = self._load_schemes_from_json()

        self._scheme_cache = schemes
        logger.info(f"Loaded {len(schemes)} schemes")
        return schemes

    def _load_schemes_from_json(self) -> List[GovernmentScheme]:
        """Load schemes from JSON files"""
        schemes = []
        json_dir = Path(get_env_variable('PROCESSED_DATA_PATH', 'data/processed')) / 'schemes'

        if not json_dir.exists():
            logger.warning(f"Scheme directory not found: {json_dir}")
            return schemes

        for json_file in json_dir.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    scheme = GovernmentScheme(**data)
                    schemes.append(scheme)
            except Exception as e:
                logger.error(f"Failed to load scheme from {json_file}: {e}")
                continue

        return schemes

    def _metadata_to_scheme(self, metadata: Dict[str, Any]) -> GovernmentScheme:
        """Convert vector DB metadata to GovernmentScheme"""
        # This is a simplified conversion
        # In production, store full scheme JSON in metadata or use scheme ID to fetch from database

        from data_processing.scheme_models import (
            SchemeCategory,
            EligibilityCriteria,
            BenefitDetails,
            ApplicationProcess,
            BenefitType,
        )

        # Find matching scheme from cache/JSON
        scheme_id = metadata.get('scheme_id')
        if scheme_id:
            scheme = self.get_scheme_by_id(scheme_id)
            if scheme:
                return scheme

        # Fallback: Create minimal scheme from metadata
        # This won't have full details, but enough for basic eligibility checking
        raise NotImplementedError("Full metadata to scheme conversion not implemented. Use scheme_id lookup instead.")

    def _build_filters_from_profile(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Build vector DB filters from user profile"""
        filters = {}

        # Age filter
        if user_profile.age:
            filters['min_age'] = {'lte': user_profile.age}
            filters['max_age'] = {'gte': user_profile.age}

        # Income filter
        if user_profile.annual_income:
            filters['max_income'] = {'gte': user_profile.annual_income}

        # State filter
        if user_profile.state:
            filters['states'] = user_profile.state

        # Add more filters as needed

        return filters

    def _generate_summary(
        self,
        user_profile: UserProfile,
        eligible_matches: List[SchemeMatch],
        ineligible_matches: List[SchemeMatch],
        ranked_schemes: List[RankedScheme],
    ) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_benefit = 0
        if ranked_schemes:
            summary = self.ranker.generate_summary(ranked_schemes)
            total_benefit = summary.get('total_estimated_benefit', 0)

        return {
            'total_eligible_schemes': len(eligible_matches),
            'total_ineligible_schemes': len(ineligible_matches),
            'estimated_total_benefit': total_benefit,
            'formatted_benefit': f"₹{total_benefit:,.0f}",
            'top_category': ranked_schemes[0].scheme.category[0].value if ranked_schemes else None,
            'average_eligibility_score': sum(m.overall_score for m in eligible_matches) / len(eligible_matches) if eligible_matches else 0,
        }

    def _find_almost_eligible(
        self,
        ineligible_matches: List[SchemeMatch],
        threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Find schemes user is almost eligible for"""
        almost = []

        for match in ineligible_matches:
            if match.overall_score >= threshold:
                almost.append({
                    'scheme': match.scheme,
                    'score': match.overall_score,
                    'missing_criteria': match.missing_criteria,
                    'recommendations': match.recommendations,
                })

        # Sort by score
        almost.sort(key=lambda x: x['score'], reverse=True)

        return almost[:5]  # Return top 5 almost eligible schemes
