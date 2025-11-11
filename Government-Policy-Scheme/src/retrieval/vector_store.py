"""
Qdrant Vector Store Manager
Handles storage and retrieval of embeddings for government schemes
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import uuid

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
        Range,
        SearchParams,
    )
except ImportError:
    logging.warning("Qdrant client not installed. Install with: pip install qdrant-client")
    QdrantClient = None

try:
    import numpy as np
except ImportError:
    logging.error("NumPy is required. Install with: pip install numpy")
    raise

try:
    from tqdm import tqdm
except ImportError:
    # Fallback: simple progress indicator
    def tqdm(iterable, desc=None, disable=False):
        """Simple fallback for tqdm"""
        return iterable

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """
    Qdrant vector database manager for scheme embeddings
    Supports metadata filtering for eligibility matching
    """

    def __init__(
        self,
        collection_name: str = "government_schemes",
        host: str = "localhost",
        port: int = 6333,
        vector_size: int = 1024,
        distance: str = "cosine",
        on_disk: bool = True,
        path: Optional[str] = None,
    ):
        """
        Initialize Qdrant vector store

        Args:
            collection_name: Name of the collection
            host: Qdrant host
            port: Qdrant port
            vector_size: Dimension of embeddings (BGE-M3 = 1024)
            distance: Distance metric (cosine, euclid, dot)
            on_disk: Store vectors on disk
            path: Path for local storage (if using embedded mode)
        """
        self.collection_name = collection_name
        self.vector_size = vector_size

        if QdrantClient is None:
            raise ImportError("Qdrant client not installed")

        # Initialize client
        if path:
            # Local embedded mode
            logger.info(f"Initializing Qdrant in embedded mode at {path}")
            self.client = QdrantClient(path=path)
        else:
            # Client-server mode
            logger.info(f"Connecting to Qdrant at {host}:{port}")
            self.client = QdrantClient(host=host, port=port)

        # Map distance metric
        distance_map = {
            "cosine": Distance.COSINE,
            "euclid": Distance.EUCLID,
            "dot": Distance.DOT,
        }
        self.distance = distance_map.get(distance.lower(), Distance.COSINE)

        # Create collection if it doesn't exist
        self._ensure_collection(on_disk)

    def _ensure_collection(self, on_disk: bool = True):
        """Ensure collection exists, create if not"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            logger.info(f"Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=self.distance,
                    on_disk=on_disk,
                ),
            )
            logger.info(f"Collection {self.collection_name} created successfully")
        else:
            logger.info(f"Collection {self.collection_name} already exists")

    def add_documents(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        batch_size: int = 100,
    ) -> List[str]:
        """
        Add documents to the vector store

        Args:
            embeddings: Embedding vectors (n, vector_size)
            metadata: List of metadata dictionaries
            ids: Optional list of IDs (generated if not provided)
            batch_size: Batch size for upload

        Returns:
            List of document IDs
        """
        assert len(embeddings) == len(metadata), "Embeddings and metadata must have same length"

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(embeddings))]

        logger.info(f"Adding {len(embeddings)} documents to {self.collection_name}")

        # Upload in batches
        for i in tqdm(range(0, len(embeddings), batch_size), desc="Uploading to Qdrant"):
            batch_embeddings = embeddings[i:i + batch_size]
            batch_metadata = metadata[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]

            points = []
            for emb, meta, doc_id in zip(batch_embeddings, batch_metadata, batch_ids):
                point = PointStruct(
                    id=doc_id,
                    vector=emb.tolist() if isinstance(emb, np.ndarray) else emb,
                    payload=meta,
                )
                points.append(point)

            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

        logger.info(f"Successfully added {len(embeddings)} documents")
        return ids

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Metadata filters for eligibility
            score_threshold: Minimum similarity score

        Returns:
            List of search results with metadata and scores
        """
        # Convert numpy array to list
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()

        # Build filters
        search_filter = None
        if filters:
            search_filter = self._build_filter(filters)

        # Perform search
        search_params = SearchParams(
            hnsw_ef=128,
            exact=False,
        )

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=search_filter,
            search_params=search_params,
            score_threshold=score_threshold,
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result.id,
                'score': result.score,
                'metadata': result.payload,
            })

        return formatted_results

    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """
        Build Qdrant filter from dictionary

        Args:
            filters: Dictionary of filter conditions

        Returns:
            Qdrant Filter object
        """
        conditions = []

        for key, value in filters.items():
            if isinstance(value, (list, tuple)):
                # Range filter
                if len(value) == 2:
                    conditions.append(
                        FieldCondition(
                            key=key,
                            range=Range(gte=value[0], lte=value[1])
                        )
                    )
            elif isinstance(value, dict):
                # Complex filter (gte, lte, etc.)
                if 'gte' in value or 'lte' in value or 'gt' in value or 'lt' in value:
                    conditions.append(
                        FieldCondition(
                            key=key,
                            range=Range(
                                gte=value.get('gte'),
                                lte=value.get('lte'),
                                gt=value.get('gt'),
                                lt=value.get('lt'),
                            )
                        )
                    )
            else:
                # Exact match
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )

        return Filter(must=conditions) if conditions else None

    def delete_documents(self, ids: List[str]):
        """
        Delete documents by IDs

        Args:
            ids: List of document IDs to delete
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=ids,
        )
        logger.info(f"Deleted {len(ids)} documents")

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        info = self.client.get_collection(self.collection_name)
        return {
            'name': info.config.params.vectors.size,
            'vector_size': info.config.params.vectors.size,
            'distance': info.config.params.vectors.distance,
            'points_count': info.points_count,
        }

    def scroll_all(self, batch_size: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve all documents from collection

        Args:
            batch_size: Batch size for scrolling

        Returns:
            List of all documents with metadata
        """
        all_points = []
        offset = None

        while True:
            results, offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=batch_size,
                offset=offset,
            )

            if not results:
                break

            for point in results:
                all_points.append({
                    'id': point.id,
                    'vector': point.vector,
                    'metadata': point.payload,
                })

            if offset is None:
                break

        return all_points

    def clear_collection(self):
        """Delete all documents in collection"""
        self.client.delete_collection(self.collection_name)
        logger.info(f"Deleted collection: {self.collection_name}")
        self._ensure_collection()
        logger.info(f"Recreated empty collection: {self.collection_name}")


class HybridRetriever:
    """
    Hybrid retriever combining vector search with keyword matching
    """

    def __init__(
        self,
        vector_store: QdrantVectorStore,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ):
        """
        Initialize hybrid retriever

        Args:
            vector_store: Qdrant vector store
            vector_weight: Weight for vector search
            keyword_weight: Weight for keyword matching
        """
        self.vector_store = vector_store
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

    def search(
        self,
        query_vector: np.ndarray,
        query_text: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector and keyword search

        Args:
            query_vector: Query embedding
            query_text: Query text for keyword matching
            top_k: Number of results
            filters: Metadata filters

        Returns:
            List of hybrid search results
        """
        # Vector search
        vector_results = self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k * 2,  # Get more for reranking
            filters=filters,
        )

        # Simple keyword matching (can be enhanced with BM25)
        keywords = set(query_text.lower().split())

        # Score results
        for result in vector_results:
            # Get text content from metadata
            content = result['metadata'].get('content', '').lower()

            # Calculate keyword overlap
            content_words = set(content.split())
            keyword_overlap = len(keywords & content_words) / len(keywords) if keywords else 0

            # Combine scores
            result['vector_score'] = result['score']
            result['keyword_score'] = keyword_overlap
            result['hybrid_score'] = (
                self.vector_weight * result['score'] +
                self.keyword_weight * keyword_overlap
            )

        # Sort by hybrid score
        vector_results.sort(key=lambda x: x['hybrid_score'], reverse=True)

        return vector_results[:top_k]
