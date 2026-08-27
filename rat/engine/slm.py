"""
rat.engine.slm — Small Language Model (SLM) on-device engine for local inference.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple

from rat.config import config
from rat.engine.slm_prompts import (
    DECONSTRUCT_QUERY_SYSTEM_PROMPT,
    DOCUMENT_QA_SYSTEM_PROMPT,
    RERANKER_SYSTEM_PROMPT,
)

logger = logging.getLogger("rat.slm")

DEFAULT_SLM_MODEL = "qwen2.5:1.5b"


class SLMEngine:
    """Manager for local Small Language Models running on Apple Silicon / GPU."""

    def __init__(self, ollama_url: Optional[str] = None, model: Optional[str] = None) -> None:
        self.ollama_url = (ollama_url or config.ollama_url or "http://localhost:11434").rstrip("/")
        self.model = model or config.ollama_model or DEFAULT_SLM_MODEL
        self._available_models_cache: List[str] = []

    def is_service_running(self) -> bool:
        """Check if local Ollama daemon is reachable."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as response:
                return response.status == 200
        except Exception:
            return False

    def list_installed_models(self) -> List[str]:
        """Fetch list of local model names installed in Ollama."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2.0) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                self._available_models_cache = models
                return models
        except Exception as e:
            logger.debug(f"Failed to list local SLMs: {e}")
            return []

    def is_model_installed(self, model_name: Optional[str] = None) -> bool:
        """Check if target model (e.g. qwen2.5:1.5b) is downloaded."""
        target = (model_name or self.model).lower()
        installed = self.list_installed_models()
        return any(target in m.lower() or m.lower().startswith(target) for m in installed)

    def pull_model(
        self,
        model_name: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> bool:
        """Download model from Ollama library with streaming progress."""
        url = f"{self.ollama_url}/api/pull"
        payload = {"name": model_name, "stream": True}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as response:
                for line in response:
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        status = chunk.get("status", "")
                        total = chunk.get("total", 0)
                        completed = chunk.get("completed", 0)
                        if progress_callback:
                            progress_callback(status, completed, total)
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_format: bool = False,
        timeout: float = 25.0
    ) -> Optional[str]:
        """Send prompt to local SLM and receive completion."""
        url = f"{self.ollama_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 512,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
        if json_format:
            payload["format"] = "json"

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                res = json.loads(response.read().decode("utf-8"))
                return res.get("response", "").strip()
        except Exception as e:
            logger.debug(f"SLM generate call failed ({self.model}): {e}")
            return None

    def deconstruct_query(self, raw_query: str) -> Optional[Dict[str, Any]]:
        """
        Use SLM to deconstruct a messy query into structured search criteria & expanded synonyms.
        """
        if not self.is_model_installed():
            return None

        prompt = f"Phân tích câu tìm kiếm sau:\n\"{raw_query}\""
        try:
            response = self.generate(
                prompt=prompt,
                system_prompt=DECONSTRUCT_QUERY_SYSTEM_PROMPT,
                json_format=True,
                timeout=10.0,
            )
            if response:
                # Clean any markdown block if present
                clean_json = re.sub(r"^```json\s*", "", response, flags=re.MULTILINE)
                clean_json = re.sub(r"```$", "", clean_json, flags=re.MULTILINE).strip()
                data = json.loads(clean_json)
                if isinstance(data, dict):
                    # Ensure all extensions have leading dot
                    raw_exts = data.get("file_extensions", [])
                    data["file_extensions"] = [
                        (e if e.startswith(".") else f".{e}").lower()
                        for e in raw_exts if isinstance(e, str)
                    ]
                    return data
        except Exception as e:
            logger.debug(f"SLM query deconstruction error: {e}")
        return None

    def ask_document(self, document_text: str, question: str) -> str:
        """
        Instant Q&A / Summarization on selected document.
        """
        if not self.is_model_installed():
            return "⚠️ SLM chưa được kích hoạt hoặc chưa tải model. Vui lòng vào Cài đặt để tải model."

        truncated_text = document_text[:8000]  # Send up to 8k chars
        prompt = f"Nội dung tài liệu:\n\"\"\"\n{truncated_text}\n\"\"\"\n\nCâu hỏi của người dùng: {question}\n\nHãy trả lời bằng tiếng Việt ngắn gọn, rõ ràng:"
        try:
            ans = self.generate(
                prompt=prompt,
                system_prompt=DOCUMENT_QA_SYSTEM_PROMPT,
                json_format=False,
                timeout=25.0,
            )
            return ans or "Không nhận được phản hồi từ SLM."
        except Exception as e:
            return f"Lỗi hỏi đáp SLM: {e}"


# Global singleton instance
slm_engine = SLMEngine()
