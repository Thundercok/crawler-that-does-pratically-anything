# -*- mode: python ; coding: utf-8 -*-
"""
rat.spec — PyInstaller bundle specification for macOS Standalone App.
Packages Python runtime, PyQt6, ONNX/FastEmbed, Apple Vision, and all dependencies into a single rat.app.
"""

import sys
from pathlib import Path

block_cipher = None

added_files = [
    ('rat/crawler', 'rat/crawler'),
    ('rat/engine', 'rat/engine'),
    ('rat/ui', 'rat/ui'),
]

hidden_imports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'pypdf',
    'docx',
    'pptx',
    'openpyxl',
    'fastembed',
    'onnxruntime',
    'objc',
    'Foundation',
    'Quartz',
    'AppKit',
    'watchdog',
    'numpy',
    'PIL',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='rat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='rat',
)

app = BUNDLE(
    coll,
    name='rat.app',
    icon=None,
    bundle_identifier='com.thundercock.rat',
    info_plist={
        'CFBundleName': 'rat',
        'CFBundleDisplayName': 'rat — Smart File Finder',
        'CFBundleGetInfoString': "AI-Powered Local Semantic File Finder for macOS",
        'CFBundleIdentifier': "com.thundercock.rat",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': "Copyright © 2026, All Rights Reserved.",
        'NSHighResolutionCapable': True,
        'NSSupportsAutomaticGraphicsSwitching': True,
    },
)
