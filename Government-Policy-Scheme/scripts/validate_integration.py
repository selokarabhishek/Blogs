"""
Integration Validation Script
Performs comprehensive checks to ensure all components are properly integrated
"""

import sys
from pathlib import Path
import traceback

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print("=" * 80)
print(" " * 20 + "INTEGRATION VALIDATION SCRIPT")
print("=" * 80)
print()

# Track issues
issues = []
warnings = []
passed = []


def test_section(name):
    """Print test section header"""
    print(f"\n{'='*80}")
    print(f"  {name}")
    print('='*80)


def test_import(module_name, description):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {description}")
        passed.append(description)
        return True
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Error: {e}")
        issues.append(f"{description}: {e}")
        return False


def test_class_import(module_name, class_name, description):
    """Test if a specific class can be imported"""
    try:
        module = __import__(module_name, fromlist=[class_name])
        cls = getattr(module, class_name)
        print(f"✅ {description}")
        passed.append(description)
        return True
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Error: {e}")
        issues.append(f"{description}: {e}")
        return False


def test_file_exists(file_path, description):
    """Test if a file exists"""
    if file_path.exists():
        print(f"✅ {description}")
        passed.append(description)
        return True
    else:
        print(f"❌ {description}")
        issues.append(f"{description}: File not found at {file_path}")
        return False


def test_directory_structure():
    """Test project directory structure"""
    test_section("1. DIRECTORY STRUCTURE")

    required_dirs = [
        (PROJECT_ROOT / "src", "src/ directory"),
        (PROJECT_ROOT / "src/data_processing", "src/data_processing/"),
        (PROJECT_ROOT / "src/embeddings", "src/embeddings/"),
        (PROJECT_ROOT / "src/retrieval", "src/retrieval/"),
        (PROJECT_ROOT / "src/eligibility", "src/eligibility/"),
        (PROJECT_ROOT / "src/llm", "src/llm/"),
        (PROJECT_ROOT / "src/ui", "src/ui/"),
        (PROJECT_ROOT / "config", "config/"),
        (PROJECT_ROOT / "data/raw", "data/raw/"),
        (PROJECT_ROOT / "data/processed", "data/processed/"),
        (PROJECT_ROOT / "data/processed/schemes", "data/processed/schemes/"),
        (PROJECT_ROOT / "scripts", "scripts/"),
        (PROJECT_ROOT / "tests", "tests/"),
    ]

    for dir_path, desc in required_dirs:
        test_file_exists(dir_path, desc)


def test_config_files():
    """Test configuration files"""
    test_section("2. CONFIGURATION FILES")

    config_files = [
        (PROJECT_ROOT / "config/config.yaml", "config.yaml"),
        (PROJECT_ROOT / ".env.example", ".env.example"),
        (PROJECT_ROOT / ".gitignore", ".gitignore"),
        (PROJECT_ROOT / "requirements.txt", "requirements.txt"),
        (PROJECT_ROOT / "README.md", "README.md"),
    ]

    for file_path, desc in config_files:
        test_file_exists(file_path, desc)


def test_core_files():
    """Test core Python files"""
    test_section("3. CORE PYTHON FILES")

    core_files = [
        (PROJECT_ROOT / "src/__init__.py", "src/__init__.py"),
        (PROJECT_ROOT / "src/utils.py", "src/utils.py"),
        (PROJECT_ROOT / "app.py", "app.py"),
        (PROJECT_ROOT / "src/data_processing/__init__.py", "data_processing/__init__.py"),
        (PROJECT_ROOT / "src/data_processing/pdf_processor.py", "pdf_processor.py"),
        (PROJECT_ROOT / "src/data_processing/scheme_models.py", "scheme_models.py"),
        (PROJECT_ROOT / "src/embeddings/__init__.py", "embeddings/__init__.py"),
        (PROJECT_ROOT / "src/embeddings/bge_embedder.py", "bge_embedder.py"),
        (PROJECT_ROOT / "src/retrieval/__init__.py", "retrieval/__init__.py"),
        (PROJECT_ROOT / "src/retrieval/vector_store.py", "vector_store.py"),
        (PROJECT_ROOT / "src/eligibility/__init__.py", "eligibility/__init__.py"),
        (PROJECT_ROOT / "src/eligibility/matcher.py", "matcher.py"),
        (PROJECT_ROOT / "src/eligibility/ranker.py", "ranker.py"),
        (PROJECT_ROOT / "src/eligibility/checker.py", "checker.py"),
    ]

    for file_path, desc in core_files:
        test_file_exists(file_path, desc)


def test_scheme_data():
    """Test sample scheme data files"""
    test_section("4. SAMPLE SCHEME DATA")

    scheme_files = [
        (PROJECT_ROOT / "data/processed/schemes/pm_kisan.json", "PM-KISAN scheme"),
        (PROJECT_ROOT / "data/processed/schemes/nsp_scholarship.json", "NSP Scholarship scheme"),
        (PROJECT_ROOT / "data/processed/schemes/mudra_loan.json", "MUDRA Loan scheme"),
        (PROJECT_ROOT / "data/processed/schemes/pmay_housing.json", "PMAY Housing scheme"),
        (PROJECT_ROOT / "data/processed/schemes/ayushman_bharat.json", "Ayushman Bharat scheme"),
    ]

    for file_path, desc in scheme_files:
        test_file_exists(file_path, desc)


def test_module_imports():
    """Test if all modules can be imported"""
    test_section("5. MODULE IMPORTS")

    # Test basic imports
    test_import("utils", "utils module")

    # Test data processing
    test_class_import("data_processing.scheme_models", "GovernmentScheme", "GovernmentScheme model")
    test_class_import("data_processing.scheme_models", "UserProfile", "UserProfile model")
    test_class_import("data_processing.scheme_models", "EligibilityCriteria", "EligibilityCriteria model")
    test_class_import("data_processing.pdf_processor", "PDFProcessor", "PDFProcessor class")

    # Test embeddings
    test_class_import("embeddings.bge_embedder", "BGEEmbedder", "BGEEmbedder class")

    # Test retrieval
    test_class_import("retrieval.vector_store", "QdrantVectorStore", "QdrantVectorStore class")
    test_class_import("retrieval.vector_store", "HybridRetriever", "HybridRetriever class")

    # Test eligibility
    test_class_import("eligibility.matcher", "EligibilityMatcher", "EligibilityMatcher class")
    test_class_import("eligibility.ranker", "SchemeRanker", "SchemeRanker class")
    test_class_import("eligibility.checker", "EligibilityCheckerService", "EligibilityCheckerService class")


def test_scheme_loading():
    """Test loading scheme data"""
    test_section("6. SCHEME DATA LOADING")

    try:
        import json
        from data_processing.scheme_models import GovernmentScheme

        # Test loading a scheme
        scheme_path = PROJECT_ROOT / "data/processed/schemes/pm_kisan.json"
        with open(scheme_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        scheme = GovernmentScheme(**data)
        print(f"✅ Successfully loaded PM-KISAN scheme")
        print(f"   Scheme ID: {scheme.scheme_id}")
        print(f"   Name: {scheme.name}")
        print(f"   Benefit: ₹{scheme.benefits.amount:,.0f}" if scheme.benefits.amount else "   Benefit: Variable")
        passed.append("Scheme data loading")

    except Exception as e:
        print(f"❌ Failed to load scheme data")
        print(f"   Error: {e}")
        traceback.print_exc()
        issues.append(f"Scheme data loading: {e}")


def test_eligibility_matching():
    """Test eligibility matching functionality"""
    test_section("7. ELIGIBILITY MATCHING")

    try:
        from data_processing.scheme_models import (
            UserProfile, GovernmentScheme,
            EligibilityGender, EligibilityCategory
        )
        from eligibility.matcher import EligibilityMatcher
        import json

        # Create test user
        user = UserProfile(
            age=45,
            gender=EligibilityGender.MALE,
            category=EligibilityCategory.GENERAL,
            annual_income=150000,
            state="Punjab",
            occupation="Farmer",
        )
        print(f"✅ Created test user profile")

        # Load scheme
        scheme_path = PROJECT_ROOT / "data/processed/schemes/pm_kisan.json"
        with open(scheme_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        scheme = GovernmentScheme(**data)
        print(f"✅ Loaded PM-KISAN scheme")

        # Test matching
        matcher = EligibilityMatcher()
        match = matcher.check_eligibility(user, scheme)

        print(f"✅ Eligibility check completed")
        print(f"   Eligible: {match.is_eligible}")
        print(f"   Score: {match.overall_score:.2f}")
        print(f"   Matches checked: {len(match.matches)}")

        passed.append("Eligibility matching")

    except Exception as e:
        print(f"❌ Eligibility matching failed")
        print(f"   Error: {e}")
        traceback.print_exc()
        issues.append(f"Eligibility matching: {e}")


def test_scheme_ranking():
    """Test scheme ranking functionality"""
    test_section("8. SCHEME RANKING")

    try:
        from data_processing.scheme_models import (
            UserProfile, GovernmentScheme,
            EligibilityGender, EligibilityCategory
        )
        from eligibility.matcher import EligibilityMatcher
        from eligibility.ranker import SchemeRanker
        import json

        # Create test user
        user = UserProfile(
            age=45,
            gender=EligibilityGender.MALE,
            category=EligibilityCategory.GENERAL,
            annual_income=150000,
            state="Punjab",
            occupation="Farmer",
        )

        # Load schemes
        schemes = []
        scheme_dir = PROJECT_ROOT / "data/processed/schemes"
        for scheme_file in scheme_dir.glob("*.json"):
            with open(scheme_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            schemes.append(GovernmentScheme(**data))

        print(f"✅ Loaded {len(schemes)} schemes")

        # Check eligibility
        matcher = EligibilityMatcher()
        matches = [matcher.check_eligibility(user, s) for s in schemes]
        eligible_matches = [m for m in matches if m.is_eligible]

        print(f"✅ Found {len(eligible_matches)} eligible schemes")

        # Rank schemes
        ranker = SchemeRanker()
        ranked = ranker.rank_schemes(eligible_matches)

        print(f"✅ Ranked {len(ranked)} schemes")
        if ranked:
            print(f"   Top scheme: {ranked[0].scheme.name}")
            print(f"   Score: {ranked[0].final_score:.2f}")

        passed.append("Scheme ranking")

    except Exception as e:
        print(f"❌ Scheme ranking failed")
        print(f"   Error: {e}")
        traceback.print_exc()
        issues.append(f"Scheme ranking: {e}")


def test_eligibility_service():
    """Test complete eligibility service"""
    test_section("9. ELIGIBILITY CHECKER SERVICE")

    try:
        from data_processing.scheme_models import (
            UserProfile, EligibilityGender, EligibilityCategory
        )
        from eligibility.checker import EligibilityCheckerService

        # Create test user
        user = UserProfile(
            age=20,
            gender=EligibilityGender.FEMALE,
            category=EligibilityCategory.SC,
            annual_income=200000,
            state="Maharashtra",
            occupation="Student",
            education="12th Pass",
        )

        print(f"✅ Created student profile")

        # Create service
        service = EligibilityCheckerService()
        print(f"✅ Initialized EligibilityCheckerService")

        # Check eligibility
        results = service.check_eligibility_for_all_schemes(user, rank_results=True)

        print(f"✅ Checked eligibility for all schemes")
        print(f"   Total schemes: {results['total_schemes_checked']}")
        print(f"   Eligible: {results['eligible_schemes']}")
        print(f"   Top schemes: {len(results['top_10_schemes'])}")
        print(f"   Estimated benefit: {results['summary']['formatted_benefit']}")

        passed.append("Eligibility checker service")

    except Exception as e:
        print(f"❌ Eligibility service failed")
        print(f"   Error: {e}")
        traceback.print_exc()
        issues.append(f"Eligibility service: {e}")


def test_utils():
    """Test utility functions"""
    test_section("10. UTILITY FUNCTIONS")

    try:
        from utils import load_config, format_currency

        # Test config loading
        config = load_config()
        print(f"✅ Config loaded successfully")
        print(f"   App name: {config['app']['name']}")

        # Test currency formatting
        formatted = format_currency(250000)
        print(f"✅ Currency formatting works")
        print(f"   ₹2,50,000 → {formatted}")

        passed.append("Utility functions")

    except Exception as e:
        print(f"❌ Utility functions failed")
        print(f"   Error: {e}")
        traceback.print_exc()
        issues.append(f"Utility functions: {e}")


def print_summary():
    """Print validation summary"""
    test_section("VALIDATION SUMMARY")

    total_tests = len(passed) + len(issues) + len(warnings)

    print(f"\n📊 Test Results:")
    print(f"   Total tests: {total_tests}")
    print(f"   ✅ Passed: {len(passed)}")
    print(f"   ❌ Failed: {len(issues)}")
    print(f"   ⚠️  Warnings: {len(warnings)}")
    print()

    if issues:
        print("❌ ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print()

    if warnings:
        print("⚠️  WARNINGS:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
        print()

    if not issues:
        print("✅ ALL TESTS PASSED! Integration is successful.")
        print()
        print("🎉 Your Government Scheme Discovery AI is ready to use!")
        print()
        print("Next steps:")
        print("  1. Run eligibility test: python scripts/test_eligibility.py")
        print("  2. Start Streamlit app: streamlit run app.py")
        print("  3. Ingest more data: python scripts/ingest_data.py")
    else:
        print("⚠️  INTEGRATION ISSUES DETECTED")
        print("Please fix the issues above before proceeding.")

    print()
    print("=" * 80)


def main():
    """Run all validation tests"""
    try:
        test_directory_structure()
        test_config_files()
        test_core_files()
        test_scheme_data()
        test_module_imports()
        test_scheme_loading()
        test_eligibility_matching()
        test_scheme_ranking()
        test_eligibility_service()
        test_utils()

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during validation:")
        print(f"   {e}")
        traceback.print_exc()
        issues.append(f"Critical error: {e}")

    finally:
        print_summary()


if __name__ == '__main__':
    main()
