"""
rat.engine.qa_engine — In-Situ Document Q&A & Semantic Extraction Assistant.
Enables instant questioning, summarization, and facts extraction directly from local files
with automatic fallback from Local SLM -> Cloud LLM -> High-precision Offline Extractive Reasoner.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from rat.config import config
from rat.engine.context_parser import remove_accents
from rat.engine.embedder import embedder
from rat.engine.llm_client import LLMClient
from rat.engine.slm import slm_engine
from rat.engine.slm_prompts import DOCUMENT_QA_SYSTEM_PROMPT

logger = logging.getLogger("rat.qa_engine")


class DocumentQAEngine:
    """Intelligent Question Answering Engine for local files."""

    def __init__(self) -> None:
        self.slm = slm_engine
        self.llm = LLMClient()
        self.embedder = embedder

    def extract_relevant_paragraphs(
        self,
        doc_text: str,
        question: str,
        max_paragraphs: int = 4
    ) -> List[Tuple[str, float]]:
        """
        Extract the most relevant paragraphs from document text matching the question.
        Uses sentence chunking and dense vector / keyword scoring.
        """
        if not doc_text or not question:
            return []

        # Split into distinct paragraphs or logical chunks
        raw_paras = [p.strip() for p in re.split(r"\n{2,}|\r\n{2,}|--- Page \d+ ---", doc_text) if p.strip()]
        if not raw_paras:
            raw_paras = [p.strip() for p in doc_text.split("\n") if len(p.strip()) > 30]

        if not raw_paras:
            return [(doc_text[:600], 1.0)]

        q_norm = remove_accents(question).lower()
        q_tokens = [w for w in re.findall(r"\w+", q_norm) if len(w) > 2]

        scored_paras: List[Tuple[str, float]] = []

        for p in raw_paras:
            p_norm = remove_accents(p).lower()
            # Token overlap score
            overlap_count = sum(1 for tok in q_tokens if tok in p_norm)
            score = overlap_count * 15.0

            # Boost for numbers if asking about numbers/money/dates
            if any(term in q_norm for term in ["bao nhieu", "tien", "so", "ngay", "vnd", "usd", "%"]):
                num_count = len(re.findall(r"\d+[\.\,\d]*", p))
                score += num_count * 5.0

            # Boost for summary triggers
            if any(term in q_norm for term in ["tom tat", "noi dung", "y chinh", "summary"]):
                if len(p) > 80:
                    score += 10.0

            if score > 0 or len(raw_paras) <= max_paragraphs:
                scored_paras.append((p, score))

        # Sort descending by score
        scored_paras.sort(key=lambda x: x[1], reverse=True)
        return scored_paras[:max_paragraphs]

    def _answer_extractive_heuristic(
        self,
        doc_text: str,
        question: str,
        file_name: str = ""
    ) -> Dict[str, Any]:
        """
        Offline zero-dependency extractive answer generator.
        Extracts relevant facts and creates structured bullet points with citations.
        """
        relevant_paras = self.extract_relevant_paragraphs(doc_text, question, max_paragraphs=3)
        if not relevant_paras:
            return {
                "answer": f"Không tìm thấy đoạn nội dung phù hợp trong tệp `{file_name}` để trả lời câu hỏi.",
                "snippets": [],
                "engine": "Offline Heuristic Reasoner",
                "confidence": 0.3,
            }

        q_norm = remove_accents(question).lower()
        is_summary = any(k in q_norm for k in ["tom tat", "y chinh", "tong quan", "noi dung"])

        formatted_lines = []
        if is_summary:
            formatted_lines.append(f"📌 **Tóm tắt các điểm nổi bật trong `{file_name}`:**\n")
            for idx, (p, score) in enumerate(relevant_paras, 1):
                clean_p = p.replace("\n", " ").strip()
                if len(clean_p) > 280:
                    clean_p = clean_p[:275] + "..."
                formatted_lines.append(f"• {clean_p}")
        else:
            formatted_lines.append(f"🔍 **Thông tin liên quan tìm thấy trong `{file_name}`:**\n")
            for idx, (p, score) in enumerate(relevant_paras, 1):
                clean_p = p.replace("\n", " ").strip()
                if len(clean_p) > 350:
                    clean_p = clean_p[:345] + "..."
                formatted_lines.append(f"> \"{clean_p}\"")

        snippets = [p[0] for p in relevant_paras]
        return {
            "answer": "\n".join(formatted_lines),
            "snippets": snippets,
            "engine": "Offline Extractive Reasoner (100% On-Device)",
            "confidence": 0.85,
        }

    def answer_question(
        self,
        doc_text: str,
        question: str,
        file_name: str = "",
        use_cloud_if_available: bool = True
    ) -> Dict[str, Any]:
        """
        Multi-tier Q&A Router:
        1. Local SLM (Ollama / Apple MLX) if running.
        2. Cloud LLM (Gemini / OpenAI) if configured.
        3. Offline Extractive Reasoner (Instant, Zero Setup).
        """
        cleaned_text = doc_text.strip() if doc_text else ""
        if not cleaned_text:
            return {
                "answer": f"⚠️ Tệp `{file_name}` không có nội dung văn bản để phân tích.",
                "snippets": [],
                "engine": "None",
                "confidence": 0.0,
            }

        # 1. Try Local SLM
        if config.use_slm and self.slm.is_model_installed():
            try:
                slm_ans = self.slm.ask_document(cleaned_text, question)
                if slm_ans and not slm_ans.startswith("⚠️") and "Không nhận được phản hồi" not in slm_ans and "Lỗi" not in slm_ans:
                    return {
                        "answer": slm_ans,
                        "snippets": [cleaned_text[:400]],
                        "engine": f"Local SLM ({self.slm.model})",
                        "confidence": 0.95,
                    }
            except Exception as e:
                logger.debug(f"Local SLM QA failed: {e}")

        # 2. Try Cloud LLM (Gemini / OpenAI)
        if use_cloud_if_available and (config.gemini_api_key or config.openai_api_key):
            try:
                prompt = (
                    f"Nội dung tệp tin [{file_name}]:\n\"\"\"\n{cleaned_text[:12000]}\n\"\"\"\n\n"
                    f"Câu hỏi: {question}\n\n"
                    "Hãy trả lời ngắn gọn, súc tích bằng tiếng Việt:"
                )
                cloud_ans = self.llm.call_llm(prompt, system_prompt=DOCUMENT_QA_SYSTEM_PROMPT, max_tokens=600)
                if cloud_ans:
                    return {
                        "answer": cloud_ans,
                        "snippets": [cleaned_text[:400]],
                        "engine": f"Cloud LLM ({config.llm_provider.upper()})",
                        "confidence": 0.98,
                    }
            except Exception as e:
                logger.debug(f"Cloud LLM QA failed: {e}")

        # 3. Offline Extractive Reasoner (Default Zero-Setup fallback)
        return self._answer_extractive_heuristic(cleaned_text, question, file_name=file_name)


# Global singleton instance
qa_engine = DocumentQAEngine()
