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

    def test_exclusion_parsing(self) -> None:
        ctx = ContextParser.parse_query("tìm file kế hoạch không phải word trừ pdf")
        self.assertIn(".docx", ctx.excluded_extensions)
        self.assertIn(".pdf", ctx.excluded_extensions)
        self.assertNotIn(".docx", ctx.extensions)
        self.assertNotIn(".pdf", ctx.extensions)
        self.assertIn("kế", ctx.keywords)

    def test_provenance_search(self) -> None:
        doc = {
            "file_path": "/tmp/overleaf_paper.pdf",
            "file_name": "Paper_Draft.pdf",
            "file_ext": ".pdf",
            "file_size": 4096,
            "created_at": 1700000000.0,
            "modified_at": 1700000000.0,
            "md5_hash": "pdf12345",
            "content_text": "Báo cáo nghiên cứu thuật toán ALNS-DDQN.\n\n[File Provenance]: Tải qua ứng dụng: Safari | Tải từ trang web / Nguồn: www.overleaf.com",
            "summary": "Bản nháp bài báo Overleaf",
            "indexed_at": 1700000000.0,
        }
        self.db.upsert_document(doc)

        res = self.engine.search("file pdf tải từ overleaf")
        self.assertTrue(len(res["results"]) > 0)
        top = res["results"][0]
        self.assertEqual(top.file_name, "Paper_Draft.pdf")

    def test_deduplication_and_version_trees(self) -> None:
        from rat.crawler.dedup import SmartDeduplicationEngine, normalize_stem_for_versioning
        stem = normalize_stem_for_versioning("Bao_cao_final_v2(1).docx")
        self.assertEqual(stem, "bao cao")

        # Insert 2 versions of a document
        doc_v1 = {
            "file_path": "/tmp/Bao_cao_v1.docx",
            "file_name": "Bao_cao_v1.docx",
            "file_ext": ".docx",
            "file_size": 1024,
            "created_at": 1700000000.0,
            "modified_at": 1700000000.0,
            "md5_hash": "hash_v1",
            "content_text": "Báo cáo tiến độ dự án phiên bản 1",
            "summary": "",
            "indexed_at": 1700000000.0,
        }
        doc_v2 = {
            "file_path": "/tmp/Bao_cao_final.docx",
            "file_name": "Bao_cao_final.docx",
            "file_ext": ".docx",
            "file_size": 1050,
            "created_at": 1700001000.0,
            "modified_at": 1700001000.0,
            "md5_hash": "hash_v2",
            "content_text": "Báo cáo tiến độ dự án phiên bản hoàn thiện",
            "summary": "",
            "indexed_at": 1700001000.0,
        }
        self.db.upsert_document(doc_v1)
        self.db.upsert_document(doc_v2)

        dedup = SmartDeduplicationEngine(self.db)
        trees = dedup.find_version_trees(min_versions=2)
        self.assertTrue(len(trees) >= 1)
        tree = [t for t in trees if t.canonical_name == "bao cao"][0]
        self.assertEqual(tree.count, 2)
        self.assertEqual(tree.latest_doc["file_name"], "Bao_cao_final.docx")

        # Check document version info
        v_info = dedup.get_document_version_info("/tmp/Bao_cao_final.docx")
        self.assertIsNotNone(v_info)
        self.assertTrue(v_info["is_latest"])

    def test_document_qa_engine(self) -> None:
        from rat.engine.qa_engine import qa_engine
        doc_text = (
            "Dự án NAMI triển khai nghiên cứu về tối ưu hóa lộ trình xe tự hành.\n"
            "Tổng ngân sách phê duyệt cho năm 2026 là 500.000.000 VNĐ.\n"
            "Người phụ trách chính: Huỳnh Nhật Huy."
        )
        res = qa_engine.answer_question(
            doc_text=doc_text,
            question="Tổng ngân sách dự án là bao nhiêu?",
            file_name="NAMI_Project.docx",
            use_cloud_if_available=False
        )
        self.assertIsNotNone(res)
        self.assertIn("500.000.000", res["answer"])
        self.assertTrue(len(res["snippets"]) > 0)


if __name__ == "__main__":
    unittest.main()
