# Government Scheme Discovery AI 🇮🇳

**AI-powered platform to help Indians discover and claim billions in unclaimed government benefits**

## 🎯 The Problem

- India has **1,000+ government schemes** (education, housing, agriculture, business loans, etc.)
- Nobody knows what they qualify for
- Application forms are nightmares
- Schemes have **₹10,000 crore allocated but underclaimed**
- Middle-class misses out because "schemes are for poor people" (false!)

## 💡 Why This is TRANSFORMATIVE

- People leave **₹50,000-5,00,000** on the table (grants, subsidies, low-interest loans)
- Every age group benefits:
  - Students (scholarships)
  - Farmers (PM-Kisan)
  - Businesses (Mudra loans)
  - Women (Stree Shakti)
  - Seniors (pensions)
- Government **WANTS** people to use schemes (it's allocated budget)

## 🚀 The AI Solution

### 1. **Discovery**
Answer 10 questions → AI shows ALL schemes you qualify for
> "You qualify for 23 schemes worth ₹2,45,000"

### 2. **Application Assistant**
- "Scheme requires Aadhaar, Income Certificate, Bank Statement"
- Auto-fills forms using document parsing
- Tracks application status

### 3. **Success Stories**
> "1.2L users claimed ₹450 crore in benefits"

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ USER INTERFACE (Streamlit)                                  │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│ │ Profile Form │ │ Scheme Cards │ │ Chat Widget  │         │
│ └──────────────┘ └──────────────┘ └──────────────┘         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ ORCHESTRATION LAYER (Python)                                │
│ ┌────────────────┐ ┌────────────────┐                       │
│ │ Eligibility    │ │ User Profile   │                       │
│ │ Checker        │ │ Store          │                       │
│ └───────┬────────┘ └────────────────┘                       │
│         │                                                    │
│         ▼                                                    │
│ ┌────────────────┐ ┌────────────────┐                       │
│ │ Hybrid         │ │ Query          │                       │
│ │ Retriever      │ │ Processing     │                       │
│ └───────┬────────┘ └────────────────┘                       │
│         │                                                    │
│         ▼                                                    │
│ ┌────────────────┐ ┌────────────────┐                       │
│ │ Response       │ │ Citation       │                       │
│ │ Generator      │ │ Builder        │                       │
│ └────────────────┘ └────────────────┘                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ DATA LAYER                                                   │
│ ┌────────────────┐ ┌────────────────┐ ┌──────────────┐     │
│ │ Qdrant Vector  │ │ Structured     │ │ Source PDFs  │     │
│ │ Database       │ │ Scheme JSON    │ │ (Docling)    │     │
│ └────────────────┘ └────────────────┘ └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ EXTERNAL SERVICES                                            │
│ ┌────────────────┐ ┌────────────────┐                       │
│ │ Gemini 2.0     │ │ BGE-M3         │                       │
│ │ Flash API      │ │ (Local)        │                       │
│ └────────────────┘ └────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| **Doc Processing** | Docling | Handles tables, forms, scanned PDFs perfectly |
| **Embeddings** | BGE-M3 | Multilingual, longer context, free |
| **Vector DB** | Qdrant | Best metadata filtering for eligibility |
| **LLM** | Gemini 2.0 Flash | 1M context, free tier, grounding |
| **UI** | Streamlit | Fastest MVP, built-in state management |

## 📂 Project Structure

```
Government-Policy-Scheme/
├── data/
│   ├── raw/              # Source PDFs, scraped data
│   ├── processed/        # Processed JSON, embeddings
│   └── vector_db/        # Qdrant database files
├── src/
│   ├── data_processing/  # Docling processing, scraping
│   ├── embeddings/       # BGE-M3 embedding generation
│   ├── retrieval/        # Hybrid retriever logic
│   ├── eligibility/      # Eligibility checker engine
│   ├── llm/              # Gemini integration
│   └── ui/               # Streamlit components
├── config/               # Configuration files
├── notebooks/            # Jupyter notebooks for experimentation
├── tests/                # Unit tests
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── app.py                # Main Streamlit app
```

## 🚦 Getting Started

### Prerequisites
- Python 3.9+
- Gemini API Key (free tier available)
- 4GB RAM minimum
- (Optional) GPU for faster embeddings

### Installation

1. **Clone the repository**
```bash
git clone <repo-url>
cd Government-Policy-Scheme
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

5. **Run the application**
```bash
streamlit run app.py
```

## 🎯 Weekend MVP Checklist

- [x] Project setup (folder structure, requirements, config)
- [ ] Scrape government scheme databases
- [ ] Build eligibility logic tree
- [ ] Simple questionnaire interface
- [ ] Document checklist generator
- [ ] Qdrant setup with BGE-M3 embeddings
- [ ] Gemini 2.0 Flash integration
- [ ] Basic Streamlit UI

## 🎨 Features

### Phase 1 (Weekend MVP)
- ✅ User profile questionnaire (10 questions)
- ✅ Eligibility matching algorithm
- ✅ Scheme discovery and display
- ✅ Document requirement checklist

### Phase 2 (Future)
- 🔄 Form auto-filling
- 🔄 Application status tracking
- 🔄 Document parsing and upload
- 🔄 Alerts for new schemes
- 🔄 Multi-language support (Hindi, regional)

## 💰 Market Opportunity

- **100M+ eligible Indians** don't know about schemes
- **Freemium Model**: Free eligibility check, ₹499 for application assistance
- **B2B**: Banks, NBFCs (cross-sell loans vs schemes)

## 🎯 Target Users

1. **Students** - Scholarships, education loans
2. **Farmers** - PM-Kisan, crop insurance, subsidies
3. **Entrepreneurs** - Mudra loans, startup schemes
4. **Women** - Self-help groups, Stree Shakti
5. **Senior Citizens** - Pensions, healthcare
6. **Middle Class** - Housing schemes, tax benefits

## 🔐 Security & Privacy

- No storage of personal documents
- Encrypted user data
- Compliance with IT Act 2000
- No third-party data sharing

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines.

## 📄 License

MIT License - See LICENSE file for details

## 📧 Contact

For queries or collaboration: [Your Email]

---

**Built with ❤️ to help Indians claim their rightful benefits**
