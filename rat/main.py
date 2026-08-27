"""
rat.main — Primary entry point for rat (GUI & CLI).
"""

from __future__ import annotations

import logging
import sys

from PyQt6.QtWidgets import QApplication

from rat.cli import main as cli_main
from rat.ui.finder_window import FinderWindow
from rat.ui.spotlight_window import SpotlightWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
)


def activate_macos_app() -> None:
    """Ensure the Python GUI gains active foreground focus on macOS."""
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyRegular
        ns_app = NSApplication.sharedApplication()
        ns_app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        ns_app.activateIgnoringOtherApps_(True)
    except Exception:
        pass


def run_gui(mode: str = "finder") -> None:
    """Launch Finder Window (default) or Spotlight Window."""
    activate_macos_app()
    app = QApplication(sys.argv)
    app.setApplicationName("rat — Smart macOS File Finder")

    if mode == "spotlight":
        window = SpotlightWindow()
    else:
        window = FinderWindow()

    window.show()
    window.raise_()
    window.activateWindow()
    activate_macos_app()
    sys.exit(app.exec())


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in ("search", "index", "status", "ask", "dedup", "--help", "-h"):
        cli_main()
    elif len(sys.argv) > 1 and sys.argv[1] == "spotlight":
        run_gui(mode="spotlight")
    else:
        run_gui(mode="finder")


if __name__ == "__main__":
    main()
