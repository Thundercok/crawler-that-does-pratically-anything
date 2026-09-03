"""
rat.os.hotkey — System-Wide Global Hotkey Listener for macOS.
Hooks directly into macOS input events to summon the floating search HUD anywhere.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger("rat.os.hotkey")


class GlobalHotkeyManager:
    """Manages system-wide global shortcuts (Option + Space, Cmd + Shift + Space)."""

    def __init__(self, on_trigger: Optional[Callable[[], None]] = None) -> None:
        self.on_trigger = on_trigger
        self._listener = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Start listening for global hotkeys in a background thread."""
        if self._running:
            return True

        try:
            from pynput import keyboard

            def _handle_activate() -> None:
                logger.info("Global hotkey triggered!")
                if self.on_trigger:
                    self.on_trigger()

            # Listen for Control+Space (<ctrl>+<space>) as requested, plus Cmd+Shift+Space and Option+Space as fallbacks
            hotkeys = {
                "<ctrl>+<space>": _handle_activate,
                "<alt>+<space>": _handle_activate,
                "<cmd>+<shift>+<space>": _handle_activate,
            }

            self._listener = keyboard.GlobalHotKeys(hotkeys)
            self._listener.start()
            self._running = True
            logger.info("Global Hotkey Manager started successfully (<ctrl>+<space>).")
            return True
        except Exception as e:
            logger.warning(f"Failed to start GlobalHotKeys listener: {e}")
            return False

    def stop(self) -> None:
        """Stop listening for global shortcuts."""
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        self._running = False
        logger.info("Global Hotkey Manager stopped.")
