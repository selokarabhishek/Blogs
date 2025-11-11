"""
Eligibility Module
Core eligibility checking engine that matches user profiles with scheme criteria.
"""

from .matcher import EligibilityMatcher, SchemeMatch, EligibilityMatch, MatchStatus
from .ranker import SchemeRanker, RankedScheme, RankingStrategy
from .checker import EligibilityCheckerService

__all__ = [
    'EligibilityMatcher',
    'SchemeMatch',
    'EligibilityMatch',
    'MatchStatus',
    'SchemeRanker',
    'RankedScheme',
    'RankingStrategy',
    'EligibilityCheckerService',
]
