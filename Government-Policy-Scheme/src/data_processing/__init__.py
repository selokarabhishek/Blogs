"""
Data Processing Module
Handles PDF scraping, document parsing using Docling, and data extraction.
Includes integration with data.gov.in for fetching official government schemes.
"""

from .pdf_processor import PDFProcessor, ExtractedDocument, extract_scheme_info
from .scheme_models import (
    GovernmentScheme,
    UserProfile,
    EligibilityCriteria,
    BenefitDetails,
    SchemeCategory,
)
from .datagov_api import DataGovInAPI, DataGovSchemeConverter
from .scheme_sync_service import SchemeSyncService, ScheduledSync

__all__ = [
    'PDFProcessor',
    'ExtractedDocument',
    'extract_scheme_info',
    'GovernmentScheme',
    'UserProfile',
    'EligibilityCriteria',
    'BenefitDetails',
    'SchemeCategory',
    'DataGovInAPI',
    'DataGovSchemeConverter',
    'SchemeSyncService',
    'ScheduledSync',
]
