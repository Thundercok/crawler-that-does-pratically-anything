"""
rat.crawler.watcher — Real-time filesystem watcher using watchdog.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import List, Optional, Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from rat.config import SUPPORTED_EXTENSIONS, config, is_on_battery, set_thread_qos_background
from rat.crawler.indexer import Indexer

logger = logging.getLogger("rat.watcher")


class RatFileEventHandler(FileSystemEventHandler):
    """Event handler for filesystem changes with debouncing."""

    def __init__(self, indexer: Indexer, debounce_seconds: float = 2.0) -> None:
        super().__init__()
        self.indexer = indexer
        self.debounce_seconds = debounce_seconds
        self._pending_files: dict[str, float] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

    def _should_handle(self, path_str: str) -> bool:
        path = Path(path_str)
        if path.is_dir() or self.indexer.is_ignored(path):
            return False
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return False
        return True

    def on_created(self, event: FileSystemEvent) -> None:
        if getattr(event, "is_directory", False):
            return
        if self._should_handle(event.src_path):
            self._queue_file(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if getattr(event, "is_directory", False):
            return
        if self._should_handle(event.src_path):
            self._queue_file(event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if getattr(event, "is_directory", False):
            return
        if not self._should_handle(event.src_path):
            return
        try:
            self.indexer.db.delete_document(event.src_path)
            logger.info(f"File deleted from index: {event.src_path}")
        except Exception as e:
            logger.error(f"Error handling deleted file {event.src_path}: {e}")

    def on_moved(self, event: FileSystemEvent) -> None:
        if getattr(event, "is_directory", False):
            return
        if self._should_handle(event.src_path):
            self.indexer.db.delete_document(event.src_path)
        if hasattr(event, "dest_path") and self._should_handle(event.dest_path):
            self._queue_file(event.dest_path)

    def _queue_file(self, file_path: str) -> None:
        with self._lock:
            self._pending_files[file_path] = time.time()

    def _process_queue(self) -> None:
        set_thread_qos_background()
        while not self._stop_event.is_set():
            time.sleep(1.0)
            now = time.time()
            to_process = []
            with self._lock:
                for file_path, added_time in list(self._pending_files.items()):
                    if now - added_time >= self.debounce_seconds:
                        to_process.append(file_path)
                        del self._pending_files[file_path]

            on_battery = is_on_battery()
            throttle_sleep = 0.2 if on_battery else 0.05

            for file_path in to_process:
                if self._stop_event.is_set():
                    break
                if os.path.exists(file_path):
                    indexed = self.indexer.index_single_file(file_path, force=False)
                    if indexed:
                        logger.info(f"Auto-indexed updated file: {file_path}")
                    time.sleep(throttle_sleep)

    def stop(self) -> None:
        self._stop_event.set()


class FolderWatcher:
    """Manager for watching multiple folders."""

    def __init__(self, indexer: Optional[Indexer] = None) -> None:
        self.indexer = indexer or Indexer()
        self.observer = Observer()
        self.handler = RatFileEventHandler(self.indexer)
        self.is_running = False

    def start(self, directories: Optional[List[str]] = None) -> None:
        """Start watching directories asynchronously in background thread."""
        if self.is_running:
            return

        threading.Thread(
            target=self._start_internal,
            args=(directories,),
            daemon=True,
            name="rat-filesystem-watcher",
        ).start()

    def _start_internal(self, directories: Optional[List[str]] = None) -> None:
        try:
            target_dirs = directories or config.indexed_directories
            for d in target_dirs:
                try:
                    d_path = Path(d).expanduser().resolve()
                    if d_path.exists() and d_path.is_dir():
                        self.observer.schedule(self.handler, str(d_path), recursive=True)
                        logger.info(f"Watching directory: {d_path}")
                except Exception as e:
                    logger.warning(f"Failed to schedule directory {d}: {e}")

            self.observer.start()
            self.is_running = True
            logger.info("Realtime filesystem watcher started successfully.")
        except Exception as e:
            logger.warning(f"Error starting filesystem observer: {e}")

    def stop(self) -> None:
        """Stop watching directories."""
        if not self.is_running:
            return
        self.handler.stop()
        self.observer.stop()
        self.observer.join(timeout=2.0)
        self.is_running = False


# Alias for backward compatibility
Watcher = FolderWatcher
