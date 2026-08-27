"""
rat.engine.hybrid_search — Hybrid Search Coordinator combining FTS5, Metadata, and Context Engineering.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from rat.config import config
from rat.crawler.db import Database
from rat.engine.context_engine import context_engine
from rat.engine.context_parser import ContextParser, ParsedContext
from rat.engine.embedder import embedder
from rat.engine.hyde import hyde_engine
from rat.engine.llm_client import LLMClient
from rat.engine.reranker import Reranker, SearchResultItem
from rat.engine.rrf import rrf_fuser
from rat.engine.slm import slm_engine
from rat.engine.vector_cache import VectorCache, vector_cache

logger = logging.getLogger("rat.search")


class SearchEngine:
    """End-to-end intelligent search engine combining Sparse FTS5, Dense Vectors, HyDE, and RRF."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or Database(config.db_path)
        self.llm = LLMClient()
        self.slm = slm_engine
        self.embedder = embedder
        self.hyde = hyde_engine
        self.rrf = rrf_fuser
        self.reranker = Reranker(self.llm)
        self.vector_cache = vector_cache if db is None else VectorCache(self.db)
        self.context_engine = context_engine

    def search(
        self,
        query: str,
        limit: int = 15,
        use_hyde: bool = True,
        use_vector: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute deep natural language context search with Concept Expansion, HyDE & Hybrid RRF.
        """
        start_t = time.time()
        clean_q = query.strip()
        enriched = self.context_engine.enrich_query(clean_q)
        context = enriched.base_context

        # 1. HyDE / Contextual Vector Embedding
        hypo_text = None
        multi_queries = [clean_q]
        query_vector = None

        should_use_hyde = use_hyde and config.use_slm and len(clean_q.split()) >= 4

        if use_vector and len(clean_q) > 0:
            if should_use_hyde:
                query_vector, hypo_text, multi_queries = self.hyde.get_hyde_query_vector(clean_q)
            else:
                # Embed the enriched semantic text (includes conceptual synonyms)
                query_vector = self.embedder.embed_query(enriched.semantic_query_text)

        # 2. Sparse Search across Base & Expanded Concept Keywords
        all_keywords = list(enriched.expanded_keywords)
        for mq in multi_queries:
            mq_ctx = ContextParser.parse_query(mq)
            for kw in mq_ctx.keywords:
                if kw not in all_keywords:
                    all_keywords.append(kw)

        # Use explicitly provided extensions or recommended concept extensions
        search_exts = context.extensions if context.extensions else (enriched.recommended_extensions if enriched.matched_concepts else None)
        excluded_exts = context.excluded_extensions if context.excluded_extensions else None

        sparse_candidates = self.db.search_candidates(
            keywords=all_keywords,
            extensions=search_exts,
            excluded_extensions=excluded_exts,
            date_min=context.date_min,
            date_max=context.date_max,
            limit=45
        )

        # 3. Dense Vector Search (Cosine Similarity over RAM matrix)
        dense_chunk_candidates: List[Dict[str, Any]] = []
        if use_vector and query_vector is not None and query_vector.size > 0:
            dense_chunk_candidates = self.vector_cache.search(
                query_vector=query_vector,
                extensions=search_exts,
                excluded_extensions=excluded_exts,
                date_min=context.date_min,
                date_max=context.date_max,
                limit=45
            )

        # 4. Reciprocal Rank Fusion (RRF)
        if dense_chunk_candidates:
            fused_candidates = self.rrf.fuse(
                sparse_candidates=sparse_candidates,
                dense_chunk_candidates=dense_chunk_candidates,
                top_k=limit * 2
            )
        else:
            fused_candidates = sparse_candidates

        # 5. Context Reranking & Explanation Synthesis
        results = self.reranker.rerank(
            query=query,
            context=context,
            candidates=fused_candidates,
            top_k=limit,
            use_llm=False
        )

        latency_ms = round((time.time() - start_t) * 1000.0, 1)

        return {
            "query": query,
            "results": results,
            "latency_ms": latency_ms,
            "parsed_context": context.to_dict(),
            "ai_intent_summary": enriched.ai_intent_summary,
            "matched_concepts": enriched.matched_concepts,
            "expanded_keywords": enriched.expanded_keywords,
            "hyde_passage": hypo_text,
            "total_candidates": len(fused_candidates),
            "sparse_count": len(sparse_candidates),
            "dense_count": len(dense_chunk_candidates),
        }
