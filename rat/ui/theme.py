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
/* SOTA Apple macOS Sequoia & Raycast Design System */
* {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", "Arial", sans-serif;
    outline: none;
}

/* Spotlight Window Container (Frosted Glass Acrylic Container) */
QFrame#SpotlightContainer {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 16px;
}

/* Search Header */
QFrame#SearchHeader {
    background-color: #fbfbfd;
    border-bottom: 1px solid #e2e8f0;
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
    padding: 14px 18px 11px 18px;
}

QLineEdit#SearchInput {
    background-color: #ffffff;
    color: #0f172a;
    font-size: 17px;
    font-weight: 400;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 10px 14px;
    selection-background-color: #007aff;
    selection-color: #ffffff;
}

QLineEdit#SearchInput:focus {
    border: 1.5px solid #007aff;
    background-color: #ffffff;
}

/* Scope Bar (Segmented Micro-Pills) */
QFrame#FilterPillsBar {
    background-color: transparent;
    padding: 2px 0px 0px 0px;
}

QPushButton.FilterPill {
    background-color: #f1f5f9;
    color: #475569;
    font-size: 11.5px;
    font-weight: 500;
    padding: 4px 11px;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
}

QPushButton.FilterPill:hover {
    background-color: #e2e8f0;
    color: #0f172a;
}

QPushButton.FilterPill[active="true"] {
    background-color: #007aff;
    color: #ffffff;
    font-weight: 600;
    border: 1px solid #0062cc;
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
    background-color: #f8fafc;
}

QListWidget#ResultList::item:selected {
    background-color: #eff6ff;
    border: 1px solid #38bdf8;
}

/* Inspector / Quick Look Panel */
QFrame#PreviewPanel {
    background-color: #fbfbfd;
    border-left: 1px solid #e2e8f0;
    border-bottom-right-radius: 16px;
    padding: 14px 16px;
}

QTextEdit#PreviewContent {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 12px;
    padding: 10px;
    font-family: -apple-system, BlinkMacSystemFont, "SF Mono", "Menlo", monospace;
    line-height: 1.55;
}

/* Raycast Action Footer with Keycap Badges */
QFrame#ActionFooter {
    background-color: #f8fafc;
    border-top: 1px solid #e2e8f0;
    border-bottom-left-radius: 16px;
    border-bottom-right-radius: 16px;
    padding: 8px 18px;
}

QLabel#FooterStatus {
    color: #475569;
    font-size: 11.5px;
    font-weight: 500;
}

/* SOTA Keycaps with 3D physical feel */
QLabel.HotkeyBadge {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f1f5f9);
    color: #334155;
    border: 1px solid #cbd5e1;
    border-bottom: 2px solid #94a3b8;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10.5px;
    font-weight: 600;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro", "Menlo", monospace;
}

/* Minimalist macOS Light Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: rgba(0, 0, 0, 0.18);
    min-height: 25px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(0, 0, 0, 0.35);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
