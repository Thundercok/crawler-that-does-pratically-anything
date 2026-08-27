"""
rat.crawler.provenance — macOS File Provenance & Download Origin Extractor.
Extracts source URLs, originating domains, and downloading applications (Safari, Chrome, Telegram, Slack, etc.)
from macOS extended attributes (xattr).
"""

from __future__ import annotations

import logging
import os
import platform
import plistlib
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger("rat.provenance")


class FileProvenanceExtractor:
    """Extracts origin metadata (where from URL, download application) for macOS files."""

    @staticmethod
    def extract_where_froms(file_path: str) -> List[str]:
        """Extract source URLs from 'com.apple.metadata:kMDItemWhereFroms'."""
        if platform.system() != "Darwin" or not os.path.exists(file_path):
            return []

        try:
            res = subprocess.run(
                ["xattr", "-px", "com.apple.metadata:kMDItemWhereFroms", file_path],
                capture_output=True,
                timeout=1.5
            )
            if res.returncode == 0 and res.stdout:
                hex_data = res.stdout.decode("ascii", errors="ignore").replace(" ", "").replace("\n", "")
                if hex_data:
                    raw_bytes = bytes.fromhex(hex_data)
                    parsed = plistlib.loads(raw_bytes)
                    if isinstance(parsed, list):
                        return [str(u).strip() for u in parsed if str(u).strip()]
                    elif isinstance(parsed, str):
                        return [parsed.strip()]
        except Exception as e:
            logger.debug(f"Failed to extract where_froms for {file_path}: {e}")

        return []

    @staticmethod
    def extract_quarantine_app(file_path: str) -> Optional[str]:
        """Extract downloading application name (Safari, Chrome, Telegram, etc.) from quarantine attribute."""
        if platform.system() != "Darwin" or not os.path.exists(file_path):
            return None

        try:
            res = subprocess.run(
                ["xattr", "-p", "com.apple.quarantine", file_path],
                capture_output=True,
                text=True,
                errors="ignore",
                timeout=1.5
            )
            if res.returncode == 0 and res.stdout:
                parts = res.stdout.strip().split(";")
                if len(parts) >= 3 and parts[2].strip():
                    return parts[2].strip()
        except Exception as e:
            logger.debug(f"Failed to extract quarantine app for {file_path}: {e}")

        return None

    @classmethod
    def get_provenance(cls, file_path: str) -> Dict[str, Any]:
        """
        Extract full provenance metadata for a file.
        Returns:
            {
                "source_urls": [...],
                "source_domains": ["docs.google.com", "github.com"],
                "source_app": "Safari" | "Google Chrome" | "Telegram" | ...,
                "provenance_text": "...searchable summary string..."
            }
        """
        urls = cls.extract_where_froms(file_path)
        app = cls.extract_quarantine_app(file_path)

        domains: List[str] = []
        for u in urls:
            try:
                parsed_url = urlparse(u)
                netloc = parsed_url.netloc.lower()
                # Remove port if present
                if ":" in netloc:
                    netloc = netloc.split(":")[0]
                if netloc and netloc not in domains:
                    domains.append(netloc)
            except Exception:
                continue

        # Build clean searchable text snippet
        provenance_parts = []
        if app:
            provenance_parts.append(f"Tải qua ứng dụng / Ứng dụng tạo: {app}")
        if domains:
            provenance_parts.append(f"Tải từ trang web / Nguồn: {', '.join(domains)}")

        provenance_text = " | ".join(provenance_parts) if provenance_parts else ""

        return {
            "source_urls": urls,
            "source_domains": domains,
            "source_app": app or "",
            "provenance_text": provenance_text,
        }


# Global singleton instance
provenance_extractor = FileProvenanceExtractor()
