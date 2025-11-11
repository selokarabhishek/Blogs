"""
Scheme Ranker - Scoring and Ranking System
Ranks eligible schemes by benefit value, relevance, and user preferences
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_processing.scheme_models import GovernmentScheme, BenefitType
from eligibility.matcher import SchemeMatch

logger = logging.getLogger(__name__)


class RankingStrategy(str, Enum):
    """Ranking strategies"""
    BENEFIT_AMOUNT = "benefit_amount"  # Rank by monetary value
    ELIGIBILITY_SCORE = "eligibility_score"  # Rank by how well user matches
    COMBINED = "combined"  # Weighted combination
    EASE_OF_APPLICATION = "ease_of_application"  # Rank by simplicity
    PROCESSING_TIME = "processing_time"  # Rank by how fast benefits arrive


@dataclass
class RankedScheme:
    """Scheme with ranking metadata"""
    scheme: GovernmentScheme
    match: SchemeMatch
    rank: int
    final_score: float
    benefit_score: float
    eligibility_score: float
    ease_score: float
    metadata: Dict[str, Any]


class SchemeRanker:
    """
    Ranks schemes based on multiple factors
    Helps users prioritize which schemes to apply for first
    """

    def __init__(
        self,
        strategy: RankingStrategy = RankingStrategy.COMBINED,
        benefit_weight: float = 0.5,
        eligibility_weight: float = 0.3,
        ease_weight: float = 0.2,
    ):
        """
        Initialize ranker

        Args:
            strategy: Ranking strategy to use
            benefit_weight: Weight for benefit amount (0-1)
            eligibility_weight: Weight for eligibility score (0-1)
            ease_weight: Weight for ease of application (0-1)
        """
        self.strategy = strategy
        self.benefit_weight = benefit_weight
        self.eligibility_weight = eligibility_weight
        self.ease_weight = ease_weight

        # Normalize weights
        total = benefit_weight + eligibility_weight + ease_weight
        if total > 0:
            self.benefit_weight /= total
            self.eligibility_weight /= total
            self.ease_weight /= total

    def rank_schemes(
        self,
        scheme_matches: List[SchemeMatch],
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> List[RankedScheme]:
        """
        Rank eligible schemes

        Args:
            scheme_matches: List of scheme matches from eligibility checker
            user_preferences: Optional user preferences (e.g., preferred categories)

        Returns:
            List of RankedScheme objects sorted by rank
        """
        # Filter to eligible schemes only
        eligible_matches = [m for m in scheme_matches if m.is_eligible]

        if not eligible_matches:
            logger.warning("No eligible schemes to rank")
            return []

        ranked_schemes = []

        for match in eligible_matches:
            # Calculate individual scores
            benefit_score = self._calculate_benefit_score(match.scheme)
            eligibility_score = match.overall_score
            ease_score = self._calculate_ease_score(match.scheme)

            # Calculate final score based on strategy
            if self.strategy == RankingStrategy.BENEFIT_AMOUNT:
                final_score = benefit_score
            elif self.strategy == RankingStrategy.ELIGIBILITY_SCORE:
                final_score = eligibility_score
            elif self.strategy == RankingStrategy.EASE_OF_APPLICATION:
                final_score = ease_score
            else:  # COMBINED
                final_score = (
                    self.benefit_weight * benefit_score +
                    self.eligibility_weight * eligibility_score +
                    self.ease_weight * ease_score
                )

            # Apply user preferences boost
            if user_preferences:
                final_score = self._apply_preference_boost(
                    final_score,
                    match.scheme,
                    user_preferences
                )

            ranked_schemes.append(
                RankedScheme(
                    scheme=match.scheme,
                    match=match,
                    rank=0,  # Will be assigned after sorting
                    final_score=final_score,
                    benefit_score=benefit_score,
                    eligibility_score=eligibility_score,
                    ease_score=ease_score,
                    metadata=self._generate_metadata(match.scheme),
                )
            )

        # Sort by final score (descending)
        ranked_schemes.sort(key=lambda x: x.final_score, reverse=True)

        # Assign ranks
        for i, ranked_scheme in enumerate(ranked_schemes, 1):
            ranked_scheme.rank = i

        logger.info(f"Ranked {len(ranked_schemes)} eligible schemes")
        return ranked_schemes

    def _calculate_benefit_score(self, scheme: GovernmentScheme) -> float:
        """
        Calculate benefit value score (0-1)

        Higher monetary benefits get higher scores
        """
        # Get benefit amount
        if scheme.benefits.amount:
            amount = scheme.benefits.amount
        elif scheme.benefits.amount_max:
            amount = scheme.benefits.amount_max
        elif scheme.benefits.amount_min:
            amount = scheme.benefits.amount_min
        else:
            # No clear amount - assign based on benefit type
            return self._score_by_benefit_type(scheme.benefits.benefit_type)

        # Normalize amount to 0-1 scale
        # Assuming max benefit is ₹10 lakh
        max_benefit = 1000000
        score = min(amount / max_benefit, 1.0)

        # Boost recurring benefits
        if scheme.benefits.is_recurring:
            score *= 1.5  # 50% boost for recurring

        # Cap at 1.0
        return min(score, 1.0)

    def _score_by_benefit_type(self, benefit_types: List[BenefitType]) -> float:
        """Assign score based on benefit type when amount not specified"""
        type_scores = {
            BenefitType.GRANT: 0.8,
            BenefitType.SUBSIDY: 0.7,
            BenefitType.LOAN: 0.6,
            BenefitType.SCHOLARSHIP: 0.7,
            BenefitType.PENSION: 0.75,
            BenefitType.INSURANCE: 0.65,
            BenefitType.TAX_BENEFIT: 0.6,
            BenefitType.TRAINING: 0.5,
            BenefitType.OTHER: 0.4,
        }

        if not benefit_types:
            return 0.5

        # Take max score from all benefit types
        scores = [type_scores.get(bt, 0.5) for bt in benefit_types]
        return max(scores)

    def _calculate_ease_score(self, scheme: GovernmentScheme) -> float:
        """
        Calculate ease of application score (0-1)

        Factors:
        - Number of required documents (fewer = better)
        - Application mode (online > both > offline)
        - Processing time (faster = better)
        """
        score = 1.0

        # Document count penalty (more docs = lower score)
        num_docs = len(scheme.documents_required)
        doc_penalty = min(num_docs * 0.05, 0.3)  # Max 30% penalty
        score -= doc_penalty

        # Online application boost
        if "Online" in scheme.application_process.mode:
            score += 0.2
        if "Offline" in scheme.application_process.mode and "Online" not in scheme.application_process.mode:
            score -= 0.1

        # Processing time (if specified)
        if scheme.application_process.processing_time:
            processing = scheme.application_process.processing_time.lower()
            if "instant" in processing or "immediate" in processing:
                score += 0.2
            elif "day" in processing:
                # Extract number of days
                try:
                    days = int(''.join(filter(str.isdigit, processing.split('-')[0])))
                    if days <= 15:
                        score += 0.1
                    elif days >= 90:
                        score -= 0.1
                except:
                    pass

        return max(min(score, 1.0), 0.0)

    def _apply_preference_boost(
        self,
        score: float,
        scheme: GovernmentScheme,
        preferences: Dict[str, Any],
    ) -> float:
        """Apply boost based on user preferences"""

        # Preferred categories
        if "categories" in preferences:
            preferred_cats = preferences["categories"]
            scheme_cats = [cat.value for cat in scheme.category]
            if any(cat in scheme_cats for cat in preferred_cats):
                score *= 1.2  # 20% boost

        # Preferred benefit type
        if "benefit_type" in preferences:
            preferred_types = preferences["benefit_type"]
            if any(bt.value in preferred_types for bt in scheme.benefits.benefit_type):
                score *= 1.15  # 15% boost

        # Urgency - boost schemes with faster processing
        if preferences.get("urgent", False):
            if scheme.application_process.processing_time:
                processing = scheme.application_process.processing_time.lower()
                if "instant" in processing or "day" in processing and int(''.join(filter(str.isdigit, processing.split()[0]))) <= 30:
                    score *= 1.3  # 30% boost for urgent + fast processing

        return score

    def _generate_metadata(self, scheme: GovernmentScheme) -> Dict[str, Any]:
        """Generate additional metadata for ranking display"""
        return {
            'estimated_benefit': self._estimate_benefit_value(scheme),
            'application_complexity': self._assess_complexity(scheme),
            'time_to_benefit': scheme.application_process.processing_time,
            'success_rate': self._estimate_success_rate(scheme),
        }

    def _estimate_benefit_value(self, scheme: GovernmentScheme) -> str:
        """Estimate and format benefit value"""
        if scheme.benefits.amount:
            return f"₹{scheme.benefits.amount:,.0f}"
        elif scheme.benefits.amount_max:
            if scheme.benefits.amount_min:
                return f"₹{scheme.benefits.amount_min:,.0f} - ₹{scheme.benefits.amount_max:,.0f}"
            else:
                return f"Up to ₹{scheme.benefits.amount_max:,.0f}"
        else:
            return "Variable"

    def _assess_complexity(self, scheme: GovernmentScheme) -> str:
        """Assess application complexity"""
        num_docs = len(scheme.documents_required)

        if num_docs <= 3:
            return "Simple"
        elif num_docs <= 6:
            return "Moderate"
        else:
            return "Complex"

    def _estimate_success_rate(self, scheme: GovernmentScheme) -> str:
        """Estimate success rate based on scheme characteristics"""
        # This is a simplified heuristic
        # In production, would use actual success statistics

        score = 80  # Base score

        # Central schemes generally have higher success
        if "Central" in scheme.ministry or "PM" in scheme.name or "Pradhan Mantri" in scheme.name:
            score += 10

        # Online application increases success
        if "Online" in scheme.application_process.mode:
            score += 5

        return f"{min(score, 95)}%"

    def get_top_schemes(
        self,
        ranked_schemes: List[RankedScheme],
        top_n: int = 10,
    ) -> List[RankedScheme]:
        """Get top N ranked schemes"""
        return ranked_schemes[:top_n]

    def filter_by_category(
        self,
        ranked_schemes: List[RankedScheme],
        category: str,
    ) -> List[RankedScheme]:
        """Filter ranked schemes by category"""
        filtered = [
            rs for rs in ranked_schemes
            if any(cat.value == category for cat in rs.scheme.category)
        ]

        # Re-rank after filtering
        for i, rs in enumerate(filtered, 1):
            rs.rank = i

        return filtered

    def filter_by_benefit_amount(
        self,
        ranked_schemes: List[RankedScheme],
        min_amount: float,
    ) -> List[RankedScheme]:
        """Filter schemes by minimum benefit amount"""
        filtered = [
            rs for rs in ranked_schemes
            if (rs.scheme.benefits.amount or rs.scheme.benefits.amount_max or 0) >= min_amount
        ]

        # Re-rank
        for i, rs in enumerate(filtered, 1):
            rs.rank = i

        return filtered

    def generate_summary(self, ranked_schemes: List[RankedScheme]) -> Dict[str, Any]:
        """Generate summary statistics for ranked schemes"""
        if not ranked_schemes:
            return {
                'total_schemes': 0,
                'total_estimated_benefit': 0,
                'categories': {},
                'average_score': 0,
            }

        # Total estimated benefit (sum of max amounts)
        total_benefit = sum(
            rs.scheme.benefits.amount or rs.scheme.benefits.amount_max or 0
            for rs in ranked_schemes
        )

        # Category distribution
        category_dist = {}
        for rs in ranked_schemes:
            for cat in rs.scheme.category:
                category_dist[cat.value] = category_dist.get(cat.value, 0) + 1

        # Average score
        avg_score = sum(rs.final_score for rs in ranked_schemes) / len(ranked_schemes)

        return {
            'total_schemes': len(ranked_schemes),
            'total_estimated_benefit': total_benefit,
            'categories': category_dist,
            'average_score': avg_score,
            'top_category': max(category_dist.items(), key=lambda x: x[1])[0] if category_dist else None,
        }
