"""
rat.os.menu_bar — macOS Top Menu Bar (Status Item) Resident Controller.
Places a native status indicator on the macOS top bar for quick search, stats, and background control.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Callable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from rat.config import config
from rat.crawler.db import Database
from rat.crawler.indexer import Indexer

logger = logging.getLogger("rat.os.menu_bar")


def create_tray_pixmap() -> QPixmap:
    """Draw a clean, native macOS monochrome menu bar icon."""
    pixmap = QPixmap(22, 22)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw magnifying glass / rat silhouette icon
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#000000"))

    # Lens circle
    painter.drawEllipse(3, 3, 11, 11)
    # Clear inner
    painter.setBrush(QColor(Qt.GlobalColor.transparent))
    # Handle
    painter.setPen(QColor("#000000"))
    painter.drawLine(12, 12, 18, 18)
    painter.end()

    return pixmap


class SystemTrayManager:
    """Manages the macOS Menu Bar Status Item."""

    def __init__(
        self,
        on_open_spotlight: Optional[Callable[[], None]] = None,
        on_open_finder: Optional[Callable[[], None]] = None,
    ) -> None:
        self.on_open_spotlight = on_open_spotlight
        self.on_open_finder = on_open_finder
        self.tray_icon = QSystemTrayIcon()
        self.db = Database(config.db_path)
        self._init_tray()

    def _init_tray(self) -> None:
        # Create icon
        icon = QIcon(create_tray_pixmap())
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("rat — macOS Smart AI File Finder")

        # Create Menu
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                color: #1c1c1e;
                border: 1px solid #d1d1d6;
                border-radius: 8px;
                padding: 4px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 14px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #007aff;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #e5e5ea;
                margin: 4px 8px;
            }
        """)

        # Search Quick Actions
        action_spotlight = QAction("🔍 Tìm kiếm nhanh (⌥ + Space)", menu)
        if self.on_open_spotlight:
            action_spotlight.triggered.connect(self.on_open_spotlight)
        menu.addAction(action_spotlight)

        action_finder = QAction("📁 Mở AI Finder đầy đủ", menu)
        if self.on_open_finder:
            action_finder.triggered.connect(self.on_open_finder)
        menu.addAction(action_finder)

        menu.addSeparator()

        # Stats info item (disabled)
        stats = self.db.get_stats()
        size_mb = stats["total_size_bytes"] / (1024 * 1024)
        action_stats = QAction(f"📊 Đã lập chỉ mục: {stats['total_files']} tệp (~{size_mb:.1f} MB)", menu)
        action_stats.setEnabled(False)
        menu.addAction(action_stats)

        # Rescan action
        action_rescan = QAction("🔄 Quét lại kho dữ liệu ngay", menu)
        action_rescan.triggered.connect(self._trigger_rescan)
        menu.addAction(action_rescan)

        menu.addSeparator()

        # Quit
        action_quit = QAction("❌ Thoát RAT", menu)
        action_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(action_quit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
        logger.info("macOS System Tray resident item loaded.")

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.on_open_spotlight:
                self.on_open_spotlight()

    def _trigger_rescan(self) -> None:
        logger.info("Rescan triggered from Menu Bar tray.")
        indexer = Indexer(self.db)
        indexer.run_full_index()
        self.tray_icon.showMessage(
            "rat — Quét hoàn tất",
            "Đã cập nhật toàn bộ cơ sở dữ liệu tệp tin!",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
