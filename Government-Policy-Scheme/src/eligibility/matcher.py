"""
Eligibility Matcher - Core Engine
Rule-based matching logic to determine user eligibility for government schemes
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_processing.scheme_models import (
    GovernmentScheme,
    UserProfile,
    EligibilityCriteria,
    EligibilityGender,
    EligibilityCategory,
)

logger = logging.getLogger(__name__)


class MatchStatus(str, Enum):
    """Match status for eligibility criteria"""
    MATCH = "match"
    NO_MATCH = "no_match"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class EligibilityMatch:
    """Result of eligibility matching"""
    criterion: str
    status: MatchStatus
    score: float  # 0.0 to 1.0
    reason: str
    user_value: Any = None
    required_value: Any = None


@dataclass
class SchemeMatch:
    """Complete scheme match result"""
    scheme: GovernmentScheme
    is_eligible: bool
    overall_score: float  # 0.0 to 1.0
    matches: List[EligibilityMatch]
    missing_criteria: List[str]
    recommendations: List[str]


class EligibilityMatcher:
    """
    Core eligibility matching engine
    Evaluates user profile against scheme eligibility criteria
    """

    def __init__(
        self,
        strict_mode: bool = False,
        min_match_score: float = 0.6,
        boost_factors: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize eligibility matcher

        Args:
            strict_mode: If True, ALL criteria must match (AND logic)
                        If False, weighted scoring (partial matches OK)
            min_match_score: Minimum score (0-1) to consider eligible
            boost_factors: Dictionary of criterion → boost multiplier
        """
        self.strict_mode = strict_mode
        self.min_match_score = min_match_score
        self.boost_factors = boost_factors or {
            'income': 1.5,
            'category': 1.3,
            'state': 1.2,
            'age': 1.0,
            'gender': 1.0,
            'occupation': 1.1,
        }

    def check_eligibility(
        self,
        user_profile: UserProfile,
        scheme: GovernmentScheme,
    ) -> SchemeMatch:
        """
        Check if user is eligible for a scheme

        Args:
            user_profile: User's profile data
            scheme: Government scheme to check

        Returns:
            SchemeMatch with eligibility result and details
        """
        criteria = scheme.eligibility
        matches: List[EligibilityMatch] = []

        # Check each eligibility criterion
        matches.append(self._check_age(user_profile.age, criteria))
        matches.append(self._check_gender(user_profile.gender, criteria))
        matches.append(self._check_category(user_profile.category, criteria))
        matches.append(self._check_income(user_profile.annual_income, criteria))
        matches.append(self._check_state(user_profile.state, criteria))
        matches.append(self._check_occupation(user_profile.occupation, criteria))

        # Optional criteria
        if user_profile.education:
            matches.append(self._check_education(user_profile.education, criteria))
        if user_profile.marital_status:
            matches.append(self._check_marital_status(user_profile.marital_status, criteria))

        # Special criteria
        matches.append(self._check_disability(user_profile.disability, criteria))
        matches.append(self._check_bpl(user_profile.bpl_card, criteria))
        matches.append(self._check_rural(user_profile.rural_area, criteria))

        # Calculate overall score
        overall_score = self._calculate_score(matches)

        # Determine eligibility
        is_eligible = self._determine_eligibility(matches, overall_score)

        # Find missing criteria
        missing_criteria = self._find_missing_criteria(matches)

        # Generate recommendations
        recommendations = self._generate_recommendations(matches, criteria, user_profile)

        return SchemeMatch(
            scheme=scheme,
            is_eligible=is_eligible,
            overall_score=overall_score,
            matches=matches,
            missing_criteria=missing_criteria,
            recommendations=recommendations,
        )

    def _check_age(
        self,
        user_age: int,
        criteria: EligibilityCriteria,
    ) -> EligibilityMatch:
        """Check age eligibility"""
        if criteria.min_age is None and criteria.max_age is None:
            return EligibilityMatch(
                criterion="age",
                status=MatchStatus.NOT_APPLICABLE,
                score=1.0,
                reason="No age restriction",
                user_value=user_age,
            )

        min_age = criteria.min_age or 0
        max_age = criteria.max_age or 120

        if min_age <= user_age <= max_age:
            return EligibilityMatch(
                criterion="age",
                status=MatchStatus.MATCH,
                score=1.0,
                reason=f"Age {user_age} is within range {min_age}-{max_age}",
                user_value=user_age,
                required_value=f"{min_age}-{max_age}",
            )
        else:
            # Partial score based on how close they are
            if user_age < min_age:
                gap = min_age - user_age
                reason = f"Age {user_age} is below minimum {min_age} (need {gap} more years)"
            else:
                gap = user_age - max_age
                reason = f"Age {user_age} exceeds maximum {max_age} (exceeded by {gap} years)"

            # Give partial score if within 5 years of range
            partial_score = max(0, 1.0 - (gap / 5.0))

            return EligibilityMatch(
                criterion="age",
                status=MatchStatus.NO_MATCH if partial_score == 0 else MatchStatus.PARTIAL,
                score=partial_score,
                reason=reason,
                user_value=user_age,
                required_value=f"{min_age}-{max_age}",
            )

    def _check_gender(
        self,
        user_gender: EligibilityGender,
        criteria: EligibilityCriteria,
    ) -> EligibilityMatch:
        """Check gender eligibility"""
        allowed_genders = criteria.gender

        if EligibilityGender.ALL in allowed_genders or not allowed_genders:
            return EligibilityMatch(
                criterion="gender",
                status=MatchStatus.NOT_APPLICABLE,
                score=1.0,
                reason="All genders eligible",
                user_value=user_gender.value,
            )

        if user_gender in allowed_genders:
            return EligibilityMatch(
                criterion="gender",
                status=MatchStatus.MATCH,
                score=1.0,
                reason=f"Gender {user_gender.value} is eligible",
                user_value=user_gender.value,
                required_value=[g.value for g in allowed_genders],
            )
        else:
            return EligibilityMatch(
                criterion="gender",
                status=MatchStatus.NO_MATCH,
                score=0.0,
                reason=f"Gender {user_gender.value} not eligible. Required: {', '.join([g.value for g in allowed_genders])}",
                user_value=user_gender.value,
                required_value=[g.value for g in allowed_genders],
            )

    def _check_category(
        self,
        user_category: EligibilityCategory,
        criteria: EligibilityCriteria,
    ) -> EligibilityMatch:
        """Check social category eligibility"""
        allowed_categories = criteria.category

        if EligibilityCategory.ALL in allowed_categories or not allowed_categories:
            return EligibilityMatch(
                criterion="category",
                status=MatchStatus.NOT_APPLICABLE,
                score=1.0,
                reason="All categories eligible",
                user_value=user_category.value,
            )

        if user_category in allowed_categories:
            return EligibilityMatch(
                criterion="category",
                status=MatchStatus.MATCH,
                score=1.0,
                reason=f"Category {user_category.value} is eligible",
                user_value=user_category.value,
                required_value=[c.value for c in allowed_categories],
            )
        else:
            return EligibilityMatch(
                criterion="category",
                status=MatchStatus.NO_MATCH,
                score=0.0,
                reason=f"Category {user_category.value} not eligible. Required: {', '.join([c.value for c in allowed_categories])}",
                user_value=user_category.value,
                required_value=[c.value for c in allowed_categories],
            )

    def _check_income(
        self,
        user_income: float,
        criteria: EligibilityCriteria,
    ) -> EligibilityMatch:
        """Check income eligibility"""
        if criteria.min_income is None and criteria.max_income is None:
            return EligibilityMatch(
                criterion="income",
                status=MatchStatus.NOT_APPLICABLE,
                score=1.0,
                reason="No income restriction",
                user_value=user_income,
            )

        min_income = criteria.min_income or 0
        max_income = criteria.max_income or float('inf')

        if min_income <= user_income <= max_income:
            return EligibilityMatch(
                criterion="income",
                status=MatchStatus.MATCH,
                score=1.0,
                reason=f"Income ₹{user_income:,.0f} is within range ₹{min_income:,.0f}-₹{max_income:,.0f}",
                user_value=user_income,
                required_value=f"₹{min_income:,.0f}-₹{max_income:,.0f}",
            )
        else:
            if user_income < min_income:
                gap = min_income - user_income
                reason = f"Income ₹{user_income:,.0f} is below minimum ₹{min_income:,.0f} (shortfall: ₹{gap:,.0f})"
            else:
                gap = user_income - max_income
                reason = f"Income ₹{user_income:,.0f} exceeds maximum ₹{max_income:,.0f} (excess: ₹{gap:,.0f})"

            # Partial score based on proximity (within 20% of limit)
            if user_income < min_income:
                partial_score = max(0, 1.0 - (gap / (min_income * 0.2)))
            else:
                partial_score = max(0, 1.0 - (gap / (max_income * 0.2)))

            return EligibilityMatch(
                criterion="income",
                status=MatchStatus.NO_MATCH if partial_score == 0 else MatchStatus.PARTIAL,
                score=partial_score,
                reason=reason,
                user_value=user_income,
                required_value=f"₹{min_income:,.0f}-₹{max_income:,.0f}",
            )

    def _check_state(
        self,
        user_state: str,
        criteria: EligibilityCriteria,
    ) -> EligibilityMatch:
        """Check state eligibility"""
        allowed_states = criteria.states

        if not allowed_states:
            return EligibilityMatch(
                criterion="state",
                status=MatchStatus.NOT_APPLICABLE,
                score=1.0,
                reason="All states eligible (central scheme)",
                user_value=user_state,
            )

        if user_state in allowed_states:
            return EligibilityMatch(
                criterion="state",
                status=MatchStatus.MATCH,
                score=1.0,
                reason=f"State {user_state} is eligible",
                user_value=user_state,
                required_value=allowed_states,
            )
        else:
            return EligibilityMatch(
                criterion="state",
                status=MatchStatus.NO_MATCH,
                score=0.0,
                reason=f"Scheme not available in {user_state}. Available in: {', '.join(allowed_states)}",
                user_value=user_state,
                required_value=allowed_states,
            )

    def _check_occupation(
        self,
        user_occupation: str,
        criteria: EligibilityCriteria,
    ) -> EligibilityMatch:
        """Check occupation eligibility"""
        allowed_occupations = criteria.occupation

        if not allowed_occupations:
            return EligibilityMatch(
                criterion="occupation",
                status=MatchStatus.NOT_APPLICABLE,
                score=1.0,
                reason="All occupations eligible",
                user_value=user_occupation,
            )

        # Case-insensitive matching
        user_occupation_lower = user_occupation.lower()
        allowed_occupations_lower = [occ.lower() for occ in allowed_occupations]

        if user_occupation_lower in allowed_occupations_lower:
            return EligibilityMatch(
                criterion="occupation",
                status=MatchStatus.MATCH,
                score=1.0,
                reason=f"Occupation '{user_occupation}' is eligible",
                user_value=user_occupation,
                required_value=allowed_occupations,
            )
        else:
            return EligibilityMatch(
                criterion="occupation",
                status=MatchStatus.NO_MATCH,
                score=0.0,
                reason=f"Occupation '{user_occupation}' not eligible. Required: {', '.join(allowed_occupations)}",
                user_value=user_occupation,
                required_value=allowed_occupations,
            )

    def _check_education(
        self,
        user_education: str,
        criteria: EligibilityCriteria,
    ) -> EligibilityMatch:
        """Check education eligibility"""
        required_education = criteria.education

        if not required_education:
            return EligibilityMatch(
                criterion="education",
                status=MatchStatus.NOT_APPLICABLE,
                score=1.0,
                reason="No education requirement",
                user_value=user_education,
            )

        if user_education in required_education:
            return EligibilityMatch(
                criterion="education",
                status=MatchStatus.MATCH,
                score=1.0,
                reason=f"Education level '{user_education}' meets requirement",
                user_value=user_education,
                required_value=required_education,
            )
        else:
            return EligibilityMatch(
                criterion="education",
                status=MatchStatus.NO_MATCH,
                score=0.0,
                reason=f"Education '{user_education}' doesn't match. Required: {', '.join(required_education)}",
                user_value=user_education,
                required_value=required_education,
            )

    def _check_marital_status(
        self,
        user_status: str,
        criteria: EligibilityCriteria,
    ) -> EligibilityMatch:
        """Check marital status eligibility"""
        required_status = criteria.marital_status

        if not required_status:
            return EligibilityMatch(
                criterion="marital_status",
                status=MatchStatus.NOT_APPLICABLE,
                score=1.0,
                reason="No marital status requirement",
                user_value=user_status,
            )

        if user_status in required_status:
            return EligibilityMatch(
                criterion="marital_status",
                status=MatchStatus.MATCH,
                score=1.0,
                reason=f"Marital status '{user_status}' is eligible",
                user_value=user_status,
                required_value=required_status,
            )
        else:
            return EligibilityMatch(
                criterion="marital_status",
                status=MatchStatus.NO_MATCH,
                score=0.0,
                reason=f"Marital status '{user_status}' not eligible. Required: {', '.join(required_status)}",
                user_value=user_status,
                required_value=required_status,
            )

    def _check_disability(
        self,
        has_disability: bool,
        criteria: EligibilityCriteria,
    ) -> EligibilityMatch:
        """Check disability requirement"""
        if criteria.disability is None:
            return EligibilityMatch(
                criterion="disability",
                status=MatchStatus.NOT_APPLICABLE,
                score=1.0,
                reason="No disability requirement",
                user_value=has_disability,
            )

        if has_disability == criteria.disability:
            return EligibilityMatch(
                criterion="disability",
                status=MatchStatus.MATCH,
                score=1.0,
                reason=f"Disability status matches requirement",
                user_value=has_disability,
                required_value=criteria.disability,
            )
        else:
            return EligibilityMatch(
                criterion="disability",
                status=MatchStatus.NO_MATCH,
                score=0.0,
                reason=f"Requires disability: {criteria.disability}",
                user_value=has_disability,
                required_value=criteria.disability,
            )

    def _check_bpl(
        self,
        has_bpl_card: bool,
        criteria: EligibilityCriteria,
    ) -> EligibilityMatch:
        """Check BPL card requirement"""
        if criteria.bpl_card is None:
            return EligibilityMatch(
                criterion="bpl_card",
                status=MatchStatus.NOT_APPLICABLE,
                score=1.0,
                reason="No BPL card requirement",
                user_value=has_bpl_card,
            )

        if has_bpl_card == criteria.bpl_card:
            return EligibilityMatch(
                criterion="bpl_card",
                status=MatchStatus.MATCH,
                score=1.0,
                reason=f"BPL card status matches requirement",
                user_value=has_bpl_card,
                required_value=criteria.bpl_card,
            )
        else:
            return EligibilityMatch(
                criterion="bpl_card",
                status=MatchStatus.NO_MATCH,
                score=0.0,
                reason=f"Requires BPL card: {criteria.bpl_card}",
                user_value=has_bpl_card,
                required_value=criteria.bpl_card,
            )

    def _check_rural(
        self,
        is_rural: bool,
        criteria: EligibilityCriteria,
    ) -> EligibilityMatch:
        """Check rural area requirement"""
        if criteria.rural_area is None:
            return EligibilityMatch(
                criterion="rural_area",
                status=MatchStatus.NOT_APPLICABLE,
                score=1.0,
                reason="No rural/urban requirement",
                user_value=is_rural,
            )

        if is_rural == criteria.rural_area:
            return EligibilityMatch(
                criterion="rural_area",
                status=MatchStatus.MATCH,
                score=1.0,
                reason=f"Rural area status matches requirement",
                user_value=is_rural,
                required_value=criteria.rural_area,
            )
        else:
            area_type = "rural" if criteria.rural_area else "urban"
            return EligibilityMatch(
                criterion="rural_area",
                status=MatchStatus.NO_MATCH,
                score=0.0,
                reason=f"Scheme only for {area_type} areas",
                user_value=is_rural,
                required_value=criteria.rural_area,
            )

    def _calculate_score(self, matches: List[EligibilityMatch]) -> float:
        """Calculate weighted overall score"""
        total_score = 0.0
        total_weight = 0.0

        for match in matches:
            # Skip not applicable criteria
            if match.status == MatchStatus.NOT_APPLICABLE:
                continue

            # Get boost factor for this criterion
            boost = self.boost_factors.get(match.criterion, 1.0)

            total_score += match.score * boost
            total_weight += boost

        if total_weight == 0:
            return 1.0  # All criteria not applicable = eligible

        return total_score / total_weight

    def _determine_eligibility(
        self,
        matches: List[EligibilityMatch],
        overall_score: float,
    ) -> bool:
        """Determine if user is eligible"""
        if self.strict_mode:
            # Strict mode: ALL criteria must match
            for match in matches:
                if match.status == MatchStatus.NO_MATCH:
                    return False
            return True
        else:
            # Weighted mode: Score must be above threshold
            return overall_score >= self.min_match_score

    def _find_missing_criteria(
        self,
        matches: List[EligibilityMatch],
    ) -> List[str]:
        """Find criteria that don't match"""
        missing = []
        for match in matches:
            if match.status == MatchStatus.NO_MATCH:
                missing.append(f"{match.criterion}: {match.reason}")
        return missing

    def _generate_recommendations(
        self,
        matches: List[EligibilityMatch],
        criteria: EligibilityCriteria,
        user_profile: UserProfile,
    ) -> List[str]:
        """Generate recommendations for user"""
        recommendations = []

        for match in matches:
            if match.status == MatchStatus.PARTIAL:
                recommendations.append(f"Almost eligible for {match.criterion}: {match.reason}")
            elif match.status == MatchStatus.NO_MATCH:
                if match.criterion == "age":
                    if user_profile.age < (criteria.min_age or 0):
                        recommendations.append(f"Wait until age {criteria.min_age} to apply")
                elif match.criterion == "income":
                    if user_profile.annual_income > (criteria.max_income or float('inf')):
                        recommendations.append("Consider applying after income changes or under different scheme category")

        return recommendations
