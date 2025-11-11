"""
BGE-M3 Embedding Generator
Multilingual embedding model optimized for retrieval tasks
"""

import logging
from typing import List, Union, Optional
from pathlib import Path
import pickle

try:
    import numpy as np
except ImportError:
    logging.error("NumPy is required. Install with: pip install numpy")
    raise

try:
    from FlagEmbedding import BGEM3FlagModel
except ImportError:
    logging.warning("FlagEmbedding not installed. Install with: pip install FlagEmbedding")
    BGEM3FlagModel = None

try:
    from tqdm import tqdm
except ImportError:
    # Fallback: simple progress indicator
    def tqdm(iterable, desc=None, disable=False):
        """Simple fallback for tqdm"""
        return iterable

logger = logging.getLogger(__name__)


class BGEEmbedder:
    """
    BGE-M3 embedding generator
    Supports dense vectors, sparse vectors, and multi-vector representations
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cpu",
        batch_size: int = 32,
        max_length: int = 8192,
        normalize_embeddings: bool = True,
        use_fp16: bool = False,
    ):
        """
        Initialize BGE-M3 embedder

        Args:
            model_name: HuggingFace model name
            device: Device to run model on ('cpu' or 'cuda')
            batch_size: Batch size for encoding
            max_length: Maximum sequence length
            normalize_embeddings: Whether to L2 normalize embeddings
            use_fp16: Use FP16 precision (faster on GPU)
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.max_length = max_length
        self.normalize_embeddings = normalize_embeddings
        self.use_fp16 = use_fp16

        logger.info(f"Initializing BGE-M3 model: {model_name} on {device}")

        if BGEM3FlagModel is None:
            raise ImportError("FlagEmbedding not installed. Install with: pip install FlagEmbedding")

        # Load model
        self.model = BGEM3FlagModel(
            model_name,
            use_fp16=use_fp16,
            device=device,
        )

        logger.info(f"Model loaded successfully. Embedding dimension: {self.get_embedding_dim()}")

    def get_embedding_dim(self) -> int:
        """Get embedding dimension"""
        # BGE-M3 has 1024 dimensions
        return 1024

    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode texts into dense embeddings

        Args:
            texts: Single text or list of texts
            show_progress: Show progress bar

        Returns:
            Numpy array of embeddings (n_texts, embedding_dim)
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return np.array([])

        logger.info(f"Encoding {len(texts)} texts...")

        embeddings = []

        # Process in batches
        for i in tqdm(
            range(0, len(texts), self.batch_size),
            desc="Encoding batches",
            disable=not show_progress,
        ):
            batch = texts[i:i + self.batch_size]

            # Encode batch
            batch_embeddings = self.model.encode(
                batch,
                batch_size=len(batch),
                max_length=self.max_length,
            )['dense_vecs']

            embeddings.append(batch_embeddings)

        # Concatenate all batches
        embeddings = np.vstack(embeddings)

        # Normalize if requested
        if self.normalize_embeddings:
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings

    def encode_queries(
        self,
        queries: Union[str, List[str]],
    ) -> np.ndarray:
        """
        Encode queries (optimized for retrieval)

        Args:
            queries: Single query or list of queries

        Returns:
            Numpy array of query embeddings
        """
        if isinstance(queries, str):
            queries = [queries]

        # BGE-M3 uses the same encoding for queries and documents
        # But we can add query instruction for better retrieval
        queries_with_instruction = [f"Represent this query for retrieving relevant documents: {q}" for q in queries]

        return self.encode(queries_with_instruction)

    def encode_with_sparse(
        self,
        texts: Union[str, List[str]],
    ) -> dict:
        """
        Encode texts with both dense and sparse representations

        Args:
            texts: Single text or list of texts

        Returns:
            Dictionary with 'dense' and 'sparse' embeddings
        """
        if isinstance(texts, str):
            texts = [texts]

        logger.info(f"Encoding {len(texts)} texts with dense + sparse representations...")

        # BGE-M3 supports multi-vector output
        outputs = self.model.encode(
            texts,
            batch_size=self.batch_size,
            max_length=self.max_length,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,  # ColBERT vectors optional
        )

        result = {
            'dense': outputs['dense_vecs'],
            'sparse': outputs.get('lexical_weights', None),
        }

        if self.normalize_embeddings:
            result['dense'] = result['dense'] / np.linalg.norm(result['dense'], axis=1, keepdims=True)

        return result

    def compute_similarity(
        self,
        embeddings1: np.ndarray,
        embeddings2: np.ndarray,
    ) -> np.ndarray:
        """
        Compute cosine similarity between embeddings

        Args:
            embeddings1: First set of embeddings (n, dim)
            embeddings2: Second set of embeddings (m, dim)

        Returns:
            Similarity matrix (n, m)
        """
        # Normalize if not already normalized
        if not self.normalize_embeddings:
            embeddings1 = embeddings1 / np.linalg.norm(embeddings1, axis=1, keepdims=True)
            embeddings2 = embeddings2 / np.linalg.norm(embeddings2, axis=1, keepdims=True)

        # Compute cosine similarity
        similarity = np.dot(embeddings1, embeddings2.T)
        return similarity

    def save_embeddings(
        self,
        embeddings: np.ndarray,
        metadata: List[dict],
        output_path: Path,
    ):
        """
        Save embeddings and metadata to disk

        Args:
            embeddings: Embedding matrix
            metadata: List of metadata dictionaries
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'embeddings': embeddings,
            'metadata': metadata,
            'model_name': self.model_name,
            'embedding_dim': self.get_embedding_dim(),
        }

        with open(output_path, 'wb') as f:
            pickle.dump(data, f)

        logger.info(f"Saved embeddings to {output_path}")

    @staticmethod
    def load_embeddings(input_path: Path) -> dict:
        """
        Load embeddings from disk

        Args:
            input_path: Input file path

        Returns:
            Dictionary with embeddings and metadata
        """
        with open(input_path, 'rb') as f:
            data = pickle.load(f)

        logger.info(f"Loaded embeddings from {input_path}")
        return data


class HybridEmbedder:
    """
    Hybrid embedder combining dense BGE-M3 embeddings with sparse representations
    """

    def __init__(
        self,
        bge_embedder: BGEEmbedder,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
    ):
        """
        Initialize hybrid embedder

        Args:
            bge_embedder: BGE embedder instance
            dense_weight: Weight for dense embeddings
            sparse_weight: Weight for sparse embeddings
        """
        self.bge_embedder = bge_embedder
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight

        assert abs(dense_weight + sparse_weight - 1.0) < 1e-6, "Weights must sum to 1.0"

    def encode(self, texts: Union[str, List[str]]) -> dict:
        """
        Encode texts with hybrid representation

        Args:
            texts: Texts to encode

        Returns:
            Dictionary with dense and sparse embeddings
        """
        return self.bge_embedder.encode_with_sparse(texts)

    def compute_hybrid_score(
        self,
        dense_scores: np.ndarray,
        sparse_scores: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Compute hybrid scores from dense and sparse similarities

        Args:
            dense_scores: Dense similarity scores
            sparse_scores: Sparse similarity scores (optional)

        Returns:
            Combined hybrid scores
        """
        if sparse_scores is None:
            return dense_scores

        # Combine scores with weights
        hybrid_scores = (
            self.dense_weight * dense_scores +
            self.sparse_weight * sparse_scores
        )

        return hybrid_scores
