"""
rat.ui.spotlight_window — 100% Genuine Apple macOS Light Theme Spotlight Window.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, QPoint, Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QGuiApplication, QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from rat.config import config
from rat.crawler.db import Database
from rat.engine.hybrid_search import SearchEngine
from rat.engine.reranker import SearchResultItem
from rat.ui.action_menu import ActionMenuDialog
from rat.ui.apple_item_delegate import AppleSpotlightDelegate
from rat.ui.preview_panel import PreviewPanel, open_file_default, reveal_in_finder
from rat.ui.settings_dialog import SettingsDialog
from rat.ui.theme import RAYCAST_QSS

logger = logging.getLogger("rat.ui")

FILTER_CATEGORIES = [
    ("all", "Tất cả", []),
    ("docs", "Văn bản", [".docx", ".doc", ".pdf", ".txt", ".md"]),
    ("sheets", "Bảng tính", [".xlsx", ".xls", ".csv"]),
    ("slides", "Slide", [".pptx", ".ppt"]),
    ("code", "Code", [".py", ".js", ".ts", ".html", ".css", ".json", ".sh", ".sql"]),
    ("images", "Hình ảnh", [".png", ".jpg", ".jpeg", ".webp"]),
]


class SearchWorker(QObject):
    """Long-lived background search worker."""
    search_completed = pyqtSignal(int, dict)

    def __init__(self, engine: SearchEngine) -> None:
        super().__init__()
        self.engine = engine
        try:
            self.engine.embedder.embed_query("warmup")
            self.engine.vector_cache.preload()
        except Exception as e:
            logger.warning(f"SearchWorker warmup error: {e}")

    @pyqtSlot(int, str, list)
    def do_search(self, request_id: int, query: str, extensions: list) -> None:
        try:
            response = self.engine.search(
                query,
                limit=30,
                use_hyde=False,
                use_vector=True
            )
            if extensions:
                filtered = [r for r in response["results"] if r.file_ext.lower() in extensions]
                response["results"] = filtered

            self.search_completed.emit(request_id, response)
        except Exception as e:
            logger.error(f"SearchWorker error: {e}")
            self.search_completed.emit(
                request_id,
                {"query": query, "results": [], "latency_ms": 0, "parsed_context": {}}
            )


class SpotlightWindow(QMainWindow):
    """Pure Apple macOS Light Theme Spotlight Window with Native QPainter Item Delegate."""
    search_requested = pyqtSignal(int, str, list)

    def __init__(self) -> None:
        super().__init__()
        self.db = Database(config.db_path)
        self.engine = SearchEngine(self.db)
        self.active_filter_idx = 0
        self._request_counter = 0

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(130)
        self.search_timer.timeout.connect(self._execute_search)

        self._drag_pos = QPoint()
        self._init_thread()
        self._init_window()
        self._init_ui()
        self._load_initial_data()

    def _init_thread(self) -> None:
        self.search_thread = QThread(self)
        self.worker = SearchWorker(self.engine)
        self.worker.moveToThread(self.search_thread)
        self.search_requested.connect(self.worker.do_search)
        self.worker.search_completed.connect(self._on_search_completed)
        self.search_thread.start()

    def _init_window(self) -> None:
        self.setWindowTitle("rat")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(950, 570)
        self.setStyleSheet(RAYCAST_QSS)

        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2 - 30
            self.move(x, max(geo.y() + 30, y))

    def _init_ui(self) -> None:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 55))
        shadow.setOffset(0, 8)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)

        container = QFrame()
        container.setObjectName("SpotlightContainer")
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setGraphicsEffect(shadow)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 1. Search Header
        header = QFrame()
        header.setObjectName("SearchHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 14, 16, 10)
        header_layout.setSpacing(8)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("🔍 Tìm tệp tin (VD: bài tập dsa thầy dũng, tiền cơm, đồ án tốt nghiệp...)")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        header_layout.addWidget(self.search_input)

        # Scope Bar (Filter Pills)
        self.filter_bar = QFrame()
        self.filter_bar.setObjectName("FilterPillsBar")
        filter_layout = QHBoxLayout(self.filter_bar)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(6)

        self.filter_buttons: List[QPushButton] = []
        for idx, (cat_id, label, _) in enumerate(FILTER_CATEGORIES):
            btn = QPushButton(f"{label}")
            btn.setProperty("class", "FilterPill")
            btn.setProperty("active", "true" if idx == 0 else "false")
            btn.clicked.connect(lambda checked, i=idx: self._select_filter(i))
            filter_layout.addWidget(btn)
            self.filter_buttons.append(btn)

        filter_layout.addStretch()

        self.btn_settings = QPushButton("⚙️ Cài đặt")
        self.btn_settings.setProperty("class", "FilterPill")
        self.btn_settings.clicked.connect(self._open_settings)
        filter_layout.addWidget(self.btn_settings)

        header_layout.addWidget(self.filter_bar)
        container_layout.addWidget(header)

        # 2. Main Dual Pane (50/50 Split)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #e5e5ea; width: 1px; }")

        # Left List (Rendered with Native Apple QPainter Delegate)
        self.result_list = QListWidget()
        self.result_list.setObjectName("ResultList")
        self.result_list.setFrameShape(QFrame.Shape.NoFrame)
        self.result_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.result_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.result_list.setItemDelegate(AppleSpotlightDelegate(self))
        self.result_list.currentRowChanged.connect(self._on_result_selected)
        self.result_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.splitter.addWidget(self.result_list)

        # Right Quick Look Inspector
        self.preview_panel = PreviewPanel()
        self.splitter.addWidget(self.preview_panel)

        self.splitter.setSizes([475, 475])
        container_layout.addWidget(self.splitter, 1)

        # 3. Action Footer
        footer = QFrame()
        footer.setObjectName("ActionFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 8, 16, 8)
        footer_layout.setSpacing(12)

        self.footer_status = QLabel("⚡ Đang tải...")
        self.footer_status.setObjectName("FooterStatus")
        footer_layout.addWidget(self.footer_status)
        footer_layout.addStretch()

        hotkeys = [
            ("↵", "Mở"),
            ("⌘↵", "Finder"),
            ("⌘C", "Copy"),
            ("⌘K", "Tác vụ"),
            ("Esc", "Đóng"),
        ]
        for key, desc in hotkeys:
            badge = QLabel(key)
            badge.setProperty("class", "HotkeyBadge")
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #636366; font-size: 11px; margin-right: 4px;")
            footer_layout.addWidget(badge)
            footer_layout.addWidget(desc_label)

        container_layout.addWidget(footer)
        main_layout.addWidget(container)

    def _load_initial_data(self) -> None:
        stats = self.db.get_stats()
        self.footer_status.setText(f"⚡ {stats['total_files']} tệp trong kho")
        self._execute_search()

    def _on_search_text_changed(self) -> None:
        self.search_timer.start()

    def _select_filter(self, idx: int) -> None:
        self.active_filter_idx = idx
        for i, btn in enumerate(self.filter_buttons):
            btn.setProperty("active", "true" if i == idx else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._execute_search()

    def _execute_search(self) -> None:
        self.search_timer.stop()
        query = self.search_input.text().strip()
        _, _, exts = FILTER_CATEGORIES[self.active_filter_idx]

        self._request_counter += 1
        req_id = self._request_counter
        self.footer_status.setText("Đang tìm...")
        self.search_requested.emit(req_id, query, list(exts) if exts else [])

    @pyqtSlot(int, dict)
    def _on_search_completed(self, request_id: int, response: Dict[str, Any]) -> None:
        if request_id != self._request_counter:
            return

        results: List[SearchResultItem] = response.get("results", [])
        latency = response.get("latency_ms", 0)

        self.result_list.clear()

        for item in results:
            list_item = QListWidgetItem(self.result_list)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.result_list.addItem(list_item)

        if results:
            self.result_list.setCurrentRow(0)
            self.footer_status.setText(f"{len(results)} kết quả ({latency}ms)")
        else:
            self.preview_panel.set_item(None)
            self.footer_status.setText(f"Không có kết quả ({latency}ms)")

    def _on_result_selected(self, row: int) -> None:
        item = self.result_list.item(row)
        if item:
            search_item: SearchResultItem = item.data(Qt.ItemDataRole.UserRole)
            self.preview_panel.set_item(search_item)
        else:
            self.preview_panel.set_item(None)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        search_item: SearchResultItem = item.data(Qt.ItemDataRole.UserRole)
        if search_item:
            open_file_default(search_item.file_path)

    def _open_action_menu(self) -> None:
        curr_row = self.result_list.currentRow()
        curr_item = self.result_list.item(curr_row)
        search_item = curr_item.data(Qt.ItemDataRole.UserRole) if curr_item else None

        dialog = ActionMenuDialog(search_item, self)
        dialog.action_triggered.connect(self._handle_action)

        pos = self.mapToGlobal(QPoint((self.width() - dialog.width()) // 2, (self.height() - dialog.height()) // 2))
        dialog.move(pos)
        dialog.exec()

    def _handle_action(self, action_id: str) -> None:
        curr_row = self.result_list.currentRow()
        curr_item = self.result_list.item(curr_row)
        search_item: Optional[SearchResultItem] = curr_item.data(Qt.ItemDataRole.UserRole) if curr_item else None

        if action_id == "open" and search_item:
            open_file_default(search_item.file_path)
        elif action_id == "finder" and search_item:
            reveal_in_finder(search_item.file_path)
        elif action_id == "copy_path" and search_item:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(search_item.file_path)
        elif action_id == "copy_content" and search_item:
            from rat.crawler.extractors import extract_document_content
            text = extract_document_content(search_item.file_path)
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(text)
        elif action_id == "settings":
            self._open_settings()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()

        # CMD + Number for Tab switching (⌘1, ⌘2, ⌘3, ⌘4, ⌘5, ⌘6)
        if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier):
            if Qt.Key.Key_1 <= key <= Qt.Key.Key_6:
                idx = key - Qt.Key.Key_1
                if idx < len(FILTER_CATEGORIES):
                    self._select_filter(idx)
                    return

        if key == Qt.Key.Key_K and (modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier)):
            self._open_action_menu()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier)):
            curr_row = self.result_list.currentRow()
            item = self.result_list.item(curr_row)
            if item:
                search_item = item.data(Qt.ItemDataRole.UserRole)
                reveal_in_finder(search_item.file_path)
            return

        if key == Qt.Key.Key_C and (modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier)):
            curr_row = self.result_list.currentRow()
            item = self.result_list.item(curr_row)
            if item:
                search_item = item.data(Qt.ItemDataRole.UserRole)
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setText(search_item.file_path)
            return

        if key == Qt.Key.Key_Tab:
            next_idx = (self.active_filter_idx + 1) % len(FILTER_CATEGORIES)
            self._select_filter(next_idx)
            return
        elif key == Qt.Key.Key_Backtab:
            prev_idx = (self.active_filter_idx - 1 + len(FILTER_CATEGORIES)) % len(FILTER_CATEGORIES)
            self._select_filter(prev_idx)
            return

        if key == Qt.Key.Key_Escape:
            if self.search_input.text():
                self.search_input.clear()
            else:
                self.close()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            curr_row = self.result_list.currentRow()
            item = self.result_list.item(curr_row)
            if item:
                search_item = item.data(Qt.ItemDataRole.UserRole)
                open_file_default(search_item.file_path)
            return

        if key == Qt.Key.Key_Down:
            curr = self.result_list.currentRow()
            if curr < self.result_list.count() - 1:
                self.result_list.setCurrentRow(curr + 1)
            return
        elif key == Qt.Key.Key_Up:
            curr = self.result_list.currentRow()
            if curr > 0:
                self.result_list.setCurrentRow(curr - 1)
            return

        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def closeEvent(self, event) -> None:
        if hasattr(self, "search_thread") and self.search_thread.isRunning():
            self.search_thread.quit()
            self.search_thread.wait()
        super().closeEvent(event)
