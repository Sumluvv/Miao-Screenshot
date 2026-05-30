# -*- mode: python -*-
# PyInstaller — Windows 单文件 exe
from pathlib import Path

# SPECPATH = packaging/ 目录，上一级为项目根
root = Path(SPECPATH).resolve().parent
icon = root / "assets" / "icon.ico"

block_cipher = None

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / "assets" / "icon.ico"), "assets")] if icon.exists() else [],
    hiddenimports=[
        "mss",
        "PIL",
        "PIL.Image",
        "win32clipboard",
        "win32api",
        "keyboard",
        "pyautogui",
        "app_meta",
        "ui_theme",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SplitScreenSnap",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon) if icon.exists() else None,
)
