"""
rat.engine.embedder — High performance local dense vector embedder.
"""

from __future__ import annotations

import logging
import time
import threading
from typing import List, Optional, Union

import numpy as np

logger = logging.getLogger("rat.embedder")

DEFAULT_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class LocalEmbedder:
    """Local embedding generator using FastEmbed ONNX runtime."""

    def __init__(self, model_name: str = DEFAULT_EMBED_MODEL) -> None:
        self.model_name = model_name
        self._model = None
        self._dimension: int = 384
        self._lock = threading.Lock()
        self._query_cache: dict[str, np.ndarray] = {}
        self._cache_lock = threading.Lock()
        self._cache_maxsize: int = 512
        self._last_accessed: float = 0.0

    @property
    def is_loaded(self) -> bool:
        """Return True if model is currently resident in RAM."""
        return self._model is not None

    @property
    def last_accessed(self) -> float:
        """Return unix timestamp of last embedding operation."""
        return self._last_accessed

    def evict(self) -> bool:
        """
        Evict the embedding model and ONNX runtime session from RAM.
        Frees ~250MB - 350MB when memory pressure occurs or system goes to sleep.
        Returns True if model was unloaded, False if it was already cold.
        """
        with self._lock:
            if self._model is not None:
                logger.info(f"Evicting LocalEmbedder ({self.model_name}) from RAM due to memory governance.")
                del self._model
                self._model = None
                with self._cache_lock:
                    self._query_cache.clear()
                import gc
                gc.collect()
                return True
            return False

    def _load_model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from fastembed import TextEmbedding
                        logger.info(f"Loading local embedding model: {self.model_name}")
                        self._model = TextEmbedding(model_name=self.model_name)
                        # Determine dimension with a dummy embedding
                        dummy = list(self._model.embed(["test"]))[0]
                        self._dimension = len(dummy)
                    except Exception as e:
                        logger.error(f"Failed to initialize FastEmbed: {e}")
                        self._model = None
        self._last_accessed = time.time()
        return self._model

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate L2-normalized dense embeddings for a list of text strings.
        Returns: 2D numpy array of shape (N, dim).
        """
        if not texts:
            return np.empty((0, self._dimension), dtype=np.float32)

        model = self._load_model()
        if model is None:
            # Fallback random normalized vectors if model fails to load
            vecs = np.random.randn(len(texts), self._dimension).astype(np.float32)
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            return vecs / np.maximum(norms, 1e-12)

        try:
            embeddings_gen = model.embed(texts, batch_size=batch_size)
            vec_list = [np.array(vec, dtype=np.float32) for vec in embeddings_gen]
            matrix = np.vstack(vec_list)

            # Ensure vectors are unit L2-normalized for pure dot-product cosine similarity
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            return matrix / np.maximum(norms, 1e-12)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return np.zeros((len(texts), self._dimension), dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate normalized 1D vector embedding for a search query with caching.
        Returns: 1D numpy array of shape (dim,).
        """
        clean_q = query.strip()
        if not clean_q:
            return np.zeros(self._dimension, dtype=np.float32)

        with self._cache_lock:
            if clean_q in self._query_cache:
                self._last_accessed = time.time()
                return self._query_cache[clean_q].copy()

        matrix = self.embed_texts([clean_q])
        res = matrix[0] if len(matrix) > 0 else np.zeros(self._dimension, dtype=np.float32)

        with self._cache_lock:
            if len(self._query_cache) >= self._cache_maxsize:
                oldest_key = next(iter(self._query_cache))
                del self._query_cache[oldest_key]
            self._query_cache[clean_q] = res

        return res.copy()

    @staticmethod
    def compute_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """
        Compute Cosine Similarity between 1D query vector and 2D matrix of chunk vectors.
        Since vectors are L2 normalized, cosine similarity is simply the dot product.
        """
        if matrix.size == 0 or query_vec.size == 0:
            return np.array([], dtype=np.float32)
        # Dot product
        return np.dot(matrix, query_vec)


# Global singleton instance
embedder = LocalEmbedder()
