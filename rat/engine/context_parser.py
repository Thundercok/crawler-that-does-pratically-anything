"""
rat.engine.context_parser — Natural Language context & intent parser for non-tech users.
"""

from __future__ import annotations

import datetime
import re
import unicodedata
from typing import Any, Dict, List, Optional, Set, Tuple


def remove_accents(text: str) -> str:
    """Normalize and strip Vietnamese diacritics."""
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "D")
    return text.lower()


# Stopwords in normalized unaccented form
STOPWORDS: Set[str] = {
    # Vietnamese
    "tim", "kiem", "cho", "toi", "tao", "minh", "ban", "gium", "ho", "cai", "con",
    "file", "tep", "tai", "lieu", "van", "ban", "nay", "do", "no", "kia", "nao",
    "o", "dau", "trong", "may", "tinh", "voi", "co", "chua", "nhac", "den", "ve",
    "nhe", "nha", "a", "oi", "xem", "lai", "duoc", "khong", "moi", "cu", "vua",
    "bai", "tap", "chu", "de", "muc", "noi", "dung", "va", "cua", "su", "cac",
    "nhung", "mot", "la", "thi", "ma", "nhu", "ra", "vao", "theo",
    # English
    "find", "search", "get", "show", "me", "the", "a", "an", "file", "document",
    "files", "documents", "that", "which", "has", "contains", "about", "from",
    "where", "is", "in", "on", "please", "can", "you", "my", "of", "for", "with"
}

# Type mappings
TYPE_PATTERNS: Dict[str, List[str]] = {
    # Word
    r"\b(word|docx?|van ban|soan thao|bai tap)\b": [".docx", ".doc"],
    # PDF
    r"\b(pdf|scan|sach|giao trinh|ebook)\b": [".pdf"],
    # Excel / Spreadsheet
    r"\b(excel|xlsx?|csv|bang tinh|bang luong|thu chi|ke toan|tinh tien|so sach)\b": [".xlsx", ".xls", ".csv"],
    # PowerPoint
    r"\b(powerpoint|pptx?|slide|thuyet trinh|bai giang|presentation)\b": [".pptx", ".ppt"],
    # Image
    r"\b(hinh anh|anh|hinh|photo|image|picture|png|jpe?g|webp|screenshot|chup man hinh|cap man hinh|buc anh)\b": [".png", ".jpg", ".jpeg", ".webp"],
    # Code
    r"\b(code|ma nguon|python|script|py|javascript|js|typescript|ts|html|css|json|sql|sh)\b": [
        ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json", ".yaml", ".yml", ".sh", ".sql"
    ],
    # Text / Notes
    r"\b(note|ghi chu|txt|markdown|md)\b": [".txt", ".md"]
}


class ParsedContext:
    """Represents the structured interpretation of a messy natural language query."""

    def __init__(
        self,
        raw_query: str,
        keywords: List[str],
        extensions: Optional[List[str]] = None,
        date_min: Optional[float] = None,
        date_max: Optional[float] = None,
        time_desc: Optional[str] = None,
        file_type_desc: Optional[str] = None,
    ) -> None:
        self.raw_query = raw_query
        self.keywords = keywords
        self.extensions = extensions or []
        self.date_min = date_min
        self.date_max = date_max
        self.time_desc = time_desc
        self.file_type_desc = file_type_desc

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_query": self.raw_query,
            "keywords": self.keywords,
            "extensions": self.extensions,
            "date_min": self.date_min,
            "date_max": self.date_max,
            "time_desc": self.time_desc,
            "file_type_desc": self.file_type_desc,
        }


class ContextParser:
    """Extracts search constraints and intent from natural language queries."""

    @staticmethod
    def parse_temporal_context(query: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """
        Detect temporal expressions and return (date_min, date_max, description).
        """
        now = datetime.datetime.now()
        today_start = datetime.datetime(now.year, now.month, now.day)
        today_end = today_start + datetime.timedelta(days=1, microseconds=-1)

        q_norm = remove_accents(query)

        # "hôm nay", "today"
        if re.search(r"\b(hom nay|today|ngay hom nay)\b", q_norm):
            return today_start.timestamp(), today_end.timestamp(), "Hôm nay"

        # "hôm qua", "yesterday"
        if re.search(r"\b(hom qua|yesterday|ngay hom qua)\b", q_norm):
            y_start = today_start - datetime.timedelta(days=1)
            y_end = today_start - datetime.timedelta(microseconds=1)
            return y_start.timestamp(), y_end.timestamp(), "Hôm qua"

        # "hôm kia", "ngay hom kia"
        if re.search(r"\b(hom kia|ngay hom kia)\b", q_norm):
            yk_start = today_start - datetime.timedelta(days=2)
            yk_end = today_start - datetime.timedelta(days=1, microseconds=1)
            return yk_start.timestamp(), yk_end.timestamp(), "Hôm kia"

        # "N ngày trước" / "N ngay qua"
        days_match = re.search(r"(\d+)\s*(ngay|day)s?\s*(truoc|qua|ago|recent)", q_norm)
        if days_match:
            n_days = int(days_match.group(1))
            start = now - datetime.timedelta(days=n_days)
            return start.timestamp(), now.timestamp(), f"{n_days} ngày gần đây"

        # "tuần này", "this week"
        if re.search(r"\b(tuan nay|this week)\b", q_norm):
            start_of_week = today_start - datetime.timedelta(days=now.weekday())
            return start_of_week.timestamp(), now.timestamp(), "Tuần này"

        # "tuần trước", "last week"
        if re.search(r"\b(tuan truoc|last week)\b", q_norm):
            start_of_current_week = today_start - datetime.timedelta(days=now.weekday())
            start_of_last_week = start_of_current_week - datetime.timedelta(days=7)
            end_of_last_week = start_of_current_week - datetime.timedelta(microseconds=1)
            return start_of_last_week.timestamp(), end_of_last_week.timestamp(), "Tuần trước"

        # "tháng này", "this month"
        if re.search(r"\b(thang nay|this month)\b", q_norm):
            start_of_month = datetime.datetime(now.year, now.month, 1)
            return start_of_month.timestamp(), now.timestamp(), "Tháng này"

        # "tháng trước", "last month"
        if re.search(r"\b(thang truoc|last month)\b", q_norm):
            first_day_current_month = datetime.datetime(now.year, now.month, 1)
            last_day_prev_month = first_day_current_month - datetime.timedelta(days=1)
            start_of_prev_month = datetime.datetime(last_day_prev_month.year, last_day_prev_month.month, 1)
            return start_of_prev_month.timestamp(), first_day_current_month.timestamp(), "Tháng trước"

        # Specific month: "tháng 7", "thang 7", "thang 12"
        month_match = re.search(r"\b(thang|month)\s*(\d{1,2})\b", q_norm)
        if month_match:
            month_num = int(month_match.group(2))
            if 1 <= month_num <= 12:
                # Default to current year if month is <= current month, otherwise last year
                target_year = now.year if month_num <= now.month else now.year - 1
                start_dt = datetime.datetime(target_year, month_num, 1)
                if month_num == 12:
                    end_dt = datetime.datetime(target_year + 1, 1, 1)
                else:
                    end_dt = datetime.datetime(target_year, month_num + 1, 1)
                return start_dt.timestamp(), end_dt.timestamp(), f"Tháng {month_num}/{target_year}"

        # "mới đây", "gần đây", "recently"
        if re.search(r"\b(moi day|gan day|moi sua|moi tai|recently|recent)\b", q_norm):
            recent_start = now - datetime.timedelta(days=7)
            return recent_start.timestamp(), now.timestamp(), "Gần đây (7 ngày)"

        return None, None, None

    @staticmethod
    def parse_file_types(query: str) -> Tuple[List[str], Optional[str]]:
        """Detect intended file types."""
        q_norm = remove_accents(query)
        detected_extensions: List[str] = []
        detected_descriptions: List[str] = []

        for pattern, exts in TYPE_PATTERNS.items():
            if re.search(pattern, q_norm):
                for e in exts:
                    if e not in detected_extensions:
                        detected_extensions.append(e)
                desc = exts[0].replace(".", "").upper()
                if desc not in detected_descriptions:
                    detected_descriptions.append(desc)

        desc_str = ", ".join(detected_descriptions) if detected_descriptions else None
        return detected_extensions, desc_str

    @classmethod
    def parse_query(cls, raw_query: str) -> ParsedContext:
        """Parse natural language query into structured context constraints & keywords."""
        cleaned_raw = raw_query.strip()
        if not cleaned_raw:
            return ParsedContext(raw_query="", keywords=[])

        date_min, date_max, time_desc = cls.parse_temporal_context(cleaned_raw)
        extensions, type_desc = cls.parse_file_types(cleaned_raw)

        # Extract core keywords by removing temporal words, type words, and stopwords
        q_norm = remove_accents(cleaned_raw)

        # Tokenize by non-alphanumeric
        tokens = re.findall(r"[\w\.\-]+", cleaned_raw)
        clean_keywords: List[str] = []

        for token in tokens:
            t_norm = remove_accents(token).lower()
            if len(t_norm) <= 1:
                continue
            if t_norm in STOPWORDS:
                continue
            # Also check if token is part of detected temporal or type words
            if t_norm in [
                "hom", "qua", "nay", "kia", "tuan", "thang", "word", "docx", "doc",
                "excel", "xlsx", "xls", "csv", "pdf", "scan", "slide", "pptx", "ppt",
                "anh", "hinh", "code", "tep", "file"
            ]:
                continue
            clean_keywords.append(token)

        # If all tokens were filtered out (e.g. user literally just typed "tìm file word hôm qua"),
        # keep keywords empty so we retrieve by time and type filters.
        return ParsedContext(
            raw_query=cleaned_raw,
            keywords=clean_keywords,
            extensions=extensions,
            date_min=date_min,
            date_max=date_max,
            time_desc=time_desc,
            file_type_desc=type_desc,
        )
