"""
PDF Processing Module using Docling
Extracts text, tables, and structured data from government scheme PDFs
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
except ImportError:
    logging.warning("Docling not installed. PDF processing will be limited.")
    DocumentConverter = None

try:
    from tqdm import tqdm
except ImportError:
    # Fallback: simple progress indicator
    def tqdm(iterable, desc=None, disable=False):
        """Simple fallback for tqdm"""
        return iterable

logger = logging.getLogger(__name__)


@dataclass
class ExtractedDocument:
    """Represents an extracted document with metadata"""
    file_path: str
    title: str
    content: str
    tables: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    chunks: List[str]


class PDFProcessor:
    """
    PDF processor using Docling for advanced document parsing
    Handles tables, forms, and scanned PDFs with OCR
    """

    def __init__(
        self,
        ocr_enabled: bool = True,
        extract_tables: bool = True,
        extract_images: bool = False,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        """
        Initialize PDF processor

        Args:
            ocr_enabled: Enable OCR for scanned PDFs
            extract_tables: Extract tables from PDFs
            extract_images: Extract images from PDFs
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks
        """
        self.ocr_enabled = ocr_enabled
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize Docling converter
        if DocumentConverter:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = ocr_enabled
            pipeline_options.do_table_structure = extract_tables

            self.converter = DocumentConverter(
                allowed_formats=[InputFormat.PDF],
                pipeline_options=pipeline_options,
            )
        else:
            self.converter = None
            logger.warning("Docling not available. Using fallback PDF processing.")

    def process_pdf(self, pdf_path: Path) -> ExtractedDocument:
        """
        Process a single PDF file

        Args:
            pdf_path: Path to PDF file

        Returns:
            ExtractedDocument with extracted content
        """
        logger.info(f"Processing PDF: {pdf_path}")

        if self.converter:
            return self._process_with_docling(pdf_path)
        else:
            return self._process_fallback(pdf_path)

    def _process_with_docling(self, pdf_path: Path) -> ExtractedDocument:
        """Process PDF using Docling"""
        try:
            # Convert document
            result = self.converter.convert(str(pdf_path))

            # Extract text content
            content = result.document.export_to_markdown()

            # Extract tables
            tables = []
            if self.extract_tables and hasattr(result.document, 'tables'):
                for table in result.document.tables:
                    tables.append({
                        'data': table.export_to_dataframe().to_dict() if hasattr(table, 'export_to_dataframe') else {},
                        'caption': getattr(table, 'caption', ''),
                    })

            # Extract metadata
            metadata = {
                'num_pages': getattr(result.document, 'num_pages', 0),
                'file_size': pdf_path.stat().st_size,
                'file_name': pdf_path.name,
            }

            # Create chunks
            chunks = self._create_chunks(content)

            # Extract title (first heading or filename)
            title = pdf_path.stem.replace('_', ' ').title()
            if hasattr(result.document, 'main_text'):
                first_lines = content.split('\n')[:3]
                for line in first_lines:
                    if line.strip() and len(line.strip()) > 5:
                        title = line.strip()
                        break

            return ExtractedDocument(
                file_path=str(pdf_path),
                title=title,
                content=content,
                tables=tables,
                metadata=metadata,
                chunks=chunks,
            )

        except Exception as e:
            logger.error(f"Error processing PDF with Docling: {e}")
            return self._process_fallback(pdf_path)

    def _process_fallback(self, pdf_path: Path) -> ExtractedDocument:
        """Fallback processing using PyPDF2"""
        try:
            import PyPDF2

            content = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    content += page.extract_text() + "\n"

            metadata = {
                'num_pages': len(reader.pages),
                'file_size': pdf_path.stat().st_size,
                'file_name': pdf_path.name,
            }

            chunks = self._create_chunks(content)
            title = pdf_path.stem.replace('_', ' ').title()

            return ExtractedDocument(
                file_path=str(pdf_path),
                title=title,
                content=content,
                tables=[],
                metadata=metadata,
                chunks=chunks,
            )

        except Exception as e:
            logger.error(f"Error in fallback processing: {e}")
            raise

    def _create_chunks(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text:
            return []

        chunks = []
        words = text.split()

        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())

        return chunks

    def process_directory(
        self,
        directory: Path,
        output_dir: Optional[Path] = None,
        save_json: bool = True,
    ) -> List[ExtractedDocument]:
        """
        Process all PDFs in a directory

        Args:
            directory: Directory containing PDFs
            output_dir: Directory to save processed JSON files
            save_json: Whether to save extracted data as JSON

        Returns:
            List of ExtractedDocuments
        """
        pdf_files = list(directory.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")

        documents = []

        for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                doc = self.process_pdf(pdf_file)
                documents.append(doc)

                # Save as JSON if requested
                if save_json and output_dir:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    json_path = output_dir / f"{pdf_file.stem}.json"

                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            'file_path': doc.file_path,
                            'title': doc.title,
                            'content': doc.content,
                            'tables': doc.tables,
                            'metadata': doc.metadata,
                            'num_chunks': len(doc.chunks),
                        }, f, indent=2, ensure_ascii=False)

            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                continue

        logger.info(f"Successfully processed {len(documents)}/{len(pdf_files)} PDFs")
        return documents


def extract_scheme_info(content: str) -> Dict[str, Any]:
    """
    Extract structured scheme information from document content
    Uses simple heuristics to identify key fields

    Args:
        content: Document text content

    Returns:
        Dictionary with extracted scheme information
    """
    scheme_info = {
        'name': '',
        'ministry': '',
        'benefits': '',
        'eligibility': '',
        'documents_required': [],
        'application_process': '',
        'contact': '',
    }

    # Simple keyword-based extraction
    lines = content.split('\n')

    for i, line in enumerate(lines):
        line_lower = line.lower()

        # Extract scheme name (usually in title or first few lines)
        if i < 5 and len(line.strip()) > 10 and not scheme_info['name']:
            scheme_info['name'] = line.strip()

        # Extract ministry
        if 'ministry' in line_lower or 'department' in line_lower:
            scheme_info['ministry'] = line.strip()

        # Extract benefits
        if 'benefit' in line_lower or 'subsidy' in line_lower or 'assistance' in line_lower:
            scheme_info['benefits'] += line.strip() + ' '

        # Extract eligibility
        if 'eligibility' in line_lower or 'eligible' in line_lower or 'criteria' in line_lower:
            # Capture next few lines
            scheme_info['eligibility'] += ' '.join(lines[i:i+3])

        # Extract documents required
        if 'document' in line_lower and 'required' in line_lower:
            # Capture next few lines
            for j in range(i+1, min(i+10, len(lines))):
                if lines[j].strip():
                    scheme_info['documents_required'].append(lines[j].strip())

    return scheme_info
