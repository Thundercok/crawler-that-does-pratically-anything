"""
rat.engine.vector_cache — High-speed In-Memory Vector Cache for sub-millisecond retrieval.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

import numpy as np

from rat.config import config
from rat.crawler.db import Database

logger = logging.getLogger("rat.vector_cache")


class VectorCache:
    """
    Maintains all document chunk embeddings in RAM for instant (1ms) vector dot-product search.
    """

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or Database(config.db_path)
        self._matrix: np.ndarray = np.empty((0, 384), dtype=np.float32)
        self._records: List[Dict[str, Any]] = []
        self._is_loaded = False
        self._lock = threading.RLock()

    def preload(self) -> None:
        """Load all chunk vectors from SQLite into contiguous RAM memory."""
        with self._lock:
            t0 = time.time()
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    c.id as chunk_id, c.doc_id, c.file_path, c.chunk_index, c.chunk_text, c.embedding,
                    d.file_name, d.file_ext, d.file_size, d.created_at, d.modified_at
                FROM document_chunks c
                JOIN documents d ON c.doc_id = d.id
                WHERE c.embedding IS NOT NULL
            """)
            rows = cursor.fetchall()

            records = []
            emb_list = []

            for row in rows:
                blob = row["embedding"]
                if not blob:
                    continue
                vec = np.frombuffer(blob, dtype=np.float32)
                emb_list.append(vec)
                records.append({
                    "chunk_id": row["chunk_id"],
                    "doc_id": row["doc_id"],
                    "file_path": row["file_path"],
                    "file_name": row["file_name"],
                    "file_ext": row["file_ext"],
                    "file_size": row["file_size"],
                    "created_at": row["created_at"],
                    "modified_at": row["modified_at"],
                    "chunk_index": row["chunk_index"],
                    "chunk_text": row["chunk_text"],
                })

            if emb_list:
                self._matrix = np.vstack(emb_list)
                self._records = records
                self._is_loaded = True
                logger.info(f"VectorCache preloaded {len(records)} chunks in {time.time()-t0:.3f}s")
            else:
                self._matrix = np.empty((0, 384), dtype=np.float32)
                self._records = []
                self._is_loaded = True

    def search(
        self,
        query_vector: np.ndarray,
        extensions: Optional[List[str]] = None,
        date_min: Optional[float] = None,
        date_max: Optional[float] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Execute instant in-memory Cosine Similarity search (< 1.5ms).
        """
        if not self._is_loaded:
            self.preload()

        with self._lock:
            if self._matrix.size == 0 or len(self._records) == 0 or query_vector.size == 0:
                return []

            # Filter indices by extension and date if specified
            if extensions or date_min is not None or date_max is not None:
                ext_set = set(e.lower() for e in extensions) if extensions else None
                valid_indices = []
                for idx, r in enumerate(self._records):
                    if ext_set and r["file_ext"].lower() not in ext_set:
                        continue
                    if date_min is not None and r["modified_at"] < date_min:
                        continue
                    if date_max is not None and r["modified_at"] > date_max:
                        continue
                    valid_indices.append(idx)

                if not valid_indices:
                    return []

                sub_matrix = self._matrix[valid_indices]
                similarities = np.dot(sub_matrix, query_vector)

                results = []
                for idx_in_sub, global_idx in enumerate(valid_indices):
                    rec = dict(self._records[global_idx])
                    rec["similarity_score"] = float(similarities[idx_in_sub])
                    results.append(rec)
            else:
                # Fast full matrix dot product
                similarities = np.dot(self._matrix, query_vector)
                results = []
                for idx, sim in enumerate(similarities):
                    rec = dict(self._records[idx])
                    rec["similarity_score"] = float(sim)
                    results.append(rec)

            # Sort descending by similarity
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:limit]


# Global singleton instance
vector_cache = VectorCache()
