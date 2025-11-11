"""
Dependency Checker
Checks if all required and optional dependencies are installed
"""

import sys
import subprocess
from pathlib import Path

print("=" * 80)
print(" " * 25 + "DEPENDENCY CHECKER")
print("=" * 80)
print()

# Required dependencies (MUST be installed)
REQUIRED_DEPS = [
    ("pydantic", "Data validation and models"),
    ("numpy", "Numerical operations and embeddings"),
    ("streamlit", "Web UI framework"),
    ("python-dotenv", "Environment variable loading"),
    ("pyyaml", "Configuration file parsing"),
]

# Optional dependencies (Nice to have, graceful fallback)
OPTIONAL_DEPS = [
    ("docling", "Advanced PDF processing"),
    ("FlagEmbedding", "BGE-M3 embedding model (pip install FlagEmbedding)"),
    ("qdrant-client", "Vector database client"),
    ("tqdm", "Progress bars"),
    ("loguru", "Enhanced logging"),
    ("PyPDF2", "Basic PDF processing"),
    ("google-generativeai", "Gemini AI integration"),
]

# Development dependencies
DEV_DEPS = [
    ("pytest", "Testing framework"),
    ("black", "Code formatting"),
    ("flake8", "Code linting"),
]


def check_import(module_name):
    """Check if a module can be imported"""
    try:
        __import__(module_name.replace("-", "_"))
        return True
    except ImportError:
        return False


def get_version(package_name):
    """Get installed version of a package"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if line.startswith("Version:"):
                    return line.split(":")[1].strip()
        return None
    except:
        return None


def print_section(title):
    """Print section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print('='*80)
    print()


def check_dependencies(deps, dep_type):
    """Check a list of dependencies"""
    installed = []
    missing = []

    for package_name, description in deps:
        module_name = package_name.replace("-", "_")
        is_installed = check_import(module_name)
        version = get_version(package_name) if is_installed else None

        if is_installed:
            status = "✅"
            version_str = f"v{version}" if version else ""
            print(f"{status} {package_name:30} {version_str:15} {description}")
            installed.append(package_name)
        else:
            status = "❌"
            print(f"{status} {package_name:30} {'NOT INSTALLED':15} {description}")
            missing.append(package_name)

    return installed, missing


print_section("1. REQUIRED DEPENDENCIES")
print("These are CRITICAL - the app won't work without them")
print()

required_installed, required_missing = check_dependencies(REQUIRED_DEPS, "required")

print_section("2. OPTIONAL DEPENDENCIES")
print("These enhance functionality but have fallbacks")
print()

optional_installed, optional_missing = check_dependencies(OPTIONAL_DEPS, "optional")

print_section("3. DEVELOPMENT DEPENDENCIES")
print("These are for development and testing only")
print()

dev_installed, dev_missing = check_dependencies(DEV_DEPS, "development")

# Summary
print_section("SUMMARY")

total_required = len(REQUIRED_DEPS)
total_optional = len(OPTIONAL_DEPS)
total_dev = len(DEV_DEPS)

print(f"📦 Required Dependencies:")
print(f"   Installed: {len(required_installed)}/{total_required}")
if required_missing:
    print(f"   ❌ Missing: {', '.join(required_missing)}")
else:
    print(f"   ✅ All required dependencies installed!")

print(f"\n📦 Optional Dependencies:")
print(f"   Installed: {len(optional_installed)}/{total_optional}")
if optional_missing:
    print(f"   ⚠️  Missing: {', '.join(optional_missing)}")
    print(f"   Note: App will work but with reduced functionality")

print(f"\n📦 Development Dependencies:")
print(f"   Installed: {len(dev_installed)}/{total_dev}")

# Installation instructions
if required_missing or optional_missing:
    print_section("INSTALLATION INSTRUCTIONS")

    if required_missing:
        print("⚠️  CRITICAL: Install required dependencies first:")
        print()
        print("   pip install " + " ".join(required_missing))
        print()

    if optional_missing:
        print("💡 Recommended: Install optional dependencies for full functionality:")
        print()
        print("   pip install " + " ".join(optional_missing))
        print()

    print("Or install everything from requirements.txt:")
    print()
    print("   pip install -r requirements.txt")
    print()

if not required_missing:
    print_section("✅ READY TO GO!")
    print("All required dependencies are installed.")
    print()
    print("Next steps:")
    print("  1. Test eligibility engine: python scripts/test_eligibility.py")
    print("  2. Validate integration: python scripts/validate_integration.py")
    print("  3. Start Streamlit app: streamlit run app.py")
    print()

print("=" * 80)
