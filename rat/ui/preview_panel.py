"""
rat.ui.preview_panel — SOTA Apple macOS Sequoia & Raycast-grade Inspector Panel.
Features:
- Native Apple Folded Dog-Ear & Squircle Hero Headers
- Linear-style Metadata Tag Chips (Path, Modified, Provenance, Visual)
- High-DPI Smooth Image Thumbnail Quick Look
- SOTA FR-CoT Multi-Engine Convergence Stepper & Timeline
- In-Situ AI Document Q&A Command Bar
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from rat.engine.reasoning_trace import ReasoningTrace
from rat.engine.reranker import SearchResultItem
from rat.ui.theme import get_ext_badge_info

EXT_DESCRIPTIONS = {
    ".docx": "Tài liệu Word",
    ".doc": "Tài liệu Word",
    ".pdf": "Tài liệu PDF",
    ".xlsx": "Bảng tính Excel",
    ".xls": "Bảng tính Excel",
    ".csv": "Dữ liệu CSV",
    ".pptx": "Bản trình chiếu PPT",
    ".ppt": "Bản trình chiếu PPT",
    ".py": "Mã nguồn Python",
    ".js": "Mã nguồn JavaScript",
    ".ts": "Mã nguồn TypeScript",
    ".html": "Trang web HTML",
    ".css": "Định dạng CSS",
    ".json": "Cấu hình JSON",
    ".sh": "Tập lệnh Shell",
    ".sql": "Cơ sở dữ liệu SQL",
    ".txt": "Văn bản thuần Text",
    ".md": "Tài liệu Markdown",
    ".png": "Hình ảnh PNG",
    ".jpg": "Hình ảnh JPEG",
    ".jpeg": "Hình ảnh JPEG",
    ".webp": "Hình ảnh WebP",
}


def open_file_default(file_path: str) -> None:
    if not os.path.exists(file_path):
        return
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", file_path])
    elif system == "Windows":
        os.startfile(file_path)
    else:
        subprocess.run(["xdg-open", file_path])


def reveal_in_finder(file_path: str) -> None:
    if not os.path.exists(file_path):
        return
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", "-R", file_path])
    elif system == "Windows":
        subprocess.run(["explorer", "/select,", os.path.normpath(file_path)])
    else:
        parent_dir = str(Path(file_path).parent)
        subprocess.run(["xdg-open", parent_dir])


class PreviewPanel(QFrame):
    """SOTA Apple macOS Sequoia & Raycast Inspector Panel."""
    ask_requested = pyqtSignal(str, str, str)  # (file_path, file_name, question)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("PreviewPanel")
        self.current_item: Optional[SearchResultItem] = None
        self.current_trace: Optional[ReasoningTrace] = None
        self.current_plan: Optional[Dict[str, Any]] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(9)

        # -------------------------------------------------------------
        # 1. Hero File Header (42x42 squircle icon + Title + Kind/Size)
        # -------------------------------------------------------------
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 6px 10px;
            }
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(4, 4, 4, 4)
        h_layout.setSpacing(10)

        self.badge_label = QLabel("FILE")
        self.badge_label.setFixedSize(40, 40)
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_label.setStyleSheet("""
            background-color: #007aff;
            color: #ffffff;
            font-weight: 700;
            font-size: 11px;
            border-radius: 8px;
        """)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        self.name_label = QLabel("Chọn một tệp tin")
        self.name_label.setStyleSheet("color: #0f172a; font-size: 14.5px; font-weight: 600;")
        self.name_label.setWordWrap(True)

        self.meta_sub_label = QLabel("")
        self.meta_sub_label.setStyleSheet("color: #64748b; font-size: 11px;")

        title_col.addWidget(self.name_label)
        title_col.addWidget(self.meta_sub_label)

        h_layout.addWidget(self.badge_label)
        h_layout.addLayout(title_col, 1)
        layout.addWidget(header_card)

        # -------------------------------------------------------------
        # 2. Image Thumbnail Quick Look (Only shown for images)
        # -------------------------------------------------------------
        self.image_preview_box = QLabel()
        self.image_preview_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_box.setFixedHeight(140)
        self.image_preview_box.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 4px;
        """)
        self.image_preview_box.hide()
        layout.addWidget(self.image_preview_box)

        # -------------------------------------------------------------
        # 3. Linear-Style Metadata Tag Chips
        # -------------------------------------------------------------
        self.meta_chips_frame = QFrame()
        self.meta_chips_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
            QLabel.MetaPill {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                padding: 2px 7px;
                font-size: 10.5px;
                font-weight: 500;
            }
        """)
        chips_layout = QHBoxLayout(self.meta_chips_frame)
        chips_layout.setContentsMargins(0, 0, 0, 0)
        chips_layout.setSpacing(5)

        self.pill_path = QLabel("📁 /")
        self.pill_path.setProperty("class", "MetaPill")
        chips_layout.addWidget(self.pill_path)

        self.pill_time = QLabel("🕒 Hôm nay")
        self.pill_time.setProperty("class", "MetaPill")
        chips_layout.addWidget(self.pill_time)

        self.pill_source = QLabel("🌐 Safari")
        self.pill_source.setProperty("class", "MetaPill")
        self.pill_source.setStyleSheet("background-color: #faf5ff; color: #7c3aed; border: 1px solid #e9d5ff;")
        self.pill_source.hide()
        chips_layout.addWidget(self.pill_source)

        chips_layout.addStretch()
        layout.addWidget(self.meta_chips_frame)

        # -------------------------------------------------------------
        # 4. Context Reason Card (Soft Azure Tint)
        # -------------------------------------------------------------
        self.reason_box = QFrame()
        self.reason_box.setStyleSheet("""
            QFrame {
                background-color: #f0f9ff;
                border: 1px solid #bae6fd;
                border-radius: 7px;
                padding: 5px 8px;
            }
        """)
        reason_layout = QVBoxLayout(self.reason_box)
        reason_layout.setContentsMargins(6, 4, 6, 4)
        reason_layout.setSpacing(2)

        self.reason_title = QLabel("💡 Khớp ngữ cảnh AI:")
        self.reason_title.setStyleSheet("color: #0284c7; font-size: 11px; font-weight: 600;")
        self.reason_text = QLabel("")
        self.reason_text.setStyleSheet("color: #0369a1; font-size: 11.5px; line-height: 1.35;")
        self.reason_text.setWordWrap(True)

        reason_layout.addWidget(self.reason_title)
        reason_layout.addWidget(self.reason_text)
        layout.addWidget(self.reason_box)

        # -------------------------------------------------------------
        # 5. Segmented Mode Switcher (26px SOTA macOS Control)
        # -------------------------------------------------------------
        switch_row = QHBoxLayout()
        switch_row.setSpacing(6)
        switch_row.setContentsMargins(0, 1, 0, 1)

        self.seg_container = QFrame()
        self.seg_container.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QPushButton {
                border: none;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 500;
                color: #64748b;
                background-color: transparent;
            }
            QPushButton:hover {
                color: #0f172a;
            }
            QPushButton[selected="true"] {
                background-color: #ffffff;
                color: #0f172a;
                font-weight: 600;
                border: 1px solid #cbd5e1;
            }
        """)
        seg_layout = QHBoxLayout(self.seg_container)
        seg_layout.setContentsMargins(2, 2, 2, 2)
        seg_layout.setSpacing(2)

        self.btn_tab_preview = QPushButton("📄 Xem trước")
        self.btn_tab_preview.setProperty("selected", "true")
        self.btn_tab_preview.clicked.connect(lambda: self.set_active_tab(0))

        self.btn_tab_cot = QPushButton("🧠 Suy luận CoT")
        self.btn_tab_cot.setProperty("selected", "false")
        self.btn_tab_cot.clicked.connect(lambda: self.set_active_tab(1))

        seg_layout.addWidget(self.btn_tab_preview)
        seg_layout.addWidget(self.btn_tab_cot)

        switch_row.addWidget(self.seg_container)
        switch_row.addStretch()
        layout.addLayout(switch_row)

        # -------------------------------------------------------------
        # 6. Stacked Pages: [Page 0: Preview Text | Page 1: CoT Timeline]
        # -------------------------------------------------------------
        self.stack = QStackedWidget()

        # Page 0: Quick Look Editor
        self.preview_text = QTextEdit()
        self.preview_text.setObjectName("PreviewContent")
        self.preview_text.setReadOnly(True)
        self.preview_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                color: #0f172a;
                font-size: 11.5px;
                line-height: 1.45;
                padding: 8px;
            }
        """)
        self.stack.addWidget(self.preview_text)

        # Page 1: Minimalist CoT Timeline View
        self.cot_scroll = QScrollArea()
        self.cot_scroll.setWidgetResizable(True)
        self.cot_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cot_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cot_scroll.setStyleSheet("background-color: transparent;")

        self.cot_content_widget = QWidget()
        self.cot_content_layout = QVBoxLayout(self.cot_content_widget)
        self.cot_content_layout.setContentsMargins(2, 2, 2, 2)
        self.cot_content_layout.setSpacing(7)
        self.cot_scroll.setWidget(self.cot_content_widget)

        self.stack.addWidget(self.cot_scroll)
        layout.addWidget(self.stack, 1)

        # -------------------------------------------------------------
        # 7. Linear-Style In-Situ AI Document Q&A Bar
        # -------------------------------------------------------------
        chat_frame = QFrame()
        chat_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 4px 6px;
            }
        """)
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(4, 4, 4, 4)
        chat_layout.setSpacing(4)

        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self.ask_input = QLineEdit()
        self.ask_input.setPlaceholderText("💬 Hỏi AI về tệp này... (Nhấn ↵)")
        self.ask_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 5px 9px;
                font-size: 11.5px;
            }
            QLineEdit:focus {
                border: 1.5px solid #007aff;
            }
        """)
        self.ask_input.returnPressed.connect(self._trigger_ask)

        self.ask_btn = QPushButton("Hỏi ↵")
        self.ask_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: #ffffff;
                font-weight: 600;
                font-size: 11px;
                border-radius: 6px;
                padding: 5px 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.ask_btn.clicked.connect(self._trigger_ask)

        input_row.addWidget(self.ask_input, 1)
        input_row.addWidget(self.ask_btn)
        chat_layout.addLayout(input_row)

        self.qa_response_box = QLabel("")
        self.qa_response_box.setStyleSheet("""
            background-color: #ffffff;
            color: #1e293b;
            font-size: 11.5px;
            padding: 7px 9px;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
            line-height: 1.4;
        """)
        self.qa_response_box.setWordWrap(True)
        self.qa_response_box.hide()
        chat_layout.addWidget(self.qa_response_box)

        layout.addWidget(chat_frame)

        self._render_empty_cot()

    def set_active_tab(self, tab_index: int) -> None:
        """Switch between 0 (Quick Look) and 1 (CoT Timeline)."""
        self.stack.setCurrentIndex(tab_index)
        if tab_index == 0:
            self.btn_tab_preview.setProperty("selected", "true")
            self.btn_tab_cot.setProperty("selected", "false")
        else:
            self.btn_tab_preview.setProperty("selected", "false")
            self.btn_tab_cot.setProperty("selected", "true")

        self.btn_tab_preview.style().unpolish(self.btn_tab_preview)
        self.btn_tab_preview.style().polish(self.btn_tab_preview)
        self.btn_tab_cot.style().unpolish(self.btn_tab_cot)
        self.btn_tab_cot.style().polish(self.btn_tab_cot)

    def _render_empty_cot(self) -> None:
        """Render placeholder when no search query is active."""
        while self.cot_content_layout.count():
            item = self.cot_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        empty_label = QLabel("Chưa có chuỗi suy luận.\nHãy nhập câu hỏi tìm kiếm ở ô phía trên.")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("color: #94a3b8; font-size: 11.5px; padding: 40px 10px;")
        self.cot_content_layout.addWidget(empty_label)
        self.cot_content_layout.addStretch()

    def set_reasoning_trace(
        self,
        trace: Optional[ReasoningTrace],
        plan: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update CoT reasoning trace with SOTA visual cards."""
        self.current_trace = trace
        self.current_plan = plan

        if not trace or not trace.steps:
            self.btn_tab_cot.setText("🧠 Suy luận CoT")
            self._render_empty_cot()
            return

        conf_pct = int(trace.final_confidence * 100)
        self.btn_tab_cot.setText(f"🧠 Suy luận CoT ({conf_pct}%)")

        while self.cot_content_layout.count():
            item = self.cot_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. Summary Header Card
        status_text = "ĐỦ ĐIỀU KIỆN" if trace.is_sufficient else "PHẦN NÀO"
        status_color = "#15803d" if trace.is_sufficient else "#b45309"
        status_bg = "#f0fdf4" if trace.is_sufficient else "#fefce8"
        border_color = "#bbf7d0" if trace.is_sufficient else "#fef08a"

        header_card = QFrame()
        header_card.setStyleSheet(f"""
            QFrame {{
                background-color: {status_bg};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 4px 8px;
            }}
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(6, 3, 6, 3)
        h_layout.setSpacing(6)

        lbl_status = QLabel(f"● <b>{status_text}</b> ({conf_pct}%)")
        lbl_status.setStyleSheet(f"color: {status_color}; font-size: 11.5px;")
        h_layout.addWidget(lbl_status)
        h_layout.addStretch()

        lbl_latency = QLabel(f"⚡ {trace.total_latency_ms}ms • {len(trace.steps)} bước")
        lbl_latency.setStyleSheet("color: #64748b; font-size: 10.5px;")
        h_layout.addWidget(lbl_latency)
        self.cot_content_layout.addWidget(header_card)

        # 2. Render Step Cards
        phase_icons = {
            "decompose": ("🔍", "Phân rã mục tiêu (MFQD)", "#0284c7", "#f0f9ff", "#e0f2fe"),
            "retrieve": ("⚡", "Truy xuất đa luồng (M-RRF)", "#7c3aed", "#faf5ff", "#f3e8ff"),
            "evaluate": ("🎯", "Đánh giá thông tin", "#059669", "#ecfdf5", "#d1fae5"),
            "correct": ("🛠️", "Tự động sửa lỗi (CRAG)", "#ea580c", "#fff7ed", "#ffedd5"),
            "rerank": ("📊", "Tái xếp hạng & Bằng chứng", "#334155", "#f8fafc", "#e2e8f0"),
            "synthesize": ("💬", "Tổng hợp tri thức", "#2563eb", "#eff6ff", "#dbeafe"),
        }

        for step in trace.steps:
            icon, title_text, col_accent, col_bg, col_border = phase_icons.get(
                step.phase, ("🔹", step.phase.upper(), "#475569", "#f8fafc", "#e2e8f0")
            )

            step_card = QFrame()
            step_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {col_bg};
                    border: 1px solid {col_border};
                    border-radius: 6px;
                    padding: 4px 7px;
                }}
            """)
            s_layout = QVBoxLayout(step_card)
            s_layout.setContentsMargins(5, 4, 5, 4)
            s_layout.setSpacing(2)

            title_row = QHBoxLayout()
            title_row.setSpacing(6)
            title_lbl = QLabel(f"{icon} <b>{title_text}</b>")
            title_lbl.setStyleSheet(f"color: {col_accent}; font-size: 11px;")
            title_row.addWidget(title_lbl)
            title_row.addStretch()

            step_ms = QLabel(f"{step.latency_ms}ms")
            step_ms.setStyleSheet("color: #94a3b8; font-size: 10px;")
            title_row.addWidget(step_ms)
            s_layout.addLayout(title_row)

            obs_text = step.observation if step.observation else step.thought
            if obs_text:
                desc_lbl = QLabel(obs_text)
                desc_lbl.setStyleSheet("color: #334155; font-size: 10.5px; line-height: 1.35;")
                desc_lbl.setWordWrap(True)
                s_layout.addWidget(desc_lbl)

            self.cot_content_layout.addWidget(step_card)

        self.cot_content_layout.addStretch()

    def set_item(self, item: Optional[SearchResultItem]) -> None:
        """Update file details, metadata pills, thumbnail, and content."""
        self.current_item = item
        self.qa_response_box.hide()
        self.qa_response_box.setText("")
        self.ask_input.clear()

        if not item:
            self.badge_label.setText("FILE")
            self.badge_label.setStyleSheet("background-color: #e2e8f0; color: #64748b; font-weight: 700; font-size: 11px; border-radius: 8px;")
            self.name_label.setText("Chọn một tệp để xem chi tiết")
            self.meta_sub_label.setText("")
            self.image_preview_box.hide()
            self.reason_box.hide()
            self.preview_text.setPlainText("")
            self.pill_path.setText("📁 /")
            self.pill_time.setText("🕒 Chưa có")
            self.pill_source.hide()
            return

        info = get_ext_badge_info(item.file_ext)
        self.badge_label.setText(info["label"])
        self.badge_label.setStyleSheet(f"""
            background-color: {info['bg']};
            color: {info['fg']};
            font-weight: 700;
            font-size: 11px;
            border-radius: 8px;
        """)

        self.name_label.setText(item.file_name)

        ext_clean = item.file_ext.lower()
        desc = EXT_DESCRIPTIONS.get(ext_clean, f"Tệp {ext_clean.upper()}")
        self.meta_sub_label.setText(f"{desc}  •  {item.file_size_formatted}")

        # Metadata Chips
        p = item.file_path
        if len(p) > 42:
            p = "..." + p[-38:]
        self.pill_path.setText(f"📁 {p}")
        self.pill_time.setText(f"🕒 {item.modified_formatted}")

        # Provenance pill
        snippet_text = item.snippet or ""
        if "[File Provenance]" in snippet_text:
            prov_app = "Safari"
            for app_name in ["Telegram", "Chrome", "Slack", "Discord", "Overleaf", "Google Drive"]:
                if app_name.lower() in snippet_text.lower():
                    prov_app = app_name
                    break
            self.pill_source.setText(f"🌐 Tải từ {prov_app}")
            self.pill_source.show()
        else:
            self.pill_source.hide()

        # Reason Card (Only show if score > 10)
        score_val = int(getattr(item, "score", 0))
        if score_val > 10:
            self.reason_box.show()
            self.reason_text.setText(f"{item.explanation}  •  Độ khớp: {score_val}%")
        else:
            self.reason_box.hide()

        # Image Thumbnail View
        if ext_clean in [".png", ".jpg", ".jpeg", ".webp"] and os.path.exists(item.file_path):
            pix = QPixmap(item.file_path)
            if not pix.isNull():
                scaled = pix.scaled(280, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.image_preview_box.setPixmap(scaled)
                self.image_preview_box.show()
            else:
                self.image_preview_box.hide()
        else:
            self.image_preview_box.hide()

        # Text Quick Look
        preview_body = snippet_text if snippet_text else "(Không có nội dung trích đoạn xem trước)"
        self.preview_text.setPlainText(preview_body)

    def _trigger_ask(self) -> None:
        q = self.ask_input.text().strip()
        if not q or not self.current_item:
            return

        self.qa_response_box.show()
        self.qa_response_box.setText("⏳ <i>Đang phân tích tài liệu và suy luận...</i>")
        self.ask_requested.emit(self.current_item.file_path, self.current_item.file_name, q)

    def set_qa_answer(self, result: Dict[str, Any]) -> None:
        ans = result.get("answer", "Không có câu trả lời.")
        engine = result.get("engine", "AI")
        self.qa_response_box.show()
        self.qa_response_box.setText(f"<b>💡 {engine}:</b>\n{ans}")
        if not self.preview_text.toPlainText() or "💡" in self.preview_text.toPlainText():
            self.preview_text.setPlainText(ans)
        self.set_active_tab(0)

