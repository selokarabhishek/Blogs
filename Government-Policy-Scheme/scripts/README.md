# Scripts Directory

This directory contains utility scripts for the Government Scheme Discovery AI project.

## Available Scripts

### 1. `ingest_data.py`

Main data ingestion pipeline that orchestrates PDF processing, embedding generation, and vector database population.

**Usage:**

```bash
# Basic usage (process all PDFs and schemes)
python scripts/ingest_data.py

# Specify custom directories
python scripts/ingest_data.py \
  --pdf-dir /path/to/pdfs \
  --scheme-json-dir /path/to/schemes \
  --config /path/to/config.yaml

# Clear existing data and reload
python scripts/ingest_data.py --clear

# Use GPU for faster embedding generation
python scripts/ingest_data.py --gpu
```

**Options:**
- `--pdf-dir`: Directory containing PDF files (default: `data/raw`)
- `--scheme-json-dir`: Directory containing scheme JSON files (default: `data/processed/schemes`)
- `--config`: Path to config file (default: `config/config.yaml`)
- `--clear`: Clear existing vector database before ingestion
- `--gpu`: Use GPU for embedding generation (requires CUDA)

**What it does:**
1. Processes PDF files using Docling
2. Loads structured scheme data from JSON files
3. Generates BGE-M3 embeddings for all content
4. Ingests embeddings into Qdrant vector database

## Pipeline Workflow

```
PDFs → Docling Processing → Text Chunks
                                ↓
Scheme JSONs → Validation → Structured Data
                                ↓
        BGE-M3 Embedding Generation
                                ↓
        Qdrant Vector Database
```

## Requirements

Before running the scripts, ensure:

1. **Python environment** is set up with all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment variables** are configured (copy `.env.example` to `.env`):
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

3. **Qdrant** is running (optional - will use embedded mode if not):
   ```bash
   # Using Docker
   docker run -p 6333:6333 qdrant/qdrant

   # Or use embedded mode (automatic if no Qdrant server found)
   ```

## Sample Data

Sample scheme data is available in `data/processed/schemes/`:
- `pm_kisan.json` - PM-KISAN farmer support scheme
- `nsp_scholarship.json` - NSP scholarship for SC/ST/OBC
- `mudra_loan.json` - MUDRA business loans
- `pmay_housing.json` - PMAY housing subsidy
- `ayushman_bharat.json` - Ayushman Bharat health insurance

## Troubleshooting

### Issue: Docling not working
**Solution:** Docling requires specific dependencies. Install with:
```bash
pip install docling --upgrade
```

### Issue: BGE-M3 model download fails
**Solution:** The model (~2GB) downloads on first run. Ensure stable internet:
```bash
# Pre-download the model
python -c "from FlagEmbedding import BGEM3FlagModel; BGEM3FlagModel('BAAI/bge-m3')"
```

### Issue: Qdrant connection error
**Solution:** Use embedded mode by setting path in config:
```yaml
vector_db:
  path: "data/vector_db"  # This enables embedded mode
```

### Issue: Out of memory during embedding
**Solution:** Reduce batch size in `config/config.yaml`:
```yaml
embeddings:
  batch_size: 16  # Reduce from 32
```

## Performance Tips

1. **Use GPU**: If available, use `--gpu` flag for 5-10x faster embedding generation
2. **Batch processing**: Process PDFs in smaller batches for large datasets
3. **Incremental updates**: Don't use `--clear` flag for incremental updates
4. **Monitor logs**: Check `logs/app.log` for detailed progress

## Next Steps

After running the ingestion pipeline:
1. Verify data in Qdrant: Check collection info in logs
2. Test search: Use the retrieval module to test searches
3. Update schemes: Add more scheme JSON files and re-run without `--clear`
4. Build UI: Launch Streamlit app to interact with the data
