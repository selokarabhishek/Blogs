"""
Data Ingestion Pipeline
Orchestrates PDF processing, embedding generation, and vector DB insertion
"""

import sys
from pathlib import Path
import logging
import argparse
import json
from typing import List
import time

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data_processing.pdf_processor import PDFProcessor, ExtractedDocument
from data_processing.scheme_models import GovernmentScheme
from embeddings.bge_embedder import BGEEmbedder
from retrieval.vector_store import QdrantVectorStore
from utils import load_config, setup_logging, get_env_variable

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """
    Complete data ingestion pipeline
    PDF → Processed Text → Embeddings → Vector DB
    """

    def __init__(
        self,
        config_path: Path = None,
        use_gpu: bool = False,
    ):
        """
        Initialize pipeline

        Args:
            config_path: Path to config file
            use_gpu: Use GPU for embeddings
        """
        # Load configuration
        self.config = load_config(config_path)

        # Initialize PDF processor
        doc_config = self.config['document_processing']
        self.pdf_processor = PDFProcessor(
            ocr_enabled=doc_config['ocr_enabled'],
            extract_tables=doc_config['extract_tables'],
            chunk_size=doc_config['chunk_size'],
            chunk_overlap=doc_config['chunk_overlap'],
        )
        logger.info("PDF processor initialized")

        # Initialize embedder
        emb_config = self.config['embeddings']
        device = 'cuda' if use_gpu else emb_config['device']
        self.embedder = BGEEmbedder(
            model_name=emb_config['model_name'],
            device=device,
            batch_size=emb_config['batch_size'],
            max_length=emb_config['max_length'],
            normalize_embeddings=emb_config['normalize_embeddings'],
        )
        logger.info("Embedder initialized")

        # Initialize vector store
        db_config = self.config['vector_db']
        vector_db_path = get_env_variable('VECTOR_DB_PATH', str(PROJECT_ROOT / 'data' / 'vector_db'))

        self.vector_store = QdrantVectorStore(
            collection_name=db_config['collection_name'],
            vector_size=db_config['vector_size'],
            distance=db_config['distance_metric'],
            on_disk=db_config['on_disk'],
            path=vector_db_path,
        )
        logger.info("Vector store initialized")

    def process_pdfs(
        self,
        input_dir: Path,
        output_dir: Path = None,
    ) -> List[ExtractedDocument]:
        """
        Process all PDFs in directory

        Args:
            input_dir: Directory with PDF files
            output_dir: Output directory for processed files

        Returns:
            List of extracted documents
        """
        logger.info(f"Processing PDFs from {input_dir}")

        if output_dir is None:
            output_dir = PROJECT_ROOT / 'data' / 'processed'

        documents = self.pdf_processor.process_directory(
            directory=input_dir,
            output_dir=output_dir,
            save_json=True,
        )

        logger.info(f"Processed {len(documents)} PDF documents")
        return documents

    def load_schemes_from_json(self, json_dir: Path) -> List[GovernmentScheme]:
        """
        Load scheme data from JSON files

        Args:
            json_dir: Directory with scheme JSON files

        Returns:
            List of GovernmentScheme objects
        """
        logger.info(f"Loading schemes from {json_dir}")

        schemes = []
        json_files = list(json_dir.glob("*.json"))

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # If it's a scheme (has scheme_id), load it
                if isinstance(data, dict) and 'scheme_id' in data:
                    scheme = GovernmentScheme(**data)
                    schemes.append(scheme)
                # If it's a list of schemes
                elif isinstance(data, list):
                    for item in data:
                        if 'scheme_id' in item:
                            scheme = GovernmentScheme(**item)
                            schemes.append(scheme)

            except Exception as e:
                logger.error(f"Failed to load scheme from {json_file}: {e}")
                continue

        logger.info(f"Loaded {len(schemes)} schemes")
        return schemes

    def generate_embeddings(
        self,
        documents: List[ExtractedDocument] = None,
        schemes: List[GovernmentScheme] = None,
    ) -> tuple:
        """
        Generate embeddings for documents or schemes

        Args:
            documents: Extracted documents (from PDFs)
            schemes: Scheme objects (structured data)

        Returns:
            Tuple of (embeddings, metadata)
        """
        logger.info("Generating embeddings...")

        texts = []
        metadata = []

        # Process extracted documents
        if documents:
            for doc in documents:
                for i, chunk in enumerate(doc.chunks):
                    texts.append(chunk)
                    metadata.append({
                        'doc_id': f"{Path(doc.file_path).stem}_{i}",
                        'source_file': doc.file_path,
                        'title': doc.title,
                        'chunk_index': i,
                        'total_chunks': len(doc.chunks),
                        'content': chunk,
                        'type': 'document_chunk',
                    })

        # Process schemes
        if schemes:
            for scheme in schemes:
                # Embed full scheme content
                content = scheme._generate_searchable_content()
                texts.append(content)

                # Get metadata for vector DB
                scheme_metadata = scheme.to_vector_metadata()
                scheme_metadata['type'] = 'scheme'
                metadata.append(scheme_metadata)

        # Generate embeddings
        embeddings = self.embedder.encode(texts, show_progress=True)

        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings, metadata

    def ingest_to_vector_db(
        self,
        embeddings,
        metadata: List[dict],
    ):
        """
        Ingest embeddings and metadata to vector database

        Args:
            embeddings: Embedding vectors
            metadata: Metadata for each embedding
        """
        logger.info("Ingesting to vector database...")

        self.vector_store.add_documents(
            embeddings=embeddings,
            metadata=metadata,
            batch_size=100,
        )

        # Get collection info
        info = self.vector_store.get_collection_info()
        logger.info(f"Vector DB info: {info}")

    def run_full_pipeline(
        self,
        pdf_dir: Path = None,
        scheme_json_dir: Path = None,
        clear_existing: bool = False,
    ):
        """
        Run complete ingestion pipeline

        Args:
            pdf_dir: Directory with PDF files
            scheme_json_dir: Directory with scheme JSON files
            clear_existing: Clear existing data in vector DB
        """
        logger.info("=" * 80)
        logger.info("Starting Data Ingestion Pipeline")
        logger.info("=" * 80)

        start_time = time.time()

        # Clear existing data if requested
        if clear_existing:
            logger.warning("Clearing existing vector database...")
            self.vector_store.clear_collection()

        documents = []
        schemes = []

        # Process PDFs
        if pdf_dir and pdf_dir.exists():
            documents = self.process_pdfs(pdf_dir)
        else:
            logger.warning(f"PDF directory not found: {pdf_dir}")

        # Load schemes
        if scheme_json_dir and scheme_json_dir.exists():
            schemes = self.load_schemes_from_json(scheme_json_dir)
        else:
            logger.warning(f"Scheme JSON directory not found: {scheme_json_dir}")

        # Generate embeddings
        if documents or schemes:
            embeddings, metadata = self.generate_embeddings(
                documents=documents,
                schemes=schemes,
            )

            # Ingest to vector DB
            self.ingest_to_vector_db(embeddings, metadata)
        else:
            logger.error("No documents or schemes to process!")

        elapsed_time = time.time() - start_time
        logger.info("=" * 80)
        logger.info(f"Pipeline completed in {elapsed_time:.2f} seconds")
        logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Data Ingestion Pipeline")
    parser.add_argument(
        '--pdf-dir',
        type=Path,
        default=PROJECT_ROOT / 'data' / 'raw',
        help='Directory with PDF files',
    )
    parser.add_argument(
        '--scheme-json-dir',
        type=Path,
        default=PROJECT_ROOT / 'data' / 'processed' / 'schemes',
        help='Directory with scheme JSON files',
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=PROJECT_ROOT / 'config' / 'config.yaml',
        help='Config file path',
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing vector database',
    )
    parser.add_argument(
        '--gpu',
        action='store_true',
        help='Use GPU for embeddings',
    )

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = DataIngestionPipeline(
        config_path=args.config,
        use_gpu=args.gpu,
    )

    # Run pipeline
    pipeline.run_full_pipeline(
        pdf_dir=args.pdf_dir,
        scheme_json_dir=args.scheme_json_dir,
        clear_existing=args.clear,
    )


if __name__ == '__main__':
    main()
