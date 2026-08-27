"""
rat.ui.theme — 100% Genuine Apple macOS Light Theme Design System.
"""

# Native Apple System Colors (macOS Light HIG)
EXT_COLORS = {
    # Pages / Word -> Apple Blue
    ".docx": {"bg": "#007aff", "fg": "#ffffff", "border": "#0a84ff", "label": "DOC"},
    ".doc": {"bg": "#007aff", "fg": "#ffffff", "border": "#0a84ff", "label": "DOC"},
    # Preview / PDF -> Apple Red
    ".pdf": {"bg": "#ff3b30", "fg": "#ffffff", "border": "#ff453a", "label": "PDF"},
    # Numbers / Excel -> Apple Green
    ".xlsx": {"bg": "#34c759", "fg": "#ffffff", "border": "#30d158", "label": "XLS"},
    ".xls": {"bg": "#34c759", "fg": "#ffffff", "border": "#30d158", "label": "XLS"},
    ".csv": {"bg": "#34c759", "fg": "#ffffff", "border": "#30d158", "label": "CSV"},
    # Keynote / Slide -> Apple Orange
    ".pptx": {"bg": "#ff9500", "fg": "#ffffff", "border": "#ff9f0a", "label": "PPT"},
    ".ppt": {"bg": "#ff9500", "fg": "#ffffff", "border": "#ff9f0a", "label": "PPT"},
    # Photos / Images -> Apple Teal
    ".png": {"bg": "#30b0c7", "fg": "#ffffff", "border": "#40c8e0", "label": "IMG"},
    ".jpg": {"bg": "#30b0c7", "fg": "#ffffff", "border": "#40c8e0", "label": "IMG"},
    ".jpeg": {"bg": "#30b0c7", "fg": "#ffffff", "border": "#40c8e0", "label": "IMG"},
    ".webp": {"bg": "#30b0c7", "fg": "#ffffff", "border": "#40c8e0", "label": "IMG"},
    # Xcode / Code -> Apple Purple
    ".py": {"bg": "#af52de", "fg": "#ffffff", "border": "#bf5af2", "label": "PY"},
    ".js": {"bg": "#e6a100", "fg": "#ffffff", "border": "#ffd60a", "label": "JS"},
    ".ts": {"bg": "#007aff", "fg": "#ffffff", "border": "#0a84ff", "label": "TS"},
    ".html": {"bg": "#ff9500", "fg": "#ffffff", "border": "#ff9f0a", "label": "HTML"},
    ".css": {"bg": "#30b0c7", "fg": "#ffffff", "border": "#40c8e0", "label": "CSS"},
    ".json": {"bg": "#bf5af2", "fg": "#ffffff", "border": "#da8fff", "label": "JSON"},
    ".sh": {"bg": "#34c759", "fg": "#ffffff", "border": "#30d158", "label": "SH"},
    ".sql": {"bg": "#5856d6", "fg": "#ffffff", "border": "#7d7aff", "label": "SQL"},
    # TextEdit / Notes -> Apple Graphite
    ".txt": {"bg": "#636366", "fg": "#ffffff", "border": "#8e8e93", "label": "TXT"},
    ".md": {"bg": "#636366", "fg": "#ffffff", "border": "#8e8e93", "label": "MD"},
}


def get_ext_badge_info(ext: str) -> dict:
    ext_clean = ext.lower()
    if ext_clean in EXT_COLORS:
        return EXT_COLORS[ext_clean]
    label = ext_clean.lstrip(".").upper() or "FILE"
    return {"bg": "#636366", "fg": "#ffffff", "border": "#8e8e93", "label": label[:4]}


RAYCAST_QSS = """
/* 100% Genuine Apple macOS Light Theme */
* {
    font-family: ".AppleSystemUIFont", "Helvetica Neue", "Arial";
    outline: none;
}

/* Spotlight Window Container (Frosted White Glass) */
QFrame#SpotlightContainer {
    background-color: #ffffff;
    border: 1px solid #d1d1d6;
    border-radius: 16px;
}

/* Search Header */
QFrame#SearchHeader {
    background-color: #fbfbfd;
    border-bottom: 1px solid #e5e5ea;
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
    padding: 12px 16px 10px 16px;
}

QLineEdit#SearchInput {
    background-color: #ffffff;
    color: #1c1c1e;
    font-size: 17px;
    font-weight: 400;
    border: 1px solid #d1d1d6;
    border-radius: 10px;
    padding: 10px 14px;
    selection-background-color: #007aff;
    selection-color: #ffffff;
}

QLineEdit#SearchInput:focus {
    border: 1.5px solid #007aff;
    background-color: #ffffff;
}

/* Scope Bar (Segmented Pills) */
QFrame#FilterPillsBar {
    background-color: transparent;
    padding: 2px 0px 0px 0px;
}

QPushButton.FilterPill {
    background-color: #e5e5ea;
    color: #48484a;
    font-size: 12px;
    font-weight: 500;
    padding: 5px 12px;
    border-radius: 6px;
    border: none;
}

QPushButton.FilterPill:hover {
    background-color: #d1d1d6;
    color: #1c1c1e;
}

QPushButton.FilterPill[active="true"] {
    background-color: #007aff;
    color: #ffffff;
    font-weight: 600;
}

/* Result List */
QListWidget#ResultList {
    background-color: #ffffff;
    border: none;
    outline: none;
    padding: 6px 8px;
}

QListWidget#ResultList::item {
    background-color: transparent;
    border-radius: 8px;
    padding: 0px;
    margin: 2px 0px;
    border: none;
}

QListWidget#ResultList::item:hover {
    background-color: #f2f2f7;
}

QListWidget#ResultList::item:selected {
    background-color: #e8edf7;
    border: 1px solid #007aff;
}

/* Inspector / Quick Look Panel */
QFrame#PreviewPanel {
    background-color: #fbfbfd;
    border-left: 1px solid #e5e5ea;
    border-bottom-right-radius: 16px;
    padding: 16px 20px;
}

QTextEdit#PreviewContent {
    background-color: #ffffff;
    color: #1c1c1e;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    font-size: 12px;
    padding: 12px;
    font-family: "Menlo", monospace;
    line-height: 1.55;
}

/* Action Footer */
QFrame#ActionFooter {
    background-color: #f5f5f7;
    border-top: 1px solid #e5e5ea;
    border-bottom-left-radius: 16px;
    border-bottom-right-radius: 16px;
    padding: 8px 18px;
}

QLabel#FooterStatus {
    color: #636366;
    font-size: 12px;
    font-weight: 400;
}

QLabel.HotkeyBadge {
    background-color: #ffffff;
    color: #1c1c1e;
    border: 1px solid #d1d1d6;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 600;
    font-family: "Menlo", monospace;
}

/* Minimalist macOS Light Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: rgba(0, 0, 0, 0.2);
    min-height: 25px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(0, 0, 0, 0.4);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
