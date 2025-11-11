"""
Data Processing Module
Handles PDF scraping, document parsing using Docling, and data extraction.
"""

from .pdf_processor import PDFProcessor, ExtractedDocument, extract_scheme_info
from .scheme_models import (
    GovernmentScheme,
    UserProfile,
    EligibilityCriteria,
    BenefitDetails,
    SchemeCategory,
)

__all__ = [
    'PDFProcessor',
    'ExtractedDocument',
    'extract_scheme_info',
    'GovernmentScheme',
    'UserProfile',
    'EligibilityCriteria',
    'BenefitDetails',
    'SchemeCategory',
]
