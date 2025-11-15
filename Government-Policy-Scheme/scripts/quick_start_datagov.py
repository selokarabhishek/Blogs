"""
Quick Start Script for data.gov.in Integration
Helps you set up and test data.gov.in API integration
"""

import sys
from pathlib import Path
import json
import os

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print("=" * 80)
print(" " * 20 + "DATA.GOV.IN QUICK START")
print("=" * 80)
print()

def check_api_key():
    """Check if API key is configured"""
    # Check environment variable
    api_key = os.getenv('DATA_GOV_API_KEY')

    if api_key:
        print("✅ API key found in environment variable")
        return api_key

    # Check .env file
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith('DATA_GOV_API_KEY='):
                    api_key = line.split('=')[1].strip()
                    if api_key and api_key != 'your_api_key_here':
                        print("✅ API key found in .env file")
                        return api_key

    print("❌ No API key found!")
    print()
    print("📝 How to get your API key:")
    print("   1. Visit: https://www.data.gov.in/")
    print("   2. Click 'Sign Up' or 'Register'")
    print("   3. Verify your email")
    print("   4. Go to 'My Account' → 'API Keys'")
    print("   5. Generate and copy your API key")
    print()
    print("⚙️  Then configure it:")
    print("   Method 1: Add to .env file")
    print("   echo 'DATA_GOV_API_KEY=your_key_here' >> .env")
    print()
    print("   Method 2: Export as environment variable")
    print("   export DATA_GOV_API_KEY='your_key_here'")
    print()

    # Prompt for manual entry
    user_key = input("Or enter your API key now (press Enter to skip): ").strip()
    if user_key:
        # Save to .env
        with open(env_file, 'a') as f:
            f.write(f"\nDATA_GOV_API_KEY={user_key}\n")
        print("✅ Saved to .env file")
        return user_key

    return None


def test_api_connection(api_key):
    """Test API connection"""
    print()
    print("🔍 Testing API connection...")

    try:
        from data_processing.datagov_api import DataGovInAPI

        api = DataGovInAPI(api_key=api_key)

        # Try to fetch statistics
        stats = api.get_scheme_statistics()

        print("✅ API connection successful!")
        print(f"   Found {stats['total_schemes']} schemes")
        print(f"   Sources: {list(stats['sources'].keys())}")
        return True

    except Exception as e:
        print(f"❌ API connection failed: {e}")
        print()
        print("💡 Troubleshooting:")
        print("   - Verify your API key is correct")
        print("   - Check internet connection")
        print("   - Try again in a few minutes (rate limiting)")
        return False


def run_first_sync(api_key):
    """Run first data sync"""
    print()
    print("📥 Running first sync from data.gov.in...")
    print("   This may take a few minutes...")
    print()

    try:
        from data_processing.scheme_sync_service import SchemeSyncService

        # Create sync service
        sync_service = SchemeSyncService(
            datagov_api_key=api_key,
            output_dir=PROJECT_ROOT / 'data' / 'processed' / 'schemes'
        )

        # Run sync
        stats = sync_service.run_full_sync()

        print()
        print("✅ Sync completed!")
        print(f"   Total fetched: {stats['total_fetched']}")
        print(f"   Total saved: {stats['total_saved']}")
        print(f"   Failed: {stats['total_failed']}")
        print(f"   Duration: {(stats['end_time'] - stats['start_time']).total_seconds():.1f}s")
        print()
        print(f"📁 Schemes saved to: data/processed/schemes/")

        # List some files
        scheme_dir = PROJECT_ROOT / 'data' / 'processed' / 'schemes'
        scheme_files = list(scheme_dir.glob('*.json'))
        print(f"   Total scheme files: {len(scheme_files)}")

        if scheme_files:
            print(f"   Sample files:")
            for f in scheme_files[:5]:
                print(f"     - {f.name}")

        return True

    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_eligibility_check():
    """Test eligibility checking with synced data"""
    print()
    print("🎯 Testing eligibility checker with data.gov.in schemes...")

    try:
        from data_processing.scheme_models import UserProfile, EligibilityGender, EligibilityCategory
        from eligibility.checker import EligibilityCheckerService

        # Create test user
        user = UserProfile(
            age=25,
            gender=EligibilityGender.MALE,
            category=EligibilityCategory.GENERAL,
            annual_income=300000,
            state="Maharashtra",
            occupation="Student",
            education="Graduate"
        )

        print(f"   Test user: {user.age}yo {user.gender.value} {user.occupation}")
        print(f"   Income: ₹{user.annual_income:,} | State: {user.state}")
        print()

        # Check eligibility
        checker = EligibilityCheckerService()
        results = checker.check_eligibility_for_all_schemes(user, rank_results=True)

        print(f"✅ Eligibility check complete!")
        print(f"   Total schemes checked: {results['total_schemes_checked']}")
        print(f"   Eligible schemes: {results['eligible_schemes']}")
        print(f"   Estimated benefit: {results['summary']['formatted_benefit']}")
        print()

        if results['top_10_schemes']:
            print("🏆 Top 3 Recommended Schemes:")
            for rank, ranked_scheme in enumerate(results['top_10_schemes'][:3], 1):
                scheme = ranked_scheme.scheme
                print(f"   {rank}. {scheme.name}")
                print(f"      Category: {', '.join([c.value for c in scheme.category])}")
                print(f"      Score: {ranked_scheme.final_score:.2f}")

        return True

    except Exception as e:
        print(f"❌ Eligibility check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_next_steps():
    """Show what to do next"""
    print()
    print("=" * 80)
    print(" " * 25 + "NEXT STEPS")
    print("=" * 80)
    print()
    print("✅ Your data.gov.in integration is ready!")
    print()
    print("📚 Learn more:")
    print("   Read: docs/DATA_GOV_IN_GUIDE.md")
    print()
    print("🔄 Set up auto-sync:")
    print("   python src/data_processing/scheme_sync_service.py --api-key YOUR_KEY --schedule")
    print()
    print("🧪 Run full tests:")
    print("   python scripts/test_eligibility.py")
    print()
    print("🚀 Start the app:")
    print("   streamlit run app.py")
    print()
    print("📊 View your schemes:")
    print("   ls data/processed/schemes/")
    print(f"   Total: {len(list((PROJECT_ROOT / 'data' / 'processed' / 'schemes').glob('*.json')))} schemes")
    print()


def main():
    """Main quick start flow"""

    # Step 1: Check API key
    api_key = check_api_key()
    if not api_key:
        print()
        print("⚠️  Cannot proceed without API key")
        print("   Please get your API key and try again")
        return

    # Step 2: Test connection
    if not test_api_connection(api_key):
        print()
        print("⚠️  API connection failed")
        print("   Fix the issue and try again")
        return

    # Step 3: Ask user if they want to sync
    print()
    sync = input("Do you want to sync schemes now? (y/n): ").strip().lower()

    if sync == 'y':
        if not run_first_sync(api_key):
            print()
            print("⚠️  Sync failed")
            return

        # Step 4: Test eligibility
        print()
        test = input("Do you want to test eligibility checking? (y/n): ").strip().lower()

        if test == 'y':
            test_eligibility_check()

    # Show next steps
    show_next_steps()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
