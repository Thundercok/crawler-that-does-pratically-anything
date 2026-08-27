"""
tests/test_rat.py — Automated verification tests for rat search assistant.
"""

import sys
import unittest
from pathlib import Path

from rat.config import config
from rat.crawler.db import Database
from rat.crawler.extractors import extract_document_content
from rat.engine.context_parser import ContextParser
from rat.engine.hybrid_search import SearchEngine


class TestRatAssistant(unittest.TestCase):

    def setUp(self) -> None:
        self.test_db_path = "/tmp/test_rat.db"
        p = Path(self.test_db_path)
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
        self.db = Database(self.test_db_path)
        self.engine = SearchEngine(self.db)

        # Insert standard sample test document
        doc = {
            "file_path": "/tmp/test_file.docx",
            "file_name": "Ke_Hoach_Tai_Chinh_2026.docx",
            "file_ext": ".docx",
            "file_size": 1024,
            "created_at": 1700000000.0,
            "modified_at": 1700000000.0,
            "md5_hash": "abc12345",
            "content_text": "Bảng dự toán ngân sách quý 3 dành cho bộ phận kỹ thuật và kinh doanh.",
            "summary": "",
            "indexed_at": 1700000000.0,
        }
        self.db.upsert_document(doc)

    def test_context_parser_temporal(self) -> None:
        ctx_yesterday = ContextParser.parse_query("tìm file hôm qua")
        self.assertEqual(ctx_yesterday.time_desc, "Hôm qua")
        self.assertIsNotNone(ctx_yesterday.date_min)

        ctx_last_week = ContextParser.parse_query("báo cáo tuần trước")
        self.assertEqual(ctx_last_week.time_desc, "Tuần trước")

    def test_context_parser_file_types(self) -> None:
        ctx_word = ContextParser.parse_query("tìm tài liệu word kế hoạch")
        self.assertIn(".docx", ctx_word.extensions)
        self.assertIn("kế", ctx_word.keywords)

        ctx_pdf = ContextParser.parse_query("file pdf hợp đồng thuê nhà")
        self.assertIn(".pdf", ctx_pdf.extensions)
        self.assertIn("thuê", ctx_pdf.keywords)

    def test_db_upsert_and_search(self) -> None:
        # Search for exact keyword
        res = self.engine.search("dự toán ngân sách word")
        self.assertTrue(len(res["results"]) > 0)
        top = res["results"][0]
        self.assertEqual(top.file_name, "Ke_Hoach_Tai_Chinh_2026.docx")
        self.assertIn("ngân", top.explanation.lower())

    def test_unaccented_search(self) -> None:
        # Search in Vietnamese without accents
        res = self.engine.search("tai chinh du toan")
        self.assertTrue(len(res["results"]) > 0)
        self.assertEqual(res["results"][0].file_name, "Ke_Hoach_Tai_Chinh_2026.docx")

    def test_vision_taxonomy_expansion(self) -> None:
        from rat.crawler.vision_taxonomy import expand_taxonomy_labels
        en_tags, vi_tags = expand_taxonomy_labels(["sunset", "dog", "receipt"])
        self.assertIn("sunset", en_tags)
        self.assertIn("hoàng hôn", vi_tags)
        self.assertIn("chó", vi_tags)
        self.assertIn("hóa đơn", vi_tags)

    def test_multimodal_image_search(self) -> None:
        # Insert a sample image document with visual taxonomy concepts
        img_doc = {
            "file_path": "/tmp/IMG_9921.jpg",
            "file_name": "IMG_9921.jpg",
            "file_ext": ".jpg",
            "file_size": 2048,
            "created_at": 1700000000.0,
            "modified_at": 1700000000.0,
            "md5_hash": "img12345",
            "content_text": "Visual Concepts (VI): hoàng hôn, chiều tà, bãi biển, biển, đại dương\nVisual Concepts (EN): sunset, dusk, beach, ocean",
            "summary": "Ảnh chụp hoàng hôn trên bãi biển",
            "indexed_at": 1700000000.0,
        }
        self.db.upsert_document(img_doc)

        res = self.engine.search("ảnh hoàng hôn bãi biển")
        self.assertTrue(len(res["results"]) > 0)
        found_names = [r.file_name for r in res["results"]]
        self.assertIn("IMG_9921.jpg", found_names)


if __name__ == "__main__":
    unittest.main()
