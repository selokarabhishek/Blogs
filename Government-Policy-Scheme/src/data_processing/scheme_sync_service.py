"""
Scheme Data Synchronization Service
Orchestrates fetching data from multiple sources and updating the database
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import asyncio

try:
    from .datagov_api import DataGovInAPI, DataGovSchemeConverter
    from .scheme_models import GovernmentScheme
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data_processing.datagov_api import DataGovInAPI, DataGovSchemeConverter
    from data_processing.scheme_models import GovernmentScheme

logger = logging.getLogger(__name__)


class SchemeSyncService:
    """
    Main service for synchronizing scheme data from multiple sources

    Sources:
    1. data.gov.in API (Primary)
    2. MyScheme API (when available)
    3. Local JSON files (Manual additions)
    4. Web scraping (Gaps only)
    """

    def __init__(
        self,
        datagov_api_key: Optional[str] = None,
        output_dir: Path = None,
    ):
        """
        Initialize sync service

        Args:
            datagov_api_key: API key for data.gov.in
            output_dir: Directory to save synchronized schemes
        """
        self.output_dir = output_dir or Path("data/processed/schemes")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize data sources
        self.datagov_api = None
        if datagov_api_key:
            self.datagov_api = DataGovInAPI(api_key=datagov_api_key)

        self.converter = DataGovSchemeConverter()

        # Statistics
        self.stats = {
            'total_fetched': 0,
            'total_saved': 0,
            'total_updated': 0,
            'total_failed': 0,
            'sources': {},
            'start_time': None,
            'end_time': None,
        }

    def sync_from_datagov(self) -> List[GovernmentScheme]:
        """
        Sync schemes from data.gov.in

        Returns:
            List of GovernmentScheme objects
        """
        if not self.datagov_api:
            logger.warning("data.gov.in API not configured. Skipping.")
            return []

        logger.info("=" * 80)
        logger.info("SYNCING FROM DATA.GOV.IN")
        logger.info("=" * 80)

        schemes = []

        try:
            # Fetch all schemes
            raw_schemes = self.datagov_api.search_all_schemes()
            logger.info(f"Fetched {len(raw_schemes)} raw records from data.gov.in")

            # Convert to our model
            for raw_scheme in raw_schemes:
                try:
                    # Convert to our schema
                    scheme_data = self.converter.convert_to_scheme_model(raw_scheme)

                    # Validate and create GovernmentScheme
                    scheme = GovernmentScheme(**scheme_data)
                    schemes.append(scheme)

                except Exception as e:
                    logger.error(f"Failed to convert scheme: {e}")
                    self.stats['total_failed'] += 1
                    continue

            logger.info(f"Successfully converted {len(schemes)} schemes")
            self.stats['sources']['data.gov.in'] = len(schemes)

        except Exception as e:
            logger.error(f"Error syncing from data.gov.in: {e}")

        return schemes

    def sync_from_local_json(self) -> List[GovernmentScheme]:
        """
        Load existing schemes from local JSON files

        Returns:
            List of GovernmentScheme objects
        """
        logger.info("=" * 80)
        logger.info("LOADING LOCAL JSON SCHEMES")
        logger.info("=" * 80)

        schemes = []
        json_files = list(self.output_dir.glob("*.json"))

        logger.info(f"Found {len(json_files)} local JSON files")

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                scheme = GovernmentScheme(**data)
                schemes.append(scheme)

            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")
                continue

        logger.info(f"Loaded {len(schemes)} schemes from local storage")
        self.stats['sources']['local_json'] = len(schemes)

        return schemes

    def deduplicate_schemes(
        self,
        schemes: List[GovernmentScheme]
    ) -> List[GovernmentScheme]:
        """
        Remove duplicate schemes based on name and ministry

        Args:
            schemes: List of schemes

        Returns:
            Deduplicated list
        """
        logger.info("Deduplicating schemes...")

        seen = set()
        unique_schemes = []

        for scheme in schemes:
            # Create unique key
            key = (scheme.name.lower().strip(), scheme.ministry.lower().strip())

            if key not in seen:
                seen.add(key)
                unique_schemes.append(scheme)
            else:
                logger.debug(f"Duplicate found: {scheme.name}")

        logger.info(f"Removed {len(schemes) - len(unique_schemes)} duplicates")
        return unique_schemes

    def save_schemes(self, schemes: List[GovernmentScheme]):
        """
        Save schemes to JSON files

        Args:
            schemes: List of schemes to save
        """
        logger.info(f"Saving {len(schemes)} schemes to {self.output_dir}")

        for scheme in schemes:
            try:
                # Generate filename from scheme_id
                filename = f"{scheme.scheme_id.lower().replace(' ', '_')}.json"
                filepath = self.output_dir / filename

                # Save as JSON
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(
                        scheme.dict(),
                        f,
                        indent=2,
                        ensure_ascii=False,
                        default=str,  # Handle datetime serialization
                    )

                self.stats['total_saved'] += 1

            except Exception as e:
                logger.error(f"Failed to save {scheme.name}: {e}")
                self.stats['total_failed'] += 1
                continue

        logger.info(f"Saved {self.stats['total_saved']} schemes successfully")

    def run_full_sync(self) -> Dict[str, Any]:
        """
        Run complete synchronization from all sources

        Returns:
            Statistics about the sync operation
        """
        self.stats['start_time'] = datetime.now()

        logger.info("=" * 80)
        logger.info("STARTING FULL SCHEME SYNCHRONIZATION")
        logger.info("=" * 80)

        all_schemes = []

        # 1. Sync from data.gov.in
        if self.datagov_api:
            datagov_schemes = self.sync_from_datagov()
            all_schemes.extend(datagov_schemes)

        # 2. Load existing local schemes (for merging)
        local_schemes = self.sync_from_local_json()

        # 3. Merge all sources
        all_schemes.extend(local_schemes)
        self.stats['total_fetched'] = len(all_schemes)

        # 4. Deduplicate
        unique_schemes = self.deduplicate_schemes(all_schemes)

        # 5. Save to disk
        self.save_schemes(unique_schemes)

        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        logger.info("=" * 80)
        logger.info("SYNC COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Total fetched: {self.stats['total_fetched']}")
        logger.info(f"Total saved: {self.stats['total_saved']}")
        logger.info(f"Failed: {self.stats['total_failed']}")
        logger.info(f"Sources: {self.stats['sources']}")

        return self.stats


class ScheduledSync:
    """
    Scheduler for periodic scheme synchronization
    """

    def __init__(self, sync_service: SchemeSyncService):
        """
        Initialize scheduler

        Args:
            sync_service: SchemeSyncService instance
        """
        self.sync_service = sync_service
        self.is_running = False

    async def run_daily_sync(self, hour: int = 2):
        """
        Run daily sync at specified hour

        Args:
            hour: Hour of day to run (0-23), default 2 AM
        """
        logger.info(f"Starting daily sync scheduler (runs at {hour}:00)")

        while self.is_running:
            now = datetime.now()

            # Calculate next run time
            next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if now.hour >= hour:
                # Run tomorrow
                next_run = next_run.replace(day=next_run.day + 1)

            # Wait until next run
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"Next sync scheduled at {next_run} ({wait_seconds/3600:.1f} hours)")

            await asyncio.sleep(wait_seconds)

            # Run sync
            try:
                logger.info("Running scheduled sync...")
                self.sync_service.run_full_sync()
            except Exception as e:
                logger.error(f"Scheduled sync failed: {e}")

    def start(self):
        """Start the scheduler"""
        self.is_running = True

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False


# CLI Interface
def main():
    """Command-line interface for scheme synchronization"""
    import argparse

    parser = argparse.ArgumentParser(description="Sync government scheme data")
    parser.add_argument(
        '--api-key',
        type=str,
        help='data.gov.in API key',
        default=None,
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/processed/schemes'),
        help='Output directory for schemes',
    )
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run as scheduled service (daily at 2 AM)',
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    # Create sync service
    sync_service = SchemeSyncService(
        datagov_api_key=args.api_key,
        output_dir=args.output_dir,
    )

    if args.schedule:
        # Run as scheduled service
        scheduler = ScheduledSync(sync_service)
        scheduler.start()

        try:
            asyncio.run(scheduler.run_daily_sync())
        except KeyboardInterrupt:
            logger.info("Shutting down scheduler...")
            scheduler.stop()
    else:
        # Run once
        stats = sync_service.run_full_sync()
        print("\nSync Statistics:")
        print(json.dumps(stats, indent=2, default=str))


if __name__ == '__main__':
    main()
