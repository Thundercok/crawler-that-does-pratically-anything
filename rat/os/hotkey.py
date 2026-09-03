"""
rat.os.hotkey — System-Wide Global Hotkey Listener for macOS.
Hooks directly into macOS input events to summon the floating search HUD anywhere.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

from rat.config import config

logger = logging.getLogger("rat.os.hotkey")


class GlobalHotkeyManager:
    """Manages system-wide global shortcuts without conflicting with macOS or third-party apps."""

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

            # Non-conflicting shortcuts:
            # Avoids Control+Space (collides with macOS Vietnamese Input Source switch and IDE autocomplete)
            # Avoids Option+Space (collides with Raycast and Alfred)
            # Avoids Command+Space (collides with Apple Spotlight)
            primary = config.global_hotkey.strip()
            hotkeys = {
                primary: _handle_activate,
            }
            # Add Option+R ("R" for RAT) as secondary fallback if not primary
            if primary != "<alt>+r":
                hotkeys["<alt>+r"] = _handle_activate

            self._listener = keyboard.GlobalHotKeys(hotkeys)
            self._listener.start()
            self._running = True
            logger.info(f"Global Hotkey Manager started with conflict-free hotkey: {config.get_hotkey_display()} ({list(hotkeys.keys())})")
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
