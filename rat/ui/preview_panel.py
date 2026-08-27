"""
rat.ui.preview_panel — 100% Genuine Apple macOS Light Theme Quick Look Inspector.
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

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
    """Pure Apple macOS Light Theme Quick Look Inspector."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("PreviewPanel")
        self.current_item: Optional[SearchResultItem] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

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
        self.badge_label.setFixedSize(40, 40)
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        self.name_label = QLabel("Chi tiết tệp tin")
        self.name_label.setStyleSheet("color: #1c1c1e; font-size: 15px; font-weight: 600;")
        self.name_label.setWordWrap(True)

        self.type_desc_label = QLabel("")
        self.type_desc_label.setStyleSheet("color: #636366; font-size: 11.5px;")

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
                padding: 6px 10px;
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
                padding: 6px 10px;
                border: 1px solid #7dd3fc;
            }
        """)
        reason_layout = QVBoxLayout(self.reason_box)
        reason_layout.setContentsMargins(6, 4, 6, 4)
        reason_layout.setSpacing(2)

        self.reason_title = QLabel("💡 Khớp ngữ cảnh AI:")
        self.reason_title.setStyleSheet("color: #0284c7; font-size: 11px; font-weight: 600;")
        self.reason_text = QLabel("")
        self.reason_text.setStyleSheet("color: #0369a1; font-size: 12px; line-height: 1.4;")
        self.reason_text.setWordWrap(True)

        reason_layout.addWidget(self.reason_title)
        reason_layout.addWidget(self.reason_text)
        layout.addWidget(self.reason_box)

        # 4. Quick Look Content Area (Pure White Editor)
        preview_header = QLabel("📄 Xem trước nội dung (Quick Look):")
        preview_header.setStyleSheet("color: #636366; font-size: 11px; font-weight: 600; margin-top: 2px;")
        layout.addWidget(preview_header)

        self.preview_text = QTextEdit()
        self.preview_text.setObjectName("PreviewContent")
        self.preview_text.setReadOnly(True)
        self.preview_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.preview_text, 1)

    def set_item(self, item: Optional[SearchResultItem]) -> None:
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
            # Format visual headers nicely
            if "Visual Concepts" in snippet_text or "Detected Text" in snippet_text:
                self.preview_text.setPlainText(snippet_text)
            else:
                self.preview_text.setPlainText(f"🖼️ Hình ảnh: {item.file_name}\n\n{snippet_text}")
        else:
            self.preview_text.setPlainText(snippet_text)
