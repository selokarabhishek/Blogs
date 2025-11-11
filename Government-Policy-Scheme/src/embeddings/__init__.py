"""
Embeddings Module
Handles BGE-M3 embedding generation and management.
"""

from .bge_embedder import BGEEmbedder, HybridEmbedder

__all__ = [
    'BGEEmbedder',
    'HybridEmbedder',
]
