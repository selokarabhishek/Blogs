"""
data.gov.in API Integration Module
Fetches government scheme data from India's Open Government Data Platform
"""

import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class DataGovInAPI:
    """
    Integration with data.gov.in Open Government Data Platform

    Usage:
        1. Get API key from https://www.data.gov.in/
        2. Initialize: api = DataGovInAPI(api_key='your_key')
        3. Search schemes: schemes = api.search_schemes()
    """

    BASE_URL = "https://api.data.gov.in/resource"

    # Known resource IDs for scheme-related datasets
    RESOURCE_IDS = {
        'central_schemes': '9ef84268-d588-465a-a308-a864a43d0070',  # Central govt schemes
        'welfare_schemes': '6176ee09-3d56-4a3b-8115-21841576b996',  # Social welfare
        'pmjdy': 'efb0f614-1a71-4114-b0b8-3e8c2c8e8d3a',          # PM Jan Dhan Yojana
        'scholarship': '2db6308f-9f56-4d7b-9aa7-f06e91846c28',     # Scholarship schemes
        # Add more resource IDs as discovered
    }

    def __init__(
        self,
        api_key: str,
        cache_dir: Optional[Path] = None,
        cache_duration_hours: int = 24,
    ):
        """
        Initialize data.gov.in API client

        Args:
            api_key: Your data.gov.in API key
            cache_dir: Directory to cache responses
            cache_duration_hours: How long to cache data
        """
        self.api_key = api_key
        self.cache_dir = cache_dir or Path("data/cache/datagov")
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SchemeDiscoveryAI/1.0 (Educational; +https://github.com/yourusername)',
        })

    def _get_cache_path(self, resource_id: str) -> Path:
        """Get cache file path for a resource"""
        return self.cache_dir / f"{resource_id}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache is still valid"""
        if not cache_path.exists():
            return False

        modified_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - modified_time < self.cache_duration

    def _read_cache(self, cache_path: Path) -> Optional[Dict]:
        """Read data from cache"""
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None

    def _write_cache(self, cache_path: Path, data: Dict):
        """Write data to cache"""
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing cache: {e}")

    def fetch_resource(
        self,
        resource_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        offset: int = 0,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch data from a specific resource

        Args:
            resource_id: Resource ID from data.gov.in
            filters: Optional filters to apply
            limit: Maximum records to fetch
            offset: Offset for pagination
            use_cache: Whether to use cached data

        Returns:
            API response with records
        """
        cache_path = self._get_cache_path(resource_id)

        # Check cache first
        if use_cache and self._is_cache_valid(cache_path):
            logger.info(f"Using cached data for resource {resource_id}")
            cached_data = self._read_cache(cache_path)
            if cached_data:
                return cached_data

        # Build API request
        params = {
            'api-key': self.api_key,
            'format': 'json',
            'limit': limit,
            'offset': offset,
        }

        # Add filters if provided
        if filters:
            params.update({f'filters[{k}]': v for k, v in filters.items()})

        url = f"{self.BASE_URL}/{resource_id}"

        try:
            logger.info(f"Fetching data from data.gov.in: {resource_id}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Cache the response
            if use_cache:
                self._write_cache(cache_path, data)

            logger.info(f"Successfully fetched {len(data.get('records', []))} records")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data: {e}")

            # Try to use stale cache as fallback
            if cache_path.exists():
                logger.warning("Using stale cache as fallback")
                return self._read_cache(cache_path)

            raise

    def search_all_schemes(self) -> List[Dict[str, Any]]:
        """
        Fetch all available scheme datasets

        Returns:
            List of scheme records from all known resources
        """
        all_schemes = []

        for name, resource_id in self.RESOURCE_IDS.items():
            try:
                logger.info(f"Fetching {name} schemes...")
                response = self.fetch_resource(resource_id)

                records = response.get('records', [])

                # Add source metadata
                for record in records:
                    record['_source'] = name
                    record['_resource_id'] = resource_id
                    record['_fetched_at'] = datetime.now().isoformat()

                all_schemes.extend(records)

                # Rate limiting - be nice to the API
                time.sleep(1)

            except Exception as e:
                logger.error(f"Failed to fetch {name}: {e}")
                continue

        logger.info(f"Total schemes fetched: {len(all_schemes)}")
        return all_schemes

    def search_schemes_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Search schemes by category

        Args:
            category: Category name (e.g., 'Education', 'Health', 'Agriculture')

        Returns:
            List of matching schemes
        """
        all_schemes = self.search_all_schemes()

        # Filter by category (case-insensitive)
        category_lower = category.lower()
        filtered = [
            s for s in all_schemes
            if any(category_lower in str(v).lower() for v in s.values())
        ]

        return filtered

    def get_scheme_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about available schemes

        Returns:
            Dictionary with scheme statistics
        """
        all_schemes = self.search_all_schemes()

        # Calculate statistics
        stats = {
            'total_schemes': len(all_schemes),
            'sources': {},
            'categories': {},
            'last_updated': datetime.now().isoformat(),
        }

        # Count by source
        for scheme in all_schemes:
            source = scheme.get('_source', 'unknown')
            stats['sources'][source] = stats['sources'].get(source, 0) + 1

        return stats


class DataGovSchemeConverter:
    """
    Converts data.gov.in scheme data to our internal GovernmentScheme model
    """

    @staticmethod
    def convert_to_scheme_model(record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert data.gov.in record to GovernmentScheme format

        Args:
            record: Raw record from data.gov.in

        Returns:
            Dictionary matching GovernmentScheme model
        """
        # Extract common fields (field names vary by dataset)
        scheme_data = {
            'scheme_id': record.get('id') or record.get('scheme_id') or f"DATAGOV_{hash(str(record))}",
            'name': record.get('name') or record.get('scheme_name') or 'Unknown Scheme',
            'ministry': record.get('ministry') or record.get('department') or 'Not Specified',
            'category': DataGovSchemeConverter._extract_categories(record),
            'description': record.get('description') or record.get('objective') or '',

            # Eligibility (attempt to extract from various fields)
            'eligibility': DataGovSchemeConverter._extract_eligibility(record),

            # Benefits
            'benefits': DataGovSchemeConverter._extract_benefits(record),

            # Documents
            'documents_required': DataGovSchemeConverter._extract_documents(record),

            # Application
            'application_process': DataGovSchemeConverter._extract_application_process(record),

            # Metadata
            'source_url': record.get('url') or record.get('website'),
            'source_document': None,
            'last_updated': record.get('_fetched_at') or datetime.now().isoformat(),
            'is_active': True,
            'tags': DataGovSchemeConverter._extract_tags(record),
        }

        return scheme_data

    @staticmethod
    def _extract_categories(record: Dict) -> List[str]:
        """Extract scheme categories from record"""
        categories = []

        # Look for category fields
        category_fields = ['category', 'sector', 'type', 'domain']
        for field in category_fields:
            if field in record and record[field]:
                categories.append(str(record[field]))

        return categories if categories else ['Social Welfare']

    @staticmethod
    def _extract_eligibility(record: Dict) -> Dict[str, Any]:
        """Extract eligibility criteria"""
        return {
            'min_age': record.get('min_age'),
            'max_age': record.get('max_age'),
            'gender': ['All'],
            'category': ['All'],
            'min_income': record.get('min_income'),
            'max_income': record.get('max_income'),
            'states': [record.get('state')] if record.get('state') else [],
            'occupation': [],
            'education': [],
            'marital_status': [],
            'disability': None,
            'bpl_card': record.get('bpl_required'),
            'rural_area': None,
            'custom_criteria': {},
        }

    @staticmethod
    def _extract_benefits(record: Dict) -> Dict[str, Any]:
        """Extract benefit information"""
        return {
            'benefit_type': ['Grant'],  # Default assumption
            'amount': record.get('benefit_amount'),
            'amount_min': record.get('min_benefit'),
            'amount_max': record.get('max_benefit'),
            'description': record.get('benefit_description') or 'Financial assistance',
            'duration': record.get('duration'),
            'is_recurring': False,
        }

    @staticmethod
    def _extract_documents(record: Dict) -> List[Dict[str, Any]]:
        """Extract required documents"""
        docs = record.get('documents_required', '').split(',') if record.get('documents_required') else []
        return [
            {'name': doc.strip(), 'is_mandatory': True, 'description': None}
            for doc in docs if doc.strip()
        ]

    @staticmethod
    def _extract_application_process(record: Dict) -> Dict[str, Any]:
        """Extract application process details"""
        return {
            'mode': ['Online'] if record.get('online_application') else ['Offline'],
            'steps': [],
            'website': record.get('application_url') or record.get('website'),
            'helpline': record.get('helpline') or record.get('contact'),
            'processing_time': record.get('processing_time'),
        }

    @staticmethod
    def _extract_tags(record: Dict) -> List[str]:
        """Extract searchable tags"""
        tags = []

        # Add common tags
        if record.get('scheme_name'):
            tags.extend(record['scheme_name'].lower().split())
        if record.get('ministry'):
            tags.append(record['ministry'].lower())

        return list(set(tags))[:10]  # Limit to 10 unique tags


# Example usage and testing
if __name__ == '__main__':
    # For testing - replace with actual API key
    API_KEY = "YOUR_API_KEY_HERE"

    # Initialize API
    api = DataGovInAPI(api_key=API_KEY)

    # Fetch all schemes
    schemes = api.search_all_schemes()
    print(f"Found {len(schemes)} schemes")

    # Get statistics
    stats = api.get_scheme_statistics()
    print(f"Statistics: {json.dumps(stats, indent=2)}")

    # Convert to our model
    if schemes:
        converter = DataGovSchemeConverter()
        converted = converter.convert_to_scheme_model(schemes[0])
        print(f"Converted scheme: {json.dumps(converted, indent=2)}")
