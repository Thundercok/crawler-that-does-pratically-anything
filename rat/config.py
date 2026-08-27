"""
rat.config — Configuration management for rat assistant.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

# Default Paths
HOME_DIR = Path.home()
RAT_DIR = HOME_DIR / ".rat"
RAT_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = RAT_DIR / "config.json"
DEFAULT_DB_PATH = RAT_DIR / "rat_index.db"

# Default directories to watch & index
DEFAULT_WATCH_DIRS = [
    str(HOME_DIR / "Downloads"),
    str(HOME_DIR / "Documents"),
    str(HOME_DIR / "Desktop"),
]

# Supported Extensions
SUPPORTED_EXTENSIONS = {
    # Documents
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".csv", ".rtf",
    # Plain text & Notes
    ".txt", ".md", ".markdown", ".rst",
    # Code & Configs
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json", ".yaml", ".yml",
    ".toml", ".sh", ".sql", ".xml", ".log", ".csv",
    # Images (Metadata & OCR)
    ".jpg", ".jpeg", ".png", ".webp"
}

# Directories to always ignore
IGNORE_DIRS = {
    ".git", ".svn", ".hg", "node_modules", ".venv", "venv", "env",
    "__pycache__", ".pytest_cache", ".cargo", "target", "build", "dist",
    "Library", "Applications", ".Trash", ".cache", ".local", "RAWs",
    "Photos", "Photos Library.photoslibrary", "Movies", "Music", "Podcasts",
    ".npm", ".cargo", ".rustup", "Pods"
}

# Ignore file patterns
IGNORE_PATTERNS = {
    ".DS_Store", "Thumbs.db", "desktop.ini", "*.tmp", "*.swp", "~$*", "*.pyc"
}

MAX_FILE_SIZE_BYTES = 30 * 1024 * 1024  # 30 MB limit for deep text extraction



class Config:
    def __init__(self) -> None:
        self.db_path: str = str(DEFAULT_DB_PATH)
        self.indexed_directories: List[str] = [
            d for d in DEFAULT_WATCH_DIRS if os.path.exists(d)
        ]
        # Include current project and downloads folder if available
        custom_paths = [
            "/Users/thundercock2/Downloads/drive-download-20260721T070924Z-1-001",
            "/Users/thundercock2/Documents/Github/Spider-The-Web-Crawler",
        ]
        for p in custom_paths:
            if os.path.exists(p) and p not in self.indexed_directories:
                self.indexed_directories.append(p)

        self.llm_provider: str = "auto"  # "auto", "slm", "gemini", "openai", "ollama", "offline"
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model: str = "qwen2.5:1.5b"
        self.use_slm: bool = True
        self.auto_watch: bool = True
        self.max_results: int = 15
        self.load()

    def load(self) -> None:
        """Load settings from config.json if exists."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data: Dict[str, Any] = json.load(f)
                    if "indexed_directories" in data:
                        self.indexed_directories = data["indexed_directories"]
                    if "llm_provider" in data:
                        self.llm_provider = data["llm_provider"]
                    if "gemini_api_key" in data and data["gemini_api_key"]:
                        self.gemini_api_key = data["gemini_api_key"]
                    if "openai_api_key" in data and data["openai_api_key"]:
                        self.openai_api_key = data["openai_api_key"]
                    if "ollama_url" in data:
                        self.ollama_url = data["ollama_url"]
                    if "ollama_model" in data:
                        self.ollama_model = data["ollama_model"]
                    if "auto_watch" in data:
                        self.auto_watch = data["auto_watch"]
                    if "max_results" in data:
                        self.max_results = data["max_results"]
            except Exception:
                pass

    def save(self) -> None:
        """Save settings to config.json."""
        data = {
            "indexed_directories": self.indexed_directories,
            "llm_provider": self.llm_provider,
            "gemini_api_key": self.gemini_api_key,
            "openai_api_key": self.openai_api_key,
            "ollama_url": self.ollama_url,
            "ollama_model": self.ollama_model,
            "auto_watch": self.auto_watch,
            "max_results": self.max_results,
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Global singleton instance
config = Config()
