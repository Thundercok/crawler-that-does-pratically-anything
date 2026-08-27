"""
rat.engine.reranker — Multi-factor ranking, context snippet extraction, and explainable AI reasoning.
"""

from __future__ import annotations

import datetime
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rat.engine.context_parser import ParsedContext, remove_accents
from rat.engine.llm_client import LLMClient

logger = logging.getLogger("rat.reranker")


def format_relative_time(timestamp: float) -> str:
    """Return friendly relative time string in Vietnamese (e.g. '2 giờ trước', 'Hôm qua')."""
    now = datetime.datetime.now()
    dt = datetime.datetime.fromtimestamp(timestamp)
    diff = now - dt

    if diff.total_seconds() < 60:
        return "Vừa xong"
    elif diff.total_seconds() < 3600:
        mins = int(diff.total_seconds() / 60)
        return f"{mins} phút trước"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} giờ trước"
    elif diff.days == 1:
        return f"Hôm qua, {dt.strftime('%H:%M')}"
    elif diff.days < 7:
        return f"{diff.days} ngày trước"
    elif diff.days < 30:
        weeks = int(diff.days / 7)
        return f"{weeks} tuần trước"
    elif diff.days < 365:
        months = int(diff.days / 30)
        return f"{months} tháng trước"
    else:
        return dt.strftime("%d/%m/%Y")


def format_file_size(size_bytes: int) -> str:
    """Format bytes into readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


class SearchResultItem:
    """Structured search result with context explanation and metadata."""

    def __init__(
        self,
        file_path: str,
        file_name: str,
        file_ext: str,
        file_size: int,
        modified_at: float,
        score: float,
        explanation: str,
        snippet: str,
        version_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.file_path = file_path
        self.file_name = file_name
        self.file_ext = file_ext
        self.file_size = file_size
        self.file_size_formatted = format_file_size(file_size)
        self.modified_at = modified_at
        self.modified_formatted = format_relative_time(modified_at)
        self.score = score
        self.explanation = explanation
        self.snippet = snippet
        self.version_info = version_info

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_ext": self.file_ext,
            "file_size": self.file_size,
            "file_size_formatted": self.file_size_formatted,
            "modified_at": self.modified_at,
            "modified_formatted": self.modified_formatted,
            "score": round(self.score, 2),
            "explanation": self.explanation,
            "snippet": self.snippet,
            "version_info": self.version_info,
        }


class Reranker:
    """Reranker with heuristic scoring and LLM reasoning."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client or LLMClient()

    def extract_best_snippet(
        self,
        content: str,
        keywords: List[str],
        max_length: int = 240
    ) -> str:
        """Extract a representative text snippet containing query keywords."""
        if not content:
            return ""

        content_clean = re.sub(r"\s+", " ", content).strip()
        if not keywords:
            return content_clean[:max_length] + ("..." if len(content_clean) > max_length else "")

        # Find first occurrence of any keyword
        content_norm = remove_accents(content_clean)
        best_pos = -1
        for kw in keywords:
            kw_norm = remove_accents(kw)
            pos = content_norm.find(kw_norm)
            if pos != -1:
                if best_pos == -1 or pos < best_pos:
                    best_pos = pos

        if best_pos == -1:
            return content_clean[:max_length] + ("..." if len(content_clean) > max_length else "")

        start = max(0, best_pos - 60)
        end = min(len(content_clean), start + max_length)
        snippet = content_clean[start:end]

        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(content_clean) else ""
        return prefix + snippet.strip() + suffix

    def compute_heuristic_score(
        self,
        doc: Dict[str, Any],
        context: ParsedContext
    ) -> Tuple[float, List[str]]:
        """
        Compute multi-factor score and reasons why this document matches.
        Prioritizes exact filename matches, file extension alignment, and semantic chunks.
        """
        score = 5.0
        reasons = []

        file_name = doc.get("file_name", "")
        file_ext = doc.get("file_ext", "").lower()
        content = doc.get("content_text", "") or ""
        modified_at = doc.get("modified_at", 0)

        name_norm = remove_accents(file_name).lower()
        content_sample = content[:4000] if len(content) > 4000 else content
        content_norm = remove_accents(content_sample).lower()
        stem_norm = Path(name_norm).stem.lower()

        # 1. Extension match bonus & penalty
        if context.extensions:
            if file_ext in context.extensions:
                score += 35.0
                reasons.append(f"Đúng định dạng {file_ext.upper()}")
            else:
                score -= 30.0

        # 2. Filename keyword & stem matches (Top Priority)
        matched_kws_name = []
        matched_kws_content = []

        for kw in context.keywords:
            kw_norm = remove_accents(kw).lower()
            if not kw_norm:
                continue

            # Exact stem match (e.g. "vietnam" == "vietnam")
            if stem_norm == kw_norm:
                matched_kws_name.append(kw)
                score += 80.0
            elif re.search(r"(?:^|[\s_\.\-])" + re.escape(kw_norm) + r"(?:$|[\s_\.\-])", name_norm):
                matched_kws_name.append(kw)
                score += 55.0
            elif len(kw_norm) >= 4 and kw_norm in name_norm:
                matched_kws_name.append(kw)
                score += 40.0
            elif kw_norm in content_norm:
                matched_kws_content.append(kw)
                score += 15.0

        if matched_kws_name:
            reasons.append(f"Tên file có chứa '{', '.join(matched_kws_name)}'")
        if matched_kws_content:
            reasons.append(f"Nội dung nhắc đến '{', '.join(matched_kws_content)}'")

        # 3. Vector Dense Similarity match bonus
        vector_sim = doc.get("vector_similarity", 0.0)
        if vector_sim > 0.40:
            pct = int(vector_sim * 100)
            score += vector_sim * 35.0
            reasons.append(f"Khớp ngữ nghĩa Vector {pct}%")

        if doc.get("matched_sparse") and not matched_kws_content and not matched_kws_name:
            score += 10.0
            reasons.append("Khớp chỉ mục từ khóa FTS5")

        # 4. Penalty for incidental source code matches when user is searching for documents
        is_code_file = file_ext in [".py", ".js", ".ts", ".html", ".css", ".json", ".sh", ".sql"]
        user_wants_code = any(e in [".py", ".js", ".ts", ".html", ".css", ".json", ".sh", ".sql"] for e in context.extensions)
        if is_code_file and not user_wants_code and not matched_kws_name and len(context.keywords) > 0:
            score -= 25.0

        # 5. Time constraint match / Recency boost
        if context.date_min is not None or context.date_max is not None:
            in_range = True
            if context.date_min is not None and modified_at < context.date_min:
                in_range = False
            if context.date_max is not None and modified_at > context.date_max:
                in_range = False

            if in_range:
                score += 25.0
                reasons.append(f"Khớp mốc thời gian ({context.time_desc})")
            else:
                score -= 15.0
        elif matched_kws_name or matched_kws_content or vector_sim > 0.5:
            # Subtle recency boost for relevant recently modified files
            now = datetime.datetime.now().timestamp()
            days_old = (now - modified_at) / 86400
            if days_old < 3:
                score += 8.0
            elif days_old < 14:
                score += 4.0

        # Clamp score to 0..100
        final_score = max(5.0, min(100.0, score))
        return final_score, reasons

    def rerank(
        self,
        query: str,
        context: ParsedContext,
        candidates: List[Dict[str, Any]],
        top_k: int = 15,
        use_llm: bool = False
    ) -> List[SearchResultItem]:
        """
        Score, filter, and format candidate search results.
        """
        scored_items: List[Tuple[float, Dict[str, Any], List[str], str]] = []

        for doc in candidates:
            score, reasons = self.compute_heuristic_score(doc, context)

            # Prefer the exact matching semantic chunk snippet if available
            if doc.get("best_chunk_text"):
                raw_chunk = doc["best_chunk_text"]
                snippet = raw_chunk[:240] + ("..." if len(raw_chunk) > 240 else "")
            else:
                snippet = self.extract_best_snippet(doc.get("content_text", ""), context.keywords)

            # Generate natural language explanation
            if reasons:
                explanation = " • ".join(reasons)
            else:
                rel_time = format_relative_time(doc.get("modified_at", 0))
                explanation = f"Tệp sửa đổi {rel_time}"

            scored_items.append((score, doc, reasons, snippet))

        # Sort descending by score
        scored_items.sort(key=lambda x: x[0], reverse=True)
        top_items = scored_items[:top_k]

        results = []
        from rat.crawler.dedup import dedup_engine

        for score, doc, reasons, snippet in top_items:
            # Check version tree info for top items
            version_info = None
            try:
                version_info = dedup_engine.get_document_version_info(doc["file_path"])
                if version_info and version_info.get("total_versions", 0) > 1:
                    total_v = version_info["total_versions"]
                    if version_info.get("is_latest"):
                        reasons.insert(0, f"🎯 Bản mới nhất (Có {total_v} bản sửa đổi)")
                    else:
                        reasons.insert(0, f"⚠️ Bản cũ hơn (Bản mới: {version_info.get('latest_file_name')})")
            except Exception:
                pass

            # Build user friendly reason explanation
            reason_text = " • ".join(reasons) if reasons else f"Tệp phù hợp với ngữ cảnh ({doc['file_ext'].upper()})"
            item = SearchResultItem(
                file_path=doc["file_path"],
                file_name=doc["file_name"],
                file_ext=doc["file_ext"],
                file_size=doc["file_size"],
                modified_at=doc["modified_at"],
                score=score,
                explanation=reason_text,
                snippet=snippet,
                version_info=version_info,
            )
            results.append(item)

        return results
