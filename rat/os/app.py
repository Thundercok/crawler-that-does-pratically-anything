"""
rat.os.app — Unified macOS Resident Application Controller.
Coordinates the Global Hotkey, Menu Bar Status Item, Floating Spotlight HUD,
Full AI Finder, and Background Filesystem Watcher in a unified zero-overhead loop.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

from rat.config import config
from rat.crawler.watcher import Watcher
from rat.os.hotkey import GlobalHotkeyManager
from rat.os.menu_bar import SystemTrayManager
from rat.ui.finder_window import FinderWindow
from rat.ui.spotlight_window import SpotlightWindow

logger = logging.getLogger("rat.os.app")


def activate_macos_app() -> None:
    """Ensure the Python GUI gains active foreground focus on macOS."""
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyRegular
        ns_app = NSApplication.sharedApplication()
        ns_app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        ns_app.activateIgnoringOtherApps_(True)
    except Exception:
        pass


class ResidentApplication:
    """Unified macOS Resident Background System."""

    def __init__(self, mode: str = "all") -> None:
        self.mode = mode
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setApplicationName("rat — macOS Smart AI File Finder")
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in menu bar

        self.spotlight_window: Optional[SpotlightWindow] = None
        self.finder_window: Optional[FinderWindow] = None
        self.tray_manager: Optional[SystemTrayManager] = None
        self.hotkey_manager: Optional[GlobalHotkeyManager] = None
        self.watcher: Optional[Watcher] = None

    def toggle_spotlight(self) -> None:
        """Toggle or summon the floating Spotlight HUD window anywhere on macOS."""
        if not self.spotlight_window:
            self.spotlight_window = SpotlightWindow()

        if self.spotlight_window.isVisible():
            self.spotlight_window.hide()
        else:
            activate_macos_app()
            self.spotlight_window.show()
            self.spotlight_window.raise_()
            self.spotlight_window.activateWindow()
            self.spotlight_window.search_input.setFocus()
            self.spotlight_window.search_input.selectAll()

    def open_finder(self) -> None:
        """Open or bring the full AI Finder window to front."""
        if not self.finder_window:
            self.finder_window = FinderWindow()

        activate_macos_app()
        self.finder_window.show()
        self.finder_window.raise_()
        self.finder_window.activateWindow()

    def run(self) -> int:
        """Start resident daemon services and application event loop."""
        logger.info("Initializing macOS Resident AI Finder System...")

        # 1. Start Background Watcher (FSEvents realtime indexing)
        try:
            self.watcher = Watcher()
            self.watcher.start(config.indexed_directories)
            logger.info("Realtime FSEvents Filesystem Watcher started.")
        except Exception as e:
            logger.warning(f"Failed to start filesystem watcher: {e}")

        # 2. Start Global Hotkey Manager (Option + Space)
        self.hotkey_manager = GlobalHotkeyManager(on_trigger=self.toggle_spotlight)
        self.hotkey_manager.start()

        # 3. Start System Tray (Menu Bar resident item)
        self.tray_manager = SystemTrayManager(
            on_open_spotlight=self.toggle_spotlight,
            on_open_finder=self.open_finder,
        )

        # 4. Open initial window based on mode
        if self.mode == "finder":
            self.open_finder()
        elif self.mode == "spotlight":
            self.toggle_spotlight()
        elif self.mode == "daemon":
            logger.info("Running in pure background resident daemon mode (Menu Bar & Global Hotkey active).")

        return self.app.exec()


def run_resident_app(mode: str = "finder") -> None:
    """Launch the resident system."""
    res_app = ResidentApplication(mode=mode)
    sys.exit(res_app.run())
