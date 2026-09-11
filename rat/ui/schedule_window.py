"""
rat.ui.schedule_window — Aesthetic Native macOS Club Timetable Compositor Window.
Features a "chill chill" pastel design, interactive member toggles, instant availability heatmap,
and 1-click sync to Apple Calendar / Zalo / Messenger.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import QPoint, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from rat.timetable.compositor import TimetableCompositor, availability_to_color
from rat.timetable.data import load_club_members, save_club_members
from rat.timetable.model import DAYS, SHIFTS, GoldenWindow, MemberSchedule, ShiftAvailability

logger = logging.getLogger("rat.ui.schedule_window")


CHILL_STYLE = """
QMainWindow {
    background-color: #fdfbf7;
}

QWidget#CentralWidget {
    background-color: #fdfbf7;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif;
}

/* Header */
QFrame#HeaderCard {
    background-color: #ffffff;
    border: 1px solid #f1ece1;
    border-radius: 16px;
    padding: 16px 20px;
}

QLabel#HeaderTitle {
    font-size: 20px;
    font-weight: 700;
    color: #292524;
}

QLabel#HeaderSubtitle {
    font-size: 13px;
    color: #78716c;
    margin-top: 2px;
}

/* Golden Highlights Carousel */
QFrame#GoldenHighlightsBar {
    background-color: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 12px;
    padding: 8px 14px;
}

QLabel#GoldenHighlightsLabel {
    font-size: 12px;
    font-weight: 600;
    color: #166534;
}

/* Member Chips */
QFrame#MemberFilterCard {
    background-color: #ffffff;
    border: 1px solid #f1ece1;
    border-radius: 14px;
    padding: 10px 16px;
}

QPushButton.MemberChip {
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    border: 1px solid #e7e5e4;
    background-color: #fafaf9;
    color: #57534e;
}

QPushButton.MemberChip:hover {
    background-color: #f5f5f4;
    border-color: #d6d3d1;
}

QPushButton.MemberChip[active="true"] {
    background-color: #e0f2fe;
    color: #0369a1;
    border: 1px solid #7dd3fc;
}

QPushButton.MemberChip[active="false"] {
    background-color: #f5f5f4;
    color: #a8a29e;
    border: 1px dashed #d6d3d1;
    text-decoration: line-through;
}

/* Timetable Grid Container */
QFrame#GridContainer {
    background-color: #ffffff;
    border: 1px solid #f1ece1;
    border-radius: 16px;
    padding: 14px;
}

QLabel.DayHeader {
    font-size: 13px;
    font-weight: 700;
    color: #44403c;
    padding: 6px 4px;
    qproperty-alignment: AlignCenter;
}

QLabel.ShiftHeader {
    font-size: 12px;
    font-weight: 600;
    color: #57534e;
    padding: 6px 8px;
    background-color: #fafaf9;
    border-radius: 8px;
    border: 1px solid #f5f5f4;
}

/* Timetable Shift Cell */
QFrame.ShiftCell {
    border-radius: 10px;
    border: 1px solid #e7e5e4;
    padding: 8px;
}

QFrame.ShiftCell:hover {
    border-width: 2px;
}

QLabel.CellBadge {
    font-size: 11px;
    font-weight: 700;
}

QLabel.CellDetail {
    font-size: 11px;
    margin-top: 2px;
}

/* Details Panel */
QFrame#DetailPanel {
    background-color: #ffffff;
    border: 1px solid #f1ece1;
    border-radius: 16px;
    padding: 16px;
}

QLabel#DetailTitle {
    font-size: 15px;
    font-weight: 700;
    color: #292524;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

/* Bottom Bar */
QFrame#BottomBar {
    background-color: #ffffff;
    border: 1px solid #f1ece1;
    border-radius: 14px;
    padding: 10px 18px;
}

QPushButton.ActionButton {
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid #e7e5e4;
    background-color: #fafaf9;
    color: #292524;
}

QPushButton.ActionButton:hover {
    background-color: #f5f5f4;
    border-color: #d6d3d1;
}

QPushButton.PrimaryActionButton {
    border-radius: 10px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid #16a34a;
    background-color: #16a34a;
    color: #ffffff;
}

QPushButton.PrimaryActionButton:hover {
    background-color: #15803d;
}
"""


class ShiftCellWidget(QFrame):
    """An aesthetic interactive cell representing availability for one Shift on one Day."""
    clicked = pyqtSignal(object)  # Emits ShiftAvailability

    def __init__(self, availability: ShiftAvailability, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.availability = availability
        self.setProperty("class", "ShiftCell")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(68)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        color_info = availability_to_color(availability.ratio)

        # 1. Status Badge
        self.badge_label = QLabel(f"{color_info['badge']}")
        self.badge_label.setProperty("class", "CellBadge")
        self.badge_label.setStyleSheet(f"color: {color_info['text']};")
        layout.addWidget(self.badge_label)

        # 2. Availability Ratio & Count
        tot = availability.total_active_members
        free_c = availability.free_count
        ratio_pct = int(availability.ratio * 100)

        if tot == 0:
            count_txt = "Chưa chọn ai"
        elif free_c == tot:
            count_txt = f"{free_c}/{tot} bạn rảnh"
        elif free_c == 0:
            count_txt = "Kẹt cả nhóm"
        else:
            count_txt = f"{free_c}/{tot} bạn ({ratio_pct}%)"

        self.count_label = QLabel(count_txt)
        self.count_label.setProperty("class", "CellDetail")
        self.count_label.setStyleSheet(f"color: {color_info['text']}; opacity: 0.9;")
        layout.addWidget(self.count_label)

        # Cell background styling
        self.setStyleSheet(f"""
            QFrame.ShiftCell {{
                background-color: {color_info['bg']};
                border: 1px solid {color_info['border']};
                border-radius: 10px;
            }}
            QFrame.ShiftCell:hover {{
                background-color: {color_info['bg_hover']};
                border: 2px solid {color_info['text']};
            }}
        """)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.availability)
        super().mousePressEvent(event)


class ScheduleCompositorWindow(QMainWindow):
    """Native macOS Standalone Timetable Compositor with a chill chill pastel aesthetic."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.members: List[MemberSchedule] = load_club_members()
        self.compositor = TimetableCompositor(self.members)
        self.highlight_golden_only = False
        self.selected_availability: Optional[ShiftAvailability] = None

        self._init_window()
        self._init_ui()
        self._refresh_all()

    def _init_window(self) -> None:
        self.setWindowTitle("rat — Ghép Lịch & Khung Giờ Vàng CLB (Chill Edition)")
        self.resize(1120, 760)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(CHILL_STYLE)

    def _init_ui(self) -> None:
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(14)

        # 1. Header Card
        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(16, 14, 16, 14)
        h_layout.setSpacing(6)

        title_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("🍵 Lịch Trình CLB Chill Chill")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Phối hợp thời khóa biểu sinh viên TDTU & Tự động săn 'Khung giờ vàng' không quạu")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        title_row.addLayout(title_box)

        title_row.addStretch()

        # Stats Badge
        self.stats_pill = QLabel("👥 Đang tải...")
        self.stats_pill.setStyleSheet("""
            background-color: #f5f5f4;
            color: #44403c;
            border-radius: 12px;
            padding: 6px 14px;
            font-size: 12px;
            font-weight: 600;
            border: 1px solid #e7e5e4;
        """)
        title_row.addWidget(self.stats_pill)

        h_layout.addLayout(title_row)

        # Golden Highlights Banner
        self.golden_bar = QFrame()
        self.golden_bar.setObjectName("GoldenHighlightsBar")
        gb_layout = QHBoxLayout(self.golden_bar)
        gb_layout.setContentsMargins(12, 8, 12, 8)
        gb_layout.setSpacing(10)

        self.golden_icon = QLabel("✨")
        self.golden_icon.setFont(QFont(".AppleSystemUIFont", 15))
        gb_layout.addWidget(self.golden_icon)

        self.golden_text = QLabel("Đang quét khung giờ vàng 100%...")
        self.golden_text.setObjectName("GoldenHighlightsLabel")
        self.golden_text.setWordWrap(True)
        gb_layout.addWidget(self.golden_text, 1)

        h_layout.addWidget(self.golden_bar)
        main_layout.addWidget(header_card)

        # 2. Member Selector Card
        member_card = QFrame()
        member_card.setObjectName("MemberFilterCard")
        m_layout = QHBoxLayout(member_card)
        m_layout.setContentsMargins(14, 8, 14, 8)
        m_layout.setSpacing(10)

        m_label = QLabel("👥 Chọn thành viên:")
        m_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #57534e;")
        m_layout.addWidget(m_label)

        self.member_chips_layout = QHBoxLayout()
        self.member_chips_layout.setSpacing(8)
        m_layout.addLayout(self.member_chips_layout)

        m_layout.addStretch()

        btn_all = QPushButton("Tất cả")
        btn_all.setProperty("class", "ActionButton")
        btn_all.setFixedHeight(28)
        btn_all.clicked.connect(self._select_all_members)
        m_layout.addWidget(btn_all)

        btn_clear = QPushButton("Bỏ hết")
        btn_clear.setProperty("class", "ActionButton")
        btn_clear.setFixedHeight(28)
        btn_clear.clicked.connect(self._clear_all_members)
        m_layout.addWidget(btn_clear)

        main_layout.addWidget(member_card)

        # 3. Middle Area: Timetable Grid + Quick Details Drawer
        middle_splitter = QSplitter(Qt.Orientation.Horizontal)
        middle_splitter.setChildrenCollapsible(False)

        # Grid Container
        grid_container = QFrame()
        grid_container.setObjectName("GridContainer")
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.grid_layout.setSpacing(8)

        grid_scroll = QScrollArea()
        grid_scroll.setWidgetResizable(True)
        grid_scroll.setWidget(grid_container)
        middle_splitter.addWidget(grid_scroll)

        # Detail Panel (Right Sidebar)
        self.detail_panel = QFrame()
        self.detail_panel.setObjectName("DetailPanel")
        self.detail_panel.setMinimumWidth(300)
        self.detail_panel.setMaximumWidth(360)
        dp_layout = QVBoxLayout(self.detail_panel)
        dp_layout.setContentsMargins(16, 16, 16, 16)
        dp_layout.setSpacing(12)

        self.detail_title = QLabel("🔍 Chi Tiết Ca Học")
        self.detail_title.setObjectName("DetailTitle")
        dp_layout.addWidget(self.detail_title)

        self.detail_sub = QLabel("Bấm vào một ô bất kỳ trong bảng để xem ai rảnh, ai bận học môn gì nhé!")
        self.detail_sub.setStyleSheet("font-size: 12px; color: #78716c;")
        self.detail_sub.setWordWrap(True)
        dp_layout.addWidget(self.detail_sub)

        # Scrollable content for details
        self.detail_content_scroll = QScrollArea()
        self.detail_content_scroll.setWidgetResizable(True)
        self.detail_content_widget = QWidget()
        self.detail_content_layout = QVBoxLayout(self.detail_content_widget)
        self.detail_content_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_content_layout.setSpacing(10)
        self.detail_content_scroll.setWidget(self.detail_content_widget)
        dp_layout.addWidget(self.detail_content_scroll, 1)

        middle_splitter.addWidget(self.detail_panel)
        middle_splitter.setStretchFactor(0, 3)
        middle_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(middle_splitter, 1)

        # 4. Bottom Actions Bar
        bottom_bar = QFrame()
        bottom_bar.setObjectName("BottomBar")
        bb_layout = QHBoxLayout(bottom_bar)
        bb_layout.setContentsMargins(14, 8, 14, 8)
        bb_layout.setSpacing(12)

        self.chk_golden_only = QCheckBox("🌿 Chỉ tô đậm Khung giờ vàng (≥80% rảnh)")
        self.chk_golden_only.setStyleSheet("font-size: 12px; font-weight: 600; color: #44403c;")
        self.chk_golden_only.toggled.connect(self._toggle_golden_only)
        bb_layout.addWidget(self.chk_golden_only)

        bb_layout.addStretch()

        btn_copy = QPushButton("📋 Sao chép cho nhóm chat")
        btn_copy.setProperty("class", "ActionButton")
        btn_copy.clicked.connect(self._copy_chat_message)
        bb_layout.addWidget(btn_copy)

        btn_ics = QPushButton("🍏 Xuất file Apple / Google Calendar (.ics)")
        btn_ics.setProperty("class", "PrimaryActionButton")
        btn_ics.clicked.connect(self._export_ics)
        bb_layout.addWidget(btn_ics)

        main_layout.addWidget(bottom_bar)

    def _refresh_all(self) -> None:
        """Recalculates availability and redraws member chips, golden highlights, and grid."""
        try:
            self._render_member_chips()
            self._render_golden_highlights()
            self._render_grid()
            if self.selected_availability:
                self._render_details(self.selected_availability)
            else:
                self._render_default_details()
        except Exception as e:
            logger.error(f"Error refreshing schedule compositor: {e}", exc_info=True)

    def _render_member_chips(self) -> None:
        """Renders interactive toggle chips for each member."""
        # Clear existing
        while self.member_chips_layout.count():
            item = self.member_chips_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        active_count = len(self.compositor.active_members)
        total_count = len(self.members)
        self.stats_pill.setText(f"👥 {active_count}/{total_count} bạn tham gia")

        for m in self.members:
            btn = QPushButton(f"{'✓ ' if m.active else '✕ '}{m.name}")
            btn.setProperty("class", "MemberChip")
            btn.setProperty("active", "true" if m.active else "false")
            btn.clicked.connect(lambda checked, mid=m.id: self._on_toggle_member(mid))
            self.member_chips_layout.addWidget(btn)

    def _on_toggle_member(self, member_id: str) -> None:
        self.compositor.toggle_member(member_id)
        save_club_members(self.members)
        self._refresh_all()

    def _select_all_members(self) -> None:
        for m in self.members:
            m.active = True
        save_club_members(self.members)
        self._refresh_all()

    def _clear_all_members(self) -> None:
        for m in self.members:
            m.active = False
        save_club_members(self.members)
        self._refresh_all()

    def _render_golden_highlights(self) -> None:
        """Extracts and renders the best golden windows in the header banner."""
        active = self.compositor.active_members
        if not active:
            self.golden_text.setText("⚠️ Chưa có bạn nào được chọn để tìm khung giờ vàng.")
            return

        windows_100 = self.compositor.find_golden_windows(min_ratio=1.0)
        windows_80 = [w for w in self.compositor.find_golden_windows(min_ratio=0.8) if w.free_count < len(active)]

        parts = []
        if windows_100:
            for w in windows_100[:3]:  # Top 3
                parts.append(f"<b>🌿 {w.day_name}</b> ({w.time_range}) • 100% Rảnh")
        if windows_80:
            for w in windows_80[:2]:
                parts.append(f"<b>☀️ {w.day_name}</b> ({w.time_range}) • {w.free_count}/{len(active)} Rảnh")

        if parts:
            html = "  |  ".join(parts)
            self.golden_text.setText(f"✨ <b>Khung giờ vàng gợi ý:</b>  {html}")
        else:
            self.golden_text.setText("🌿 Tuần này không có khung giờ nào cả nhóm cùng rảnh hoàn toàn. Hãy thử tắt bớt thành viên vắng!")

    def _render_grid(self) -> None:
        """Renders the 7-day x 5-shift availability matrix."""
        # Clear existing grid items
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # Row 0: Headers (Corner + 7 Days)
        corner_lbl = QLabel("Ca \\ Thứ")
        corner_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #a8a29e; qproperty-alignment: AlignCenter;")
        self.grid_layout.addWidget(corner_lbl, 0, 0)

        for col_idx, (day_code, day_name, _) in enumerate(DAYS, 1):
            day_lbl = QLabel(day_name)
            day_lbl.setProperty("class", "DayHeader")
            self.grid_layout.addWidget(day_lbl, 0, col_idx)

        # Compute Shift Matrix
        shift_matrix = self.compositor.compute_shift_matrix()

        # Rows 1 to 5: Shifts
        for row_idx, (shift_id, shift_name, time_range, (sp, ep)) in enumerate(SHIFTS, 1):
            # Shift Header Column
            shift_lbl = QLabel(f"<b>{shift_name}</b><br><span style='font-size:10px; color:#78716c;'>{time_range}</span>")
            shift_lbl.setProperty("class", "ShiftHeader")
            shift_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(shift_lbl, row_idx, 0)

            # Columns 1 to 7: Days
            for col_idx, (day_code, day_name, _) in enumerate(DAYS, 1):
                availability = shift_matrix[day_code][shift_id]

                # If highlight golden only is on and ratio < 0.8, mute the cell
                cell = ShiftCellWidget(availability)
                cell.clicked.connect(self._on_cell_clicked)
                self.grid_layout.addWidget(cell, row_idx, col_idx)

    def _on_cell_clicked(self, availability: ShiftAvailability) -> None:
        self.selected_availability = availability
        self._render_details(availability)

    def _render_default_details(self) -> None:
        """Renders welcome placeholder in the details panel."""
        self._clear_detail_layout()
        lbl = QLabel("✨ Chọn một ca học trên bảng để xem chi tiết lịch từng thành viên.")
        lbl.setStyleSheet("color: #78716c; font-size: 12px; padding: 20px 0;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_content_layout.addWidget(lbl)

    def _clear_detail_layout(self) -> None:
        while self.detail_content_layout.count():
            item = self.detail_content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _render_details(self, a: ShiftAvailability) -> None:
        """Renders comprehensive member free/busy details for the selected shift."""
        self._clear_detail_layout()

        self.detail_title.setText(f"📍 {a.day_name} — {a.shift_name}")
        self.detail_sub.setText(f"🕒 {a.time_range} (Tiết {a.start_period} ➔ {a.end_period})")

        # 1. Availability Summary Badge
        color_info = availability_to_color(a.ratio)
        badge_box = QFrame()
        badge_box.setStyleSheet(f"""
            background-color: {color_info['bg']};
            border: 1px solid {color_info['border']};
            border-radius: 10px;
            padding: 10px;
        """)
        bb_layout = QVBoxLayout(badge_box)
        bb_layout.setContentsMargins(10, 8, 10, 8)

        lbl_status = QLabel(f"{color_info['badge']} • {a.free_count}/{a.total_active_members} bạn rảnh")
        lbl_status.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {color_info['text']};")
        bb_layout.addWidget(lbl_status)

        lbl_desc = QLabel(color_info["desc"])
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {color_info['text']}; opacity: 0.85;")
        bb_layout.addWidget(lbl_desc)

        self.detail_content_layout.addWidget(badge_box)

        # 2. Free Members List
        lbl_free_title = QLabel(f"🌿 Các bạn rảnh ({len(a.free_members)}):")
        lbl_free_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #166534; margin-top: 6px;")
        self.detail_content_layout.addWidget(lbl_free_title)

        if a.free_members:
            for name in a.free_members:
                row = QLabel(f"• {name}")
                row.setStyleSheet("font-size: 12px; color: #292524; padding-left: 8px;")
                self.detail_content_layout.addWidget(row)
        else:
            none_lbl = QLabel("• Không có bạn nào rảnh trong ca này.")
            none_lbl.setStyleSheet("font-size: 11px; color: #a8a29e; font-style: italic; padding-left: 8px;")
            self.detail_content_layout.addWidget(none_lbl)

        # 3. Busy Members List (with Course and Room details!)
        lbl_busy_title = QLabel(f"📚 Các bạn bận học ({len(a.busy_details)}):")
        lbl_busy_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #991b1b; margin-top: 10px;")
        self.detail_content_layout.addWidget(lbl_busy_title)

        if a.busy_details:
            for b in a.busy_details:
                card = QFrame()
                card.setStyleSheet("""
                    background-color: #fff1f2;
                    border: 1px solid #fecdd3;
                    border-radius: 8px;
                    padding: 8px 10px;
                """)
                c_layout = QVBoxLayout(card)
                c_layout.setContentsMargins(8, 6, 8, 6)
                c_layout.setSpacing(2)

                m_name = QLabel(f"<b>{b['member']}</b>")
                m_name.setStyleSheet("font-size: 12px; color: #9f1239;")
                c_layout.addWidget(m_name)

                c_info = QLabel(f"📖 {b['course']}")
                c_info.setStyleSheet("font-size: 11px; color: #475569;")
                c_info.setWordWrap(True)
                c_layout.addWidget(c_info)

                sub_info = QLabel(f"📍 Phòng {b['room']}  •  {b['periods']}")
                sub_info.setStyleSheet("font-size: 10px; color: #64748b;")
                c_layout.addWidget(sub_info)

                self.detail_content_layout.addWidget(card)
        else:
            none_busy = QLabel("• Tuyệt vời! Không ai bị kẹt lịch.")
            none_busy.setStyleSheet("font-size: 11px; color: #166534; font-style: italic; padding-left: 8px;")
            self.detail_content_layout.addWidget(none_busy)

        self.detail_content_layout.addStretch()

    def _toggle_golden_only(self, checked: bool) -> None:
        self.highlight_golden_only = checked
        self._render_grid()

    def _copy_chat_message(self) -> None:
        """Copies formatted Zalo / Messenger announcement to system clipboard."""
        try:
            msg = self.compositor.generate_chat_message()
            QApplication.clipboard().setText(msg)
            QMessageBox.information(
                self,
                "rat — Đã sao chép",
                "✨ Đã sao chép lịch rảnh CLB vào bộ nhớ tạm!\nBạn có thể dán (Cmd+V) ngay vào nhóm chat Zalo hoặc Messenger."
            )
        except Exception as e:
            logger.error(f"Error copying chat message: {e}", exc_info=True)

    def _export_ics(self) -> None:
        """Exports iCalendar .ics file and reveals it in Finder or opens Calendar."""
        try:
            default_path = str(Path.home() / "Downloads" / "club_free_slots.ics")
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Lưu file lịch iCalendar (.ics)",
                default_path,
                "iCalendar Files (*.ics)"
            )
            if not filepath:
                return

            ics_content = self.compositor.generate_ics_content(min_ratio=0.8)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(ics_content)

            reply = QMessageBox.question(
                self,
                "rat — Xuất Lịch Thành Công",
                f"✅ Đã xuất file lịch thành công tại:\n{filepath}\n\nBạn có muốn mở ngay bằng Apple Calendar để đồng bộ không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                subprocess.run(["open", filepath], check=False)
        except Exception as e:
            logger.error(f"Error exporting ICS file: {e}", exc_info=True)
            QMessageBox.critical(self, "Lỗi xuất file", f"Không thể xuất file: {e}")

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)
