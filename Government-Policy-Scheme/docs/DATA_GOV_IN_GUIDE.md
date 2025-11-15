# 📚 Complete Guide: Using data.gov.in for Scheme Discovery

## 🎯 Overview

This guide shows you **exactly how** to leverage data.gov.in - India's official Open Government Data Platform - to power your Government Scheme Discovery AI.

---

## 🔑 Step 1: Get Your API Key (5 minutes)

### Option A: Online Registration (Recommended)

1. **Visit**: https://www.data.gov.in/
2. **Click**: "Sign Up" or "Register" (top right)
3. **Fill Form**:
   - Name
   - Email
   - Organization (can be "Individual" or "Educational")
   - Phone number
4. **Verify Email**: Check inbox for verification link
5. **Login**: Sign in to your account
6. **Get API Key**:
   - Go to "My Account" → "API Keys"
   - Click "Generate API Key"
   - **Copy and save** your API key

### Option B: Request via Email

If registration doesn't work:
- Email: **data-support@gov.in**
- Subject: "API Key Request for Educational Project"
- Mention: Government Scheme Discovery AI project

---

## 📦 Step 2: Install Dependencies

```bash
# Navigate to project
cd Government-Scheme-Eligibility

# Install required packages
pip install requests pydantic python-dotenv

# Optional: Install data.gov.in Python library
pip install datagovindia
```

---

## ⚙️ Step 3: Configure Your API Key

### Method 1: Environment Variable (Recommended)

```bash
# Edit .env file
nano .env

# Add this line:
DATA_GOV_API_KEY=your_actual_api_key_here
```

### Method 2: Direct Configuration

```python
# In your code
API_KEY = "your_actual_api_key_here"
```

---

## 🚀 Step 4: Run Your First Sync

### Quick Test

```bash
# Test API connection
python -c "
from src.data_processing.datagov_api import DataGovInAPI
api = DataGovInAPI(api_key='YOUR_KEY_HERE')
stats = api.get_scheme_statistics()
print(stats)
"
```

### Full Sync

```bash
# Sync all schemes from data.gov.in
python src/data_processing/scheme_sync_service.py --api-key YOUR_KEY_HERE

# Output will be in data/processed/schemes/
```

---

## 📊 What Data You'll Get

### Available Datasets on data.gov.in:

| Dataset | Resource ID | Schemes Count | Category |
|---------|-------------|---------------|----------|
| **Central Government Schemes** | `9ef84268-d588-465a-a308-a864a43d0070` | 200+ | General |
| **Social Welfare Schemes** | `6176ee09-3d56-4a3b-8115-21841576b996` | 150+ | Welfare |
| **Scholarship Schemes** | `2db6308f-9f56-4d7b-9aa7-f06e91846c28` | 100+ | Education |
| **PM Jan Dhan Yojana** | `efb0f614-1a71-4114-b0b8-3e8c2c8e8d3a` | 1 | Financial |
| **Agriculture Schemes** | Various | 80+ | Agriculture |

### Data Fields You Get:

```json
{
  "scheme_name": "PM-KISAN Samman Nidhi",
  "ministry": "Ministry of Agriculture",
  "description": "Income support to farmers",
  "benefit_amount": 6000,
  "eligibility": "Farmer with land",
  "application_url": "https://pmkisan.gov.in",
  "category": "Agriculture",
  "state": "All India",
  "documents_required": "Aadhaar, Bank Account",
  "helpline": "155261"
}
```

---

## 💻 Usage Examples

### Example 1: Fetch All Schemes

```python
from src.data_processing.datagov_api import DataGovInAPI

# Initialize API
api = DataGovInAPI(api_key='YOUR_API_KEY')

# Fetch all schemes
schemes = api.search_all_schemes()
print(f"Found {len(schemes)} schemes")

# Example output:
# Found 487 schemes
```

### Example 2: Search by Category

```python
# Search education schemes
education_schemes = api.search_schemes_by_category('Education')
print(f"Found {len(education_schemes)} education schemes")

# Search agriculture schemes
agriculture_schemes = api.search_schemes_by_category('Agriculture')
```

### Example 3: Get Statistics

```python
# Get overview statistics
stats = api.get_scheme_statistics()

print(f"Total schemes: {stats['total_schemes']}")
print(f"Sources: {stats['sources']}")

# Example output:
# Total schemes: 487
# Sources: {'central_schemes': 245, 'welfare_schemes': 156, ...}
```

### Example 4: Fetch Specific Resource

```python
# Fetch scholarship schemes only
scholarship_data = api.fetch_resource(
    resource_id='2db6308f-9f56-4d7b-9aa7-f06e91846c28',
    limit=100
)

records = scholarship_data['records']
```

### Example 5: Full Sync to Database

```python
from src.data_processing.scheme_sync_service import SchemeSyncService

# Create sync service
sync_service = SchemeSyncService(
    datagov_api_key='YOUR_API_KEY',
    output_dir='data/processed/schemes'
)

# Run full sync
stats = sync_service.run_full_sync()

print(f"Synced {stats['total_saved']} schemes")
print(f"Failed: {stats['total_failed']}")
```

---

## 🔄 Automation: Daily Auto-Sync

### Option 1: Run as Service

```bash
# Run daily sync (runs at 2 AM every day)
python src/data_processing/scheme_sync_service.py \
  --api-key YOUR_KEY \
  --schedule
```

### Option 2: Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * cd /path/to/Government-Scheme-Eligibility && python src/data_processing/scheme_sync_service.py --api-key YOUR_KEY
```

### Option 3: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2:00 AM
4. Action: Start Program
   - Program: `python`
   - Arguments: `src/data_processing/scheme_sync_service.py --api-key YOUR_KEY`
   - Start in: `C:\path\to\Government-Scheme-Eligibility`

---

## 📈 Integration with Your Eligibility Engine

### Step 1: Sync Data

```bash
python src/data_processing/scheme_sync_service.py --api-key YOUR_KEY
```

### Step 2: Test Eligibility

```bash
# Schemes are now in data/processed/schemes/
python scripts/test_eligibility.py
```

### Step 3: Use in Your App

```python
from src.eligibility import EligibilityCheckerService
from src.data_processing.scheme_models import UserProfile, EligibilityGender, EligibilityCategory

# Create user profile
user = UserProfile(
    age=25,
    gender=EligibilityGender.MALE,
    category=EligibilityCategory.GENERAL,
    annual_income=300000,
    state="Maharashtra",
    occupation="Student"
)

# Check eligibility (uses schemes from data.gov.in!)
checker = EligibilityCheckerService()
results = checker.check_eligibility_for_all_schemes(user)

print(f"Eligible for {results['eligible_schemes']} schemes")
print(f"Total benefit: {results['summary']['formatted_benefit']}")
```

---

## 🔍 Advanced Features

### Custom Resource IDs

Add more datasets by finding Resource IDs:

1. Visit: https://www.data.gov.in/
2. Search for scheme datasets
3. Click on dataset
4. Look for "Resource ID" in URL or API section
5. Add to `RESOURCE_IDS` in `datagov_api.py`

```python
RESOURCE_IDS = {
    'central_schemes': '9ef84268-d588-465a-a308-a864a43d0070',
    'your_new_dataset': 'NEW_RESOURCE_ID_HERE',  # Add here
}
```

### Caching Configuration

```python
# Cache for 24 hours (default)
api = DataGovInAPI(
    api_key='YOUR_KEY',
    cache_duration_hours=24
)

# Disable cache
api = DataGovInAPI(
    api_key='YOUR_KEY',
    cache_duration_hours=0
)
```

### Filtering Data

```python
# Fetch with filters
data = api.fetch_resource(
    resource_id='YOUR_RESOURCE_ID',
    filters={
        'state': 'Maharashtra',
        'category': 'Education'
    },
    limit=50
)
```

---

## 🐛 Troubleshooting

### Issue: "API Key Invalid"

**Solution:**
```bash
# Verify your key
curl "https://api.data.gov.in/resource/RESOURCE_ID?api-key=YOUR_KEY&format=json&limit=1"

# If error, regenerate key at data.gov.in
```

### Issue: "No Data Returned"

**Solution:**
- Check if resource ID is correct
- Try different resource IDs
- Verify API endpoint is accessible

### Issue: "Rate Limit Exceeded"

**Solution:**
```python
# Add delays between requests
import time
for resource in resources:
    data = api.fetch_resource(resource)
    time.sleep(2)  # 2-second delay
```

### Issue: "Cache Not Working"

**Solution:**
```bash
# Clear cache
rm -rf data/cache/datagov/*.json

# Disable cache temporarily
api = DataGovInAPI(api_key='KEY', cache_duration_hours=0)
```

---

## 📊 Data Quality Tips

### 1. Validate Converted Data

```python
from src.data_processing.scheme_models import GovernmentScheme

# Test conversion
converter = DataGovSchemeConverter()
scheme_data = converter.convert_to_scheme_model(raw_record)

# Validate with Pydantic
try:
    scheme = GovernmentScheme(**scheme_data)
    print("✅ Valid scheme")
except Exception as e:
    print(f"❌ Invalid: {e}")
```

### 2. Manual Review

```bash
# Review converted schemes
ls data/processed/schemes/
cat data/processed/schemes/datagov_*.json | jq .
```

### 3. Data Enrichment

If data.gov.in data is incomplete:
- Keep your manual JSON files
- Sync will merge both sources
- Manual data takes precedence

---

## 🎯 Best Practices

### ✅ DO:
- ✅ Cache API responses (saves bandwidth)
- ✅ Run sync during off-peak hours (2-6 AM)
- ✅ Validate converted data
- ✅ Keep manual schemes as supplements
- ✅ Monitor sync statistics
- ✅ Use rate limiting (1-2 seconds between calls)

### ❌ DON'T:
- ❌ Call API in real-time for every user request
- ❌ Sync more than once per day
- ❌ Ignore cache
- ❌ Delete manual schemes (merge instead)
- ❌ Expose API key in code (use .env)

---

## 📞 Support

### data.gov.in Support:
- **Email**: data-support@gov.in
- **Website**: https://www.data.gov.in/contact-us
- **Forum**: https://community.data.gov.in/

### Project Issues:
- Check `logs/app.log` for errors
- Run validation: `python scripts/validate_integration.py`
- Check dependencies: `python scripts/check_dependencies.py`

---

## 🚀 Next Steps

1. ✅ Get API key from data.gov.in
2. ✅ Run first sync: `python src/data_processing/scheme_sync_service.py`
3. ✅ Verify data: `ls data/processed/schemes/`
4. ✅ Test eligibility: `python scripts/test_eligibility.py`
5. ✅ Set up daily auto-sync
6. ✅ Integrate with Streamlit UI

---

## 📚 Additional Resources

- **data.gov.in Documentation**: https://www.data.gov.in/api-doc
- **Python Library**: https://pypi.org/project/datagovindia/
- **API Gateway**: https://apisetu.gov.in/
- **Open API Policy**: https://negd.gov.in/open-api/

---

**You're now ready to leverage India's official open data for your scheme discovery platform!** 🎉
