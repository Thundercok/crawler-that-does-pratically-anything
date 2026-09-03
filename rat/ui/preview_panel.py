"""
rat.ui.preview_panel — 100% Genuine Apple macOS Light Theme Quick Look & Minimalist CoT Inspector.
Features:
- Pure Apple macOS Light Theme Quick Look
- Ultra Minimalist Segmented Switcher: [ 📄 Xem trước | 🧠 Suy luận AI ]
- Clean Vertical Reasoning Trace Timeline
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
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
    ".docx": "Tài liệu Microsoft Word",
    ".doc": "Tài liệu Microsoft Word",
    ".pdf": "Tài liệu PDF",
    ".xlsx": "Bảng tính Microsoft Excel",
    ".xls": "Bảng tính Microsoft Excel",
    ".csv": "Tệp dữ liệu CSV",
    ".pptx": "Bản trình chiếu PowerPoint",
    ".ppt": "Bản trình chiếu PowerPoint",
    ".py": "Mã nguồn Python",
    ".js": "Mã nguồn JavaScript",
    ".ts": "Mã nguồn TypeScript",
    ".html": "Trang Web HTML",
    ".css": "Tệp định dạng CSS",
    ".json": "Tệp cấu hình JSON",
    ".sh": "Tập lệnh Shell Script",
    ".sql": "Mã nguồn cơ sở dữ liệu SQL",
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
    """Pure Apple macOS Light Theme Quick Look & CoT Inspector."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("PreviewPanel")
        self.current_item: Optional[SearchResultItem] = None
        self.current_trace: Optional[ReasoningTrace] = None
        self.current_plan: Optional[Dict[str, Any]] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # 1. Hero Header Section
        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        header_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.badge_label = QLabel("FILE")
        self.badge_label.setStyleSheet("""
            background-color: #007aff;
            color: #ffffff;
            font-weight: 700;
            font-size: 11px;
            border-radius: 8px;
        """)
        self.badge_label.setFixedSize(38, 38)
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        self.name_label = QLabel("Chi tiết tệp tin")
        self.name_label.setStyleSheet("color: #1c1c1e; font-size: 14.5px; font-weight: 600;")
        self.name_label.setWordWrap(True)

        self.type_desc_label = QLabel("")
        self.type_desc_label.setStyleSheet("color: #636366; font-size: 11px;")

        title_col.addWidget(self.name_label)
        title_col.addWidget(self.type_desc_label)

        header_row.addWidget(self.badge_label)
        header_row.addLayout(title_col, 1)
        layout.addLayout(header_row)

        # 2. Metadata Info Bar (Light Mode)
        self.meta_card = QFrame()
        self.meta_card.setStyleSheet("""
            QFrame {
                background-color: #f2f2f7;
                border-radius: 6px;
                padding: 4px 8px;
                border: 1px solid #e5e5ea;
            }
        """)
        meta_card_layout = QVBoxLayout(self.meta_card)
        meta_card_layout.setContentsMargins(6, 4, 6, 4)
        meta_card_layout.setSpacing(2)

        self.meta_info_label = QLabel("")
        self.meta_info_label.setStyleSheet("color: #3a3a3c; font-size: 11px;")
        self.meta_info_label.setWordWrap(True)
        meta_card_layout.addWidget(self.meta_info_label)
        layout.addWidget(self.meta_card)

        # 3. Context Reason Box (Light Pastel Blue)
        self.reason_box = QFrame()
        self.reason_box.setStyleSheet("""
            QFrame {
                background-color: #e0f2fe;
                border-radius: 6px;
                padding: 5px 8px;
                border: 1px solid #bae6fd;
            }
        """)
        reason_layout = QVBoxLayout(self.reason_box)
        reason_layout.setContentsMargins(6, 3, 6, 3)
        reason_layout.setSpacing(2)

        self.reason_title = QLabel("💡 Khớp ngữ cảnh AI:")
        self.reason_title.setStyleSheet("color: #0284c7; font-size: 11px; font-weight: 600;")
        self.reason_text = QLabel("")
        self.reason_text.setStyleSheet("color: #0369a1; font-size: 11.5px; line-height: 1.35;")
        self.reason_text.setWordWrap(True)

        reason_layout.addWidget(self.reason_title)
        reason_layout.addWidget(self.reason_text)
        layout.addWidget(self.reason_box)

        # 4. Minimalist Segmented Switcher Row (26px height)
        switch_row = QHBoxLayout()
        switch_row.setSpacing(6)
        switch_row.setContentsMargins(0, 2, 0, 2)

        self.seg_container = QFrame()
        self.seg_container.setStyleSheet("""
            QFrame {
                background-color: #e5e5ea;
                border-radius: 6px;
            }
            QPushButton {
                border: none;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 500;
                color: #636366;
                background-color: transparent;
            }
            QPushButton:hover {
                color: #1c1c1e;
            }
            QPushButton[selected="true"] {
                background-color: #ffffff;
                color: #1c1c1e;
                font-weight: 600;
            }
        """)
        seg_layout = QHBoxLayout(self.seg_container)
        seg_layout.setContentsMargins(2, 2, 2, 2)
        seg_layout.setSpacing(2)

        self.btn_tab_preview = QPushButton("📄 Xem trước")
        self.btn_tab_preview.setProperty("selected", "true")
        self.btn_tab_preview.clicked.connect(lambda: self.set_active_tab(0))

        self.btn_tab_cot = QPushButton("🧠 Suy luận AI")
        self.btn_tab_cot.setProperty("selected", "false")
        self.btn_tab_cot.clicked.connect(lambda: self.set_active_tab(1))

        seg_layout.addWidget(self.btn_tab_preview)
        seg_layout.addWidget(self.btn_tab_cot)

        switch_row.addWidget(self.seg_container)
        switch_row.addStretch()
        layout.addLayout(switch_row)

        # 5. Stacked Pages: [Page 0: Preview Text | Page 1: CoT Timeline]
        self.stack = QStackedWidget()

        # Page 0: Quick Look
        self.preview_text = QTextEdit()
        self.preview_text.setObjectName("PreviewContent")
        self.preview_text.setReadOnly(True)
        self.preview_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 6px;
                color: #1c1c1e;
                font-size: 12px;
                line-height: 1.4;
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
        self.cot_content_layout.setContentsMargins(4, 4, 4, 4)
        self.cot_content_layout.setSpacing(8)
        self.cot_scroll.setWidget(self.cot_content_widget)

        self.stack.addWidget(self.cot_scroll)

        layout.addWidget(self.stack, 1)

        # Default empty timeline message
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

        # Refresh style
        self.btn_tab_preview.style().unpolish(self.btn_tab_preview)
        self.btn_tab_preview.style().polish(self.btn_tab_preview)
        self.btn_tab_cot.style().unpolish(self.btn_tab_cot)
        self.btn_tab_cot.style().polish(self.btn_tab_cot)

    def _render_empty_cot(self) -> None:
        """Render friendly placeholder when no search query has been run yet."""
        while self.cot_content_layout.count():
            item = self.cot_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        empty_label = QLabel("Chưa có chuỗi suy luận.\nHãy nhập câu hỏi tìm kiếm ở ô phía trên.")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("color: #8e8e93; font-size: 11.5px; padding: 40px 10px;")
        self.cot_content_layout.addWidget(empty_label)
        self.cot_content_layout.addStretch()

    def set_reasoning_trace(
        self,
        trace: Optional[ReasoningTrace],
        plan: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update CoT reasoning trace and render clean minimalist timeline."""
        self.current_trace = trace
        self.current_plan = plan

        if not trace or not trace.steps:
            self.btn_tab_cot.setText("🧠 Suy luận AI")
            self._render_empty_cot()
            return

        conf_pct = int(trace.final_confidence * 100)
        self.btn_tab_cot.setText(f"🧠 Suy luận AI ({conf_pct}%)")

        # Clear existing timeline cards
        while self.cot_content_layout.count():
            item = self.cot_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. Compact Header Summary Card
        status_text = "✅ ĐỦ ĐIỀU KIỆN" if trace.is_sufficient else "⚠️ PHẦN NÀO"
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
        h_layout.setContentsMargins(6, 4, 6, 4)
        h_layout.setSpacing(6)

        lbl_status = QLabel(f"<b>{status_text}</b> ({conf_pct}%)")
        lbl_status.setStyleSheet(f"color: {status_color}; font-size: 11.5px;")
        h_layout.addWidget(lbl_status)

        h_layout.addStretch()

        lbl_latency = QLabel(f"⚡ {trace.total_latency_ms}ms • {len(trace.steps)} bước")
        lbl_latency.setStyleSheet("color: #636366; font-size: 11px;")
        h_layout.addWidget(lbl_latency)

        self.cot_content_layout.addWidget(header_card)

        # 2. Render Minimalist Steps
        phase_icons = {
            "decompose": ("🔍", "Phân rã mục tiêu (MFQD)", "#0284c7", "#f0f9ff", "#e0f2fe"),
            "retrieve": ("⚡", "Truy xuất đa luồng (M-RRF)", "#7c3aed", "#faf5ff", "#f3e8ff"),
            "evaluate": ("🎯", "Đánh giá thông tin", "#059669", "#ecfdf5", "#d1fae5"),
            "correct": ("🛠️", "Tự động sửa lỗi (CRAG)", "#ea580c", "#fff7ed", "#ffedd5"),
            "rerank": ("📊", "Tái xếp hạng & Bằng chứng", "#475569", "#f8fafc", "#f1f5f9"),
            "synthesize": ("💬", "Tổng hợp tri thức", "#2563eb", "#eff6ff", "#dbeafe"),
        }

        for step in trace.steps:
            icon, title_text, col_accent, col_bg, col_border = phase_icons.get(
                step.phase, ("🔹", step.phase.upper(), "#48484a", "#f2f2f7", "#e5e5ea")
            )

            step_card = QFrame()
            step_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {col_bg};
                    border: 1px solid {col_border};
                    border-radius: 6px;
                    padding: 4px 8px;
                }}
            """)
            s_layout = QVBoxLayout(step_card)
            s_layout.setContentsMargins(6, 4, 6, 4)
            s_layout.setSpacing(2)

            # Step title row
            title_row = QHBoxLayout()
            title_row.setSpacing(6)
            title_lbl = QLabel(f"{icon} <b>{title_text}</b>")
            title_lbl.setStyleSheet(f"color: {col_accent}; font-size: 11.5px;")
            title_row.addWidget(title_lbl)
            title_row.addStretch()

            step_ms = QLabel(f"{step.latency_ms}ms")
            step_ms.setStyleSheet("color: #8e8e93; font-size: 10.5px;")
            title_row.addWidget(step_ms)
            s_layout.addLayout(title_row)

            # Clean Thought / Observation text (minimalist, 1-2 lines)
            obs_text = step.observation if step.observation else step.thought
            if obs_text:
                desc_lbl = QLabel(obs_text)
                desc_lbl.setStyleSheet("color: #3a3a3c; font-size: 11px; line-height: 1.35;")
                desc_lbl.setWordWrap(True)
                s_layout.addWidget(desc_lbl)

            self.cot_content_layout.addWidget(step_card)

        self.cot_content_layout.addStretch()

    def set_item(self, item: Optional[SearchResultItem]) -> None:
        """Update file details and preview content."""
        self.current_item = item
        if not item:
            self.badge_label.setText("FILE")
            self.badge_label.setStyleSheet("background-color: #e5e5ea; color: #636366; font-weight: 700; font-size: 11px; border-radius: 8px;")
            self.name_label.setText("Chọn một tệp để xem chi tiết")
            self.type_desc_label.setText("")
            self.meta_card.hide()
            self.reason_box.hide()
            self.preview_text.setPlainText("")
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
        self.type_desc_label.setText(f"{desc}  •  {item.file_size_formatted}")

        # Metadata Card
        p = item.file_path
        if len(p) > 56:
            p = "..." + p[-52:]
        self.meta_card.show()
        self.meta_info_label.setText(f"📁 {p}\n🕒 Sửa đổi lần cuối: {item.modified_formatted}")

        # Reason Card (Only show if score > 10)
        score_val = int(getattr(item, "score", 0))
        if score_val > 10:
            self.reason_box.show()
            self.reason_text.setText(f"{item.explanation}  •  Độ khớp: {score_val}%")
        else:
            self.reason_box.hide()

        snippet_text = item.snippet if item.snippet else "(Không có nội dung trích đoạn xem trước)"
        if ext_clean in [".png", ".jpg", ".jpeg", ".webp"]:
            if "Visual Concepts" in snippet_text or "Detected Text" in snippet_text:
                self.preview_text.setPlainText(snippet_text)
            else:
                self.preview_text.setPlainText(f"🖼️ Hình ảnh: {item.file_name}\n\n{snippet_text}")
        else:
            self.preview_text.setPlainText(snippet_text)

    def set_qa_answer(self, qa_res: Dict[str, Any]) -> None:
        """Display QA answer in the preview area."""
        ans = qa_res.get("answer", "")
        if ans:
            self.preview_text.setPlainText(ans)
            self.set_active_tab(0)

