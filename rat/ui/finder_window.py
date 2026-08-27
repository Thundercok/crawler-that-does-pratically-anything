"""
rat.ui.finder_window — Full macOS Native AI Finder Window.
Provides a comprehensive File Manager experience with Smart Virtual Collections,
Dual List/Grid Views, Metadata Inspector, and In-Situ AI Document Assistant.
"""

from __future__ import annotations

import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from rat.config import config
from rat.crawler.db import Database
from rat.crawler.dedup import dedup_engine
from rat.crawler.extractors import extract_document_content
from rat.engine.hybrid_search import SearchEngine
from rat.engine.qa_engine import qa_engine
from rat.engine.reranker import SearchResultItem, format_file_size, format_relative_time
from rat.ui.preview_panel import EXT_DESCRIPTIONS, open_file_default, reveal_in_finder
from rat.ui.theme import get_ext_badge_info

logger = logging.getLogger("rat.finder")


class FinderSearchWorker(QThread):
    """Background worker for debounced search and collection querying."""
    results_ready = pyqtSignal(dict)

    def __init__(self, engine: SearchEngine) -> None:
        super().__init__()
        self.engine = engine
        self.query_text: str = ""
        self.collection_filter: Optional[str] = None

    def search_query(self, query: str, collection: Optional[str] = None) -> None:
        self.query_text = query
        self.collection_filter = collection
        if not self.isRunning():
            self.start()

    def run(self) -> None:
        try:
            if self.collection_filter and not self.query_text.strip():
                # Fetch collection items
                items = self._get_collection_items(self.collection_filter)
                self.results_ready.emit({"results": items, "count": len(items)})
            else:
                # Perform natural language search
                res = self.engine.search(self.query_text, limit=40, use_hyde=False)
                self.results_ready.emit(res)
        except Exception as e:
            logger.debug(f"Finder search error: {e}")
            self.results_ready.emit({"results": [], "error": str(e)})

    def _get_collection_items(self, collection_key: str) -> List[SearchResultItem]:
        conn = self.engine.db.get_connection()
        cursor = conn.cursor()

        query_sql = "SELECT * FROM documents "
        params = []

        if collection_key == "docs":
            query_sql += "WHERE file_ext IN ('.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.txt', '.md') "
        elif collection_key == "images":
            query_sql += "WHERE file_ext IN ('.png', '.jpg', '.jpeg', '.webp', '.svg') "
        elif collection_key == "code":
            query_sql += "WHERE file_ext IN ('.py', '.js', '.ts', '.html', '.css', '.json', '.sql', '.sh', '.yaml') "
        elif collection_key == "provenance":
            query_sql += "WHERE content_text LIKE '%[File Provenance]%' "
        elif collection_key == "recent":
            pass  # Just order by modified_at desc

        query_sql += "ORDER BY modified_at DESC LIMIT 60"
        cursor.execute(query_sql, params)
        rows = [dict(r) for r in cursor.fetchall()]

        items = []
        for r in rows:
            desc = EXT_DESCRIPTIONS.get(r["file_ext"].lower(), f"Tệp {r['file_ext'].upper()}")
            snippet = r.get("content_text", "")[:240]
            v_info = dedup_engine.get_document_version_info(r["file_path"])
            item = SearchResultItem(
                file_path=r["file_path"],
                file_name=r["file_name"],
                file_ext=r["file_ext"],
                file_size=r["file_size"],
                modified_at=r["modified_at"],
                score=100.0,
                explanation=f"{desc} • Sửa {format_relative_time(r['modified_at'])}",
                snippet=snippet,
                version_info=v_info,
            )
            items.append(item)
        return items


class FinderPreviewPanel(QFrame):
    """Rich Inspector Sidebar with Image Preview and In-Situ AI Chat."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("FinderPreviewPanel")
        self.current_item: Optional[SearchResultItem] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header Info
        header_row = QHBoxLayout()
        self.badge_label = QLabel("FILE")
        self.badge_label.setFixedSize(38, 38)
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_label.setStyleSheet("background-color: #007aff; color: white; font-weight: bold; border-radius: 8px;")

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.name_label = QLabel("Chọn một tệp tin")
        self.name_label.setStyleSheet("color: #1c1c1e; font-size: 14px; font-weight: 600;")
        self.name_label.setWordWrap(True)
        self.meta_sub_label = QLabel("")
        self.meta_sub_label.setStyleSheet("color: #636366; font-size: 11px;")
        title_col.addWidget(self.name_label)
        title_col.addWidget(self.meta_sub_label)

        header_row.addWidget(self.badge_label)
        header_row.addLayout(title_col, 1)
        layout.addLayout(header_row)

        # Image Thumbnail Preview (if image)
        self.image_preview_label = QLabel()
        self.image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label.setStyleSheet("background-color: #f2f2f7; border-radius: 8px; border: 1px solid #e5e5ea; padding: 4px;")
        self.image_preview_label.setFixedHeight(140)
        self.image_preview_label.hide()
        layout.addWidget(self.image_preview_label)

        # AI Context Explanation
        self.reason_card = QFrame()
        self.reason_card.setStyleSheet("background-color: #e0f2fe; border-radius: 6px; padding: 6px; border: 1px solid #7dd3fc;")
        r_layout = QVBoxLayout(self.reason_card)
        r_layout.setContentsMargins(4, 4, 4, 4)
        self.reason_text = QLabel("")
        self.reason_text.setStyleSheet("color: #0369a1; font-size: 11px; font-weight: 500;")
        self.reason_text.setWordWrap(True)
        r_layout.addWidget(self.reason_text)
        layout.addWidget(self.reason_card)

        # Quick Look Text
        ql_title = QLabel("📄 Nội dung trích đoạn:")
        ql_title.setStyleSheet("color: #636366; font-size: 11px; font-weight: 600;")
        layout.addWidget(ql_title)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #1c1c1e;
                border: 1px solid #e5e5ea;
                border-radius: 6px;
                font-family: -apple-system, sans-serif;
                font-size: 11px;
                line-height: 1.4;
                padding: 6px;
            }
        """)
        layout.addWidget(self.preview_text, 1)

        # In-Situ AI Ask Section
        ask_card = QFrame()
        ask_card.setStyleSheet("background-color: #f8fafc; border-radius: 8px; border: 1px solid #cbd5e1; padding: 6px;")
        ask_layout = QVBoxLayout(ask_card)
        ask_layout.setContentsMargins(6, 6, 6, 6)
        ask_layout.setSpacing(6)

        ask_header = QLabel("🧠 Trợ lý AI Hỏi - Đáp trực tiếp:")
        ask_header.setStyleSheet("color: #0f172a; font-size: 11px; font-weight: 600;")
        ask_layout.addWidget(ask_header)

        ask_input_row = QHBoxLayout()
        self.ask_input = QLineEdit()
        self.ask_input.setPlaceholderText("Hỏi gì đó về file này... (nhấn Enter)")
        self.ask_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #94a3b8;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid #007aff;
            }
        """)
        self.ask_input.returnPressed.connect(self._handle_ask_question)

        self.ask_btn = QPushButton("Hỏi")
        self.ask_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                font-weight: 600;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.ask_btn.clicked.connect(self._handle_ask_question)
        ask_input_row.addWidget(self.ask_input, 1)
        ask_input_row.addWidget(self.ask_btn)
        ask_layout.addLayout(ask_input_row)

        self.qa_answer_view = QLabel("")
        self.qa_answer_view.setStyleSheet("color: #1e293b; font-size: 11px; line-height: 1.3;")
        self.qa_answer_view.setWordWrap(True)
        self.qa_answer_view.hide()
        ask_layout.addWidget(self.qa_answer_view)

        layout.addWidget(ask_card)

    def set_item(self, item: Optional[SearchResultItem]) -> None:
        self.current_item = item
        self.qa_answer_view.hide()
        self.qa_answer_view.setText("")
        self.ask_input.clear()

        if not item:
            self.name_label.setText("Chọn một tệp tin")
            self.meta_sub_label.setText("")
            self.image_preview_label.hide()
            self.reason_card.hide()
            self.preview_text.setPlainText("")
            return

        info = get_ext_badge_info(item.file_ext)
        self.badge_label.setText(info["label"])
        self.badge_label.setStyleSheet(f"background-color: {info['bg']}; color: {info['fg']}; font-weight: bold; border-radius: 8px;")
        self.name_label.setText(item.file_name)
        self.meta_sub_label.setText(f"{item.file_size_formatted} • {item.modified_formatted}")

        # Image thumbnail preview
        ext = item.file_ext.lower()
        if ext in [".png", ".jpg", ".jpeg", ".webp"] and os.path.exists(item.file_path):
            pixmap = QPixmap(item.file_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(280, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.image_preview_label.setPixmap(scaled)
                self.image_preview_label.show()
            else:
                self.image_preview_label.hide()
        else:
            self.image_preview_label.hide()

        # Reason card
        if item.explanation:
            self.reason_card.show()
            self.reason_text.setText(f"💡 {item.explanation}")
        else:
            self.reason_card.hide()

        self.preview_text.setPlainText(item.snippet or "(Không có đoạn trích nội dung)")

    def _handle_ask_question(self) -> None:
        q = self.ask_input.text().strip()
        if not q or not self.current_item:
            return

        self.qa_answer_view.show()
        self.qa_answer_view.setText("⏳ <i>Đang suy luận câu trả lời...</i>")
        try:
            content = extract_document_content(self.current_item.file_path)
            qa_res = qa_engine.answer_question(content, q, file_name=self.current_item.file_name)
            ans = qa_res.get("answer", "Không có câu trả lời.")
            engine_name = qa_res.get("engine", "AI")
            self.qa_answer_view.setText(f"<b>{engine_name}:</b>\n{ans}")
        except Exception as e:
            self.qa_answer_view.setText(f"⚠️ Lỗi: {e}")


class FinderWindow(QMainWindow):
    """Full-featured macOS AI Finder Application Window."""

    def __init__(self) -> None:
        super().__init__()
        self.db = Database(config.db_path)
        self.search_engine = SearchEngine(self.db)
        self.worker = FinderSearchWorker(self.search_engine)
        self.worker.results_ready.connect(self._on_search_results)

        self.current_results: List[SearchResultItem] = []
        self.active_collection: str = "all"
        self._init_window()
        self._init_ui()

        # Warm up engine and load all files by default
        self.worker.search_query("", collection="all")

    def _init_window(self) -> None:
        self.setWindowTitle("rat — macOS Smart AI Finder")
        self.resize(1120, 720)
        self.setMinimumSize(880, 560)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ececec;
            }
            QSplitter::handle {
                background-color: #d1d1d6;
                width: 1px;
            }
        """)

    def _init_ui(self) -> None:
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(1)

        # 1. Left macOS Sidebar
        sidebar_frame = QFrame()
        sidebar_frame.setFixedWidth(220)
        sidebar_frame.setStyleSheet("background-color: #e5e5ea; border-right: 1px solid #d1d1d6;")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(10, 14, 10, 14)
        sidebar_layout.setSpacing(4)

        sb_header = QLabel("THƯ MỤC THÔNG MINH")
        sb_header.setStyleSheet("color: #8e8e93; font-size: 10px; font-weight: 700; padding-left: 8px; margin-bottom: 2px;")
        sidebar_layout.addWidget(sb_header)

        self.sidebar_list = QListWidget()
        self.sidebar_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 7px 10px;
                border-radius: 6px;
                color: #1c1c1e;
                font-size: 12px;
                font-weight: 500;
            }
            QListWidget::item:selected {
                background-color: #007aff;
                color: #ffffff;
                font-weight: 600;
            }
            QListWidget::item:hover:!selected {
                background-color: #dcdce2;
            }
        """)

        collections = [
            ("🌟 Tất cả tệp (All Files)", "all"),
            ("📄 Tài liệu văn phòng", "docs"),
            ("🖼️ Hình ảnh & Trực quan", "images"),
            ("💻 Mã nguồn dự án", "code"),
            ("🌐 Tải từ Web (Provenance)", "provenance"),
            ("🕒 Sửa đổi gần đây", "recent"),
        ]

        for label, key in collections:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.sidebar_list.addItem(item)

        self.sidebar_list.setCurrentRow(0)
        self.sidebar_list.itemClicked.connect(self._on_sidebar_item_clicked)
        sidebar_layout.addWidget(self.sidebar_list, 1)

        # Quick Watched Folders Section
        wf_header = QLabel("VỊ TRÍ THEO DÕI")
        wf_header.setStyleSheet("color: #8e8e93; font-size: 10px; font-weight: 700; padding-left: 8px; margin-top: 10px;")
        sidebar_layout.addWidget(wf_header)

        watched_label = QLabel(f"• Downloads\n• Documents\n• Desktop")
        watched_label.setStyleSheet("color: #48484a; font-size: 11.5px; padding-left: 10px; line-height: 1.5;")
        sidebar_layout.addWidget(watched_label)

        main_splitter.addWidget(sidebar_frame)

        # 2. Center Content Area (Toolbar + File Table)
        center_frame = QFrame()
        center_frame.setStyleSheet("background-color: #ffffff;")
        center_layout = QVBoxLayout(center_frame)
        center_layout.setContentsMargins(14, 12, 14, 12)
        center_layout.setSpacing(10)

        # Top Toolbar
        toolbar_row = QHBoxLayout()
        toolbar_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm ngữ cảnh: 'slide nami', 'báo cáo tháng 7', 'ảnh screenshot'...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f2f2f7;
                color: #1c1c1e;
                border: 1px solid #d1d1d6;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                background-color: #ffffff;
                border: 1.5px solid #007aff;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        toolbar_row.addWidget(self.search_input, 1)

        # Action Buttons
        self.btn_open = QPushButton("Mở tệp")
        self.btn_open.setStyleSheet("background-color: #007aff; color: white; font-weight: 600; border-radius: 6px; padding: 6px 12px;")
        self.btn_open.clicked.connect(self._open_selected_file)
        toolbar_row.addWidget(self.btn_open)

        self.btn_reveal = QPushButton("Finder")
        self.btn_reveal.setStyleSheet("background-color: #f2f2f7; color: #1c1c1e; border: 1px solid #d1d1d6; border-radius: 6px; padding: 6px 12px;")
        self.btn_reveal.clicked.connect(self._reveal_selected_file)
        toolbar_row.addWidget(self.btn_reveal)

        center_layout.addLayout(toolbar_row)

        # Status row
        status_row = QHBoxLayout()
        self.status_count_label = QLabel("Đang tải dữ liệu...")
        self.status_count_label.setStyleSheet("color: #8e8e93; font-size: 11px;")
        status_row.addWidget(self.status_count_label)
        status_row.addStretch()
        center_layout.addLayout(status_row)

        # Main Table Widget (Finder List Mode)
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["Tên tệp tin", "Sửa đổi lần cuối", "Kích thước", "Khớp ngữ cảnh AI"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.file_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.file_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.file_table.setShowGrid(False)
        self.file_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e5ea;
                border-radius: 8px;
                gridline-color: transparent;
                font-size: 12px;
                background-color: #ffffff;
            }
            QTableWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #f2f2f7;
            }
            QTableWidget::item:selected {
                background-color: #e5f1fb;
                color: #007aff;
                font-weight: 500;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #64748b;
                font-weight: 600;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid #e2e8f0;
                padding: 6px;
            }
        """)
        self.file_table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.file_table.itemDoubleClicked.connect(self._open_selected_file)
        center_layout.addWidget(self.file_table, 1)

        main_splitter.addWidget(center_frame)

        # 3. Right Inspector Panel
        self.preview_panel = FinderPreviewPanel()
        self.preview_panel.setFixedWidth(320)
        self.preview_panel.setStyleSheet("background-color: #f8fafc; border-left: 1px solid #d1d1d6;")
        main_splitter.addWidget(self.preview_panel)

        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setStretchFactor(2, 0)

        self.setCentralWidget(main_splitter)

    def _on_sidebar_item_clicked(self, item: QListWidgetItem) -> None:
        key = item.data(Qt.ItemDataRole.UserRole)
        self.active_collection = key
        self.search_input.clear()
        self.worker.search_query("", collection=key)

    def _on_search_text_changed(self, text: str) -> None:
        q = text.strip()
        if q:
            self.worker.search_query(q, collection=None)
        else:
            self.worker.search_query("", collection=self.active_collection)

    def _on_search_results(self, response: Dict[str, Any]) -> None:
        results = response.get("results", [])
        self.current_results = results
        self.status_count_label.setText(f"Hiển thị {len(results)} tệp tin phù hợp")

        self.file_table.setRowCount(len(results))
        for row_idx, item in enumerate(results):
            # Name
            name_item = QTableWidgetItem(f"📄 {item.file_name}")
            name_item.setData(Qt.ItemDataRole.UserRole, item)
            self.file_table.setItem(row_idx, 0, name_item)

            # Modified
            mod_item = QTableWidgetItem(item.modified_formatted)
            mod_item.setForeground(QColor("#636366"))
            self.file_table.setItem(row_idx, 1, mod_item)

            # Size
            size_item = QTableWidgetItem(item.file_size_formatted)
            size_item.setForeground(QColor("#636366"))
            self.file_table.setItem(row_idx, 2, size_item)

            # Reason / Version
            expl = item.explanation or "Tệp tin"
            reason_item = QTableWidgetItem(expl[:45] + ("..." if len(expl) > 45 else ""))
            reason_item.setForeground(QColor("#0284c7"))
            self.file_table.setItem(row_idx, 3, reason_item)

        if results:
            self.file_table.selectRow(0)
        else:
            self.preview_panel.set_item(None)

    def _on_table_selection_changed(self) -> None:
        selected_rows = self.file_table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if 0 <= row < len(self.current_results):
            self.preview_panel.set_item(self.current_results[row])

    def _open_selected_file(self) -> None:
        selected_rows = self.file_table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if 0 <= row < len(self.current_results):
            open_file_default(self.current_results[row].file_path)

    def _reveal_selected_file(self) -> None:
        selected_rows = self.file_table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if 0 <= row < len(self.current_results):
            reveal_in_finder(self.current_results[row].file_path)


def run_finder() -> None:
    """Run standalone Finder window."""
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = FinderWindow()
    window.show()
    sys.exit(app.exec())
