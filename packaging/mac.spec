# -*- mode: python -*-
# PyInstaller — macOS .app
from pathlib import Path

root = Path(SPECPATH).resolve().parent
icon = root / "assets" / "icon.icns"

block_cipher = None

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[],
    hiddenimports=["mss", "PIL", "PIL.Image", "keyboard", "pyautogui", "app_meta", "ui_theme"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["win32clipboard", "pywin32"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SplitScreenSnap",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon) if icon.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SplitScreenSnap",
)

app = BUNDLE(
    coll,
    name="分屏截屏助手.app",
    icon=str(icon) if icon.exists() else None,
    bundle_identifier="com.sumluvv.splitscreensnap",
    info_plist={
        "NSHighResolutionCapable": True,
        "CFBundleName": "分屏截屏助手",
        "CFBundleDisplayName": "分屏截屏助手",
    },
)
