# -*- coding: utf-8 -*-
"""应用元信息与路径（支持 PyInstaller 打包后运行）"""

import sys
from pathlib import Path

APP_NAME = "分屏截屏助手"
APP_NAME_EN = "Split Screen Snap"
VERSION = "3.0.0"
REPO_URL = "https://github.com/Sumluvv/Miao-Screenshot"
AUTHOR = "Sumluvv"

IS_WINDOWS = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()
CONFIG_FILE = APP_DIR / "config.json"
SCREENSHOT_DIR = APP_DIR / "screenshots"
ASSETS_DIR = APP_DIR / "assets"
