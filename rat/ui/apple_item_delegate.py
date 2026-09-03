"""
rat.ui.apple_item_delegate — 100% Genuine Apple macOS Light Theme List Item Delegate.
Renders authentic Apple Dog-Ear document icons, typography hierarchy, and smooth selection.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QModelIndex, QRectF, QSize, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import QStyle, QStyleOptionViewItem, QStyledItemDelegate

from rat.engine.reranker import SearchResultItem
from rat.ui.theme import get_ext_badge_info


class AppleSpotlightDelegate(QStyledItemDelegate):
    """
    Native QPainter delegate that renders macOS Spotlight list rows with
    authentic Apple Dog-Ear document icons, typography hierarchy, and zero layout clipping.
    """

    def __init__(self, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self.row_height = 56

        # Standard Apple Typography
        self.title_font = QFont(".AppleSystemUIFont", 13)
        self.title_font.setWeight(QFont.Weight.DemiBold)

        self.sub_font = QFont(".AppleSystemUIFont", 11)
        self.sub_font.setWeight(QFont.Weight.Normal)

        self.badge_font = QFont(".AppleSystemUIFont", 9)
        self.badge_font.setWeight(QFont.Weight.Bold)

        self.meta_font = QFont(".AppleSystemUIFont", 10)
        self.meta_font.setWeight(QFont.Weight.Medium)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), self.row_height)

    def _draw_apple_document_icon(self, painter: QPainter, rect: QRectF, bg_color_hex: str, label_text: str) -> None:
        """Draw an authentic Apple macOS Dog-Ear folded corner document icon."""
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        fold_size = 8.0

        # Document Path with folded top-right corner
        path = QPainterPath()
        path.moveTo(x + 4, y)
        path.lineTo(x + w - fold_size, y)
        path.lineTo(x + w, y + fold_size)
        path.lineTo(x + w, y + h - 4)
        path.quadTo(x + w, y + h, x + w - 4, y + h)
        path.lineTo(x + 4, y + h)
        path.quadTo(x, y + h, x, y + h - 4)
        path.lineTo(x, y + 4)
        path.quadTo(x, y, x + 4, y)
        path.closeSubpath()

        # Gradient fill
        base_color = QColor(bg_color_hex)
        grad = QLinearGradient(x, y, x, y + h)
        grad.setColorAt(0.0, base_color.lighter(112))
        grad.setColorAt(1.0, base_color.darker(108))

        painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

        # Draw the folded corner flap
        flap = QPainterPath()
        flap.moveTo(x + w - fold_size, y)
        flap.lineTo(x + w - fold_size, y + fold_size)
        flap.lineTo(x + w, y + fold_size)
        flap.closeSubpath()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(base_color.lighter(135)))
        painter.drawPath(flap)

        # Label text inside the document icon
        painter.setFont(self.badge_font)
        painter.setPen(QColor("#ffffff"))
        text_rect = QRectF(x, y + 6, w - 2, h - 6)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, label_text)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        item: Optional[SearchResultItem] = index.data(Qt.ItemDataRole.UserRole)
        if not item:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        rect = option.rect
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hover = bool(option.state & QStyle.StateFlag.State_MouseOver)

        # 1. Background Selection State (Apple Light Blue Frost)
        bg_rect = QRectF(rect.x() + 4, rect.y() + 2, rect.width() - 8, rect.height() - 4)
        if is_selected:
            painter.setPen(QPen(QColor("#007aff"), 1))
            painter.setBrush(QBrush(QColor("#e8edf7")))
            painter.drawRoundedRect(bg_rect, 8, 8)
        elif is_hover:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 10)))
            painter.drawRoundedRect(bg_rect, 8, 8)

        # 2. STT (Số Thứ Tự: 1, 2, 3...)
        stt_num = index.row() + 1
        stt_rect = QRectF(rect.x() + 6, rect.y(), 26, rect.height())
        painter.setFont(self.meta_font)
        painter.setPen(QColor("#007aff") if is_selected else QColor("#8e8e93"))
        painter.drawText(stt_rect, Qt.AlignmentFlag.AlignCenter, str(stt_num))

        # 3. Apple Dog-Ear Document Icon (30x36px)
        badge_info = get_ext_badge_info(getattr(item, "file_ext", ""))
        doc_rect = QRectF(rect.x() + 36, rect.y() + (rect.height() - 36) / 2, 30, 36)
        self._draw_apple_document_icon(painter, doc_rect, badge_info["bg"], badge_info["label"])

        # Text Area Boundaries
        text_x = rect.x() + 76
        avail_width = rect.width() - 170

        # 4. File Title (Apple Dark Black #1c1c1e, DemiBold, 13px)
        file_name = getattr(item, "file_name", "") or "Không rõ tên"
        painter.setFont(self.title_font)
        painter.setPen(QColor("#1c1c1e"))
        fm_title = QFontMetrics(self.title_font)
        elided_title = fm_title.elidedText(file_name, Qt.TextElideMode.ElideRight, int(avail_width))
        painter.drawText(int(text_x), int(rect.y() + 22), elided_title)

        # 5. Folder Path & Relative Modified Time Subtitle (Apple Gray #636366, 11px)
        file_path = getattr(item, "file_path", "") or ""
        mod_time = getattr(item, "modified_formatted", "") or ""
        sub_text = f"{file_path}  •  {mod_time}" if mod_time else file_path
        painter.setFont(self.sub_font)
        painter.setPen(QColor("#636366"))
        fm_sub = QFontMetrics(self.sub_font)
        elided_path = fm_sub.elidedText(sub_text, Qt.TextElideMode.ElideMiddle, int(avail_width))
        painter.drawText(int(text_x), int(rect.y() + 41), elided_path)

        # 6. Right Tag (Score % or File Size)
        score_val = int(getattr(item, "score", 0))
        if score_val > 10:
            tag_str = f"{score_val}%"
            bg_pill = QColor("#e0f2fe")
            fg_pill = QColor("#0284c7")
            border_pill = QColor("#bae6fd")
        else:
            tag_str = getattr(item, "file_size_formatted", "") or ""
            bg_pill = QColor("#f2f2f7")
            fg_pill = QColor("#636366")
            border_pill = QColor("#e5e5ea")

        if tag_str:
            tag_width = 48
            tag_x = rect.x() + rect.width() - tag_width - 12
            tag_rect = QRectF(tag_x, rect.y() + (rect.height() - 20) / 2, tag_width, 20)

            painter.setPen(QPen(border_pill, 1))
            painter.setBrush(QBrush(bg_pill))
            painter.drawRoundedRect(tag_rect, 5, 5)

            painter.setFont(self.meta_font)
            painter.setPen(fg_pill)
            painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, tag_str)

        painter.restore()
