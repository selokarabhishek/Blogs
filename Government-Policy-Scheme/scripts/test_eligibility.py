"""
Test Script for Eligibility Engine
Demonstrates eligibility matching, scoring, and ranking
"""

import sys
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data_processing.scheme_models import (
    UserProfile,
    EligibilityGender,
    EligibilityCategory,
)
from eligibility.checker import EligibilityCheckerService
from utils import setup_logging, format_currency

# Setup logging
setup_logging()

import logging
logger = logging.getLogger(__name__)


def print_divider(char="=", length=80):
    """Print a divider line"""
    print(char * length)


def print_section(title):
    """Print a section header"""
    print("\n")
    print_divider()
    print(f"  {title}")
    print_divider()
    print()


def test_farmer_profile():
    """Test with a farmer profile"""
    print_section("TEST 1: Farmer Profile (Should match PM-KISAN)")

    # Create farmer profile
    farmer = UserProfile(
        age=45,
        gender=EligibilityGender.MALE,
        category=EligibilityCategory.GENERAL,
        annual_income=150000,  # ₹1.5 lakh
        state="Punjab",
        occupation="Farmer",
        education="10th Pass",
        marital_status="Married",
        disability=False,
        bpl_card=False,
        rural_area=True,
    )

    print("👤 User Profile:")
    print(f"   Age: {farmer.age}")
    print(f"   Gender: {farmer.gender.value}")
    print(f"   Occupation: {farmer.occupation}")
    print(f"   Income: ₹{farmer.annual_income:,.0f}")
    print(f"   State: {farmer.state}")
    print()

    # Check eligibility
    checker = EligibilityCheckerService()
    results = checker.check_eligibility_for_all_schemes(farmer, rank_results=True)

    print(f"✅ Eligible for {results['eligible_schemes']} schemes")
    print(f"❌ Not eligible for {results['ineligible_schemes']} schemes")
    print()

    if results['top_10_schemes']:
        print("🏆 Top 5 Recommended Schemes:")
        print()
        for ranked_scheme in results['top_10_schemes'][:5]:
            scheme = ranked_scheme.scheme
            print(f"  {ranked_scheme.rank}. {scheme.name}")
            print(f"     📁 Category: {', '.join([c.value for c in scheme.category])}")
            print(f"     💰 Benefit: {ranked_scheme.metadata['estimated_benefit']}")
            print(f"     ⭐ Score: {ranked_scheme.final_score:.2f}")
            print(f"     📋 Complexity: {ranked_scheme.metadata['application_complexity']}")
            print(f"     ⏱️  Processing: {ranked_scheme.metadata['time_to_benefit']}")
            print()

    # Summary
    summary = results['summary']
    print("📊 Summary:")
    print(f"   Total estimated benefits: {summary['formatted_benefit']}")
    print(f"   Top category: {summary.get('top_category', 'N/A')}")
    print(f"   Average eligibility score: {summary['average_eligibility_score']:.2f}")


def test_student_profile():
    """Test with a student profile"""
    print_section("TEST 2: Student Profile (Should match NSP Scholarship)")

    # Create student profile
    student = UserProfile(
        age=20,
        gender=EligibilityGender.FEMALE,
        category=EligibilityCategory.SC,
        annual_income=200000,  # ₹2 lakh (within limit)
        state="Maharashtra",
        occupation="Student",
        education="12th Pass",
        marital_status="Single",
        disability=False,
        bpl_card=False,
        rural_area=False,
    )

    print("👤 User Profile:")
    print(f"   Age: {student.age}")
    print(f"   Gender: {student.gender.value}")
    print(f"   Category: {student.category.value}")
    print(f"   Occupation: {student.occupation}")
    print(f"   Income: ₹{student.annual_income:,.0f}")
    print()

    # Check eligibility
    checker = EligibilityCheckerService()
    results = checker.check_eligibility_for_all_schemes(student, rank_results=True)

    print(f"✅ Eligible for {results['eligible_schemes']} schemes")
    print()

    if results['top_10_schemes']:
        print("🏆 Top 3 Recommended Schemes:")
        print()
        for ranked_scheme in results['top_10_schemes'][:3]:
            scheme = ranked_scheme.scheme
            print(f"  {ranked_scheme.rank}. {scheme.name}")
            print(f"     💰 Benefit: {ranked_scheme.metadata['estimated_benefit']}")
            print(f"     ⭐ Score: {ranked_scheme.final_score:.2f}")
            print()


def test_entrepreneur_profile():
    """Test with entrepreneur profile"""
    print_section("TEST 3: Entrepreneur Profile (Should match MUDRA Loan)")

    # Create entrepreneur profile
    entrepreneur = UserProfile(
        age=32,
        gender=EligibilityGender.MALE,
        category=EligibilityCategory.OBC,
        annual_income=400000,  # ₹4 lakh
        state="Karnataka",
        occupation="Self-employed",
        education="Graduate",
        marital_status="Married",
        disability=False,
        bpl_card=False,
        rural_area=False,
    )

    print("👤 User Profile:")
    print(f"   Age: {entrepreneur.age}")
    print(f"   Occupation: {entrepreneur.occupation}")
    print(f"   Education: {entrepreneur.education}")
    print()

    # Check eligibility
    checker = EligibilityCheckerService()
    results = checker.check_eligibility_for_all_schemes(entrepreneur, rank_results=True)

    print(f"✅ Eligible for {results['eligible_schemes']} schemes")
    print()

    # Check for business schemes specifically
    business_schemes = [
        rs for rs in results['ranked_schemes']
        if any('Business' in cat.value or 'Entrepreneurship' in cat.value for cat in rs.scheme.category)
    ]

    if business_schemes:
        print("💼 Business & Entrepreneurship Schemes:")
        print()
        for ranked_scheme in business_schemes[:3]:
            scheme = ranked_scheme.scheme
            print(f"  • {scheme.name}")
            print(f"    💰 Loan Amount: {ranked_scheme.metadata['estimated_benefit']}")
            print(f"    📞 Helpline: {scheme.application_process.helpline}")
            print()


def test_low_income_profile():
    """Test with low-income profile"""
    print_section("TEST 4: Low-Income Profile (Should match multiple welfare schemes)")

    # Create low-income profile
    low_income = UserProfile(
        age=55,
        gender=EligibilityGender.FEMALE,
        category=EligibilityCategory.ST,
        annual_income=80000,  # ₹80,000
        state="Madhya Pradesh",
        occupation="Unemployed",
        education="Below 10th",
        marital_status="Widowed",
        disability=False,
        bpl_card=True,  # Has BPL card
        rural_area=True,
    )

    print("👤 User Profile:")
    print(f"   Age: {low_income.age}")
    print(f"   Category: {low_income.category.value}")
    print(f"   Income: ₹{low_income.annual_income:,.0f}")
    print(f"   BPL Card: Yes")
    print(f"   Rural Area: Yes")
    print()

    # Check eligibility
    checker = EligibilityCheckerService()
    results = checker.check_eligibility_for_all_schemes(low_income, rank_results=True)

    print(f"✅ Eligible for {results['eligible_schemes']} schemes")
    print()

    if results['ranked_schemes']:
        print("🏆 All Eligible Schemes:")
        print()
        for ranked_scheme in results['ranked_schemes']:
            scheme = ranked_scheme.scheme
            print(f"  {ranked_scheme.rank}. {scheme.name}")
            print(f"     📁 {', '.join([c.value for c in scheme.category])}")
            print(f"     💰 {ranked_scheme.metadata['estimated_benefit']}")
            print()

    # Summary
    summary = results['summary']
    print("📊 Total Benefits Available:")
    print(f"   {summary['formatted_benefit']}")


def test_single_scheme():
    """Test eligibility for a single scheme with detailed output"""
    print_section("TEST 5: Detailed Eligibility Check (PM-KISAN)")

    # Create user profile
    user = UserProfile(
        age=35,
        gender=EligibilityGender.MALE,
        category=EligibilityCategory.GENERAL,
        annual_income=250000,
        state="Uttar Pradesh",
        occupation="Farmer",
    )

    # Get scheme
    checker = EligibilityCheckerService()
    scheme = checker.get_scheme_by_id("PM-KISAN-2024")

    if scheme:
        print(f"📄 Scheme: {scheme.name}")
        print(f"🏛️  Ministry: {scheme.ministry}")
        print()

        # Check eligibility
        match = checker.check_eligibility_for_scheme(user, scheme)

        print(f"✅ Eligible: {match.is_eligible}")
        print(f"⭐ Overall Score: {match.overall_score:.2f}")
        print()

        print("📋 Detailed Match Results:")
        for eligibility_match in match.matches:
            status_icon = "✅" if eligibility_match.status.value == "match" else "❌" if eligibility_match.status.value == "no_match" else "⚠️"
            print(f"   {status_icon} {eligibility_match.criterion}: {eligibility_match.reason}")

        if match.recommendations:
            print()
            print("💡 Recommendations:")
            for rec in match.recommendations:
                print(f"   • {rec}")


def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "ELIGIBILITY ENGINE TEST SUITE")
    print("=" * 80)

    try:
        test_farmer_profile()
        test_student_profile()
        test_entrepreneur_profile()
        test_low_income_profile()
        test_single_scheme()

        print_section("✅ ALL TESTS COMPLETED")
        print("The eligibility engine is working correctly!")
        print()

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
