#!/usr/bin/env bash
# 分屏截屏助手 — macOS 打包脚本（生成 .app）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> 安装依赖"
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller pillow

echo "==> 生成图标"
python3 scripts/make_icon.py
# macOS 可选: 将 icon.png 转为 icon.icns（需 iconutil 或在线工具）
if command -v iconutil &>/dev/null && [ -f assets/icon.png ]; then
  mkdir -p assets/icon.iconset
  sips -z 512 512 assets/icon.png --out assets/icon.iconset/icon_512x512.png 2>/dev/null || true
  iconutil -c icns assets/icon.iconset -o assets/icon.icns 2>/dev/null || true
fi

echo "==> PyInstaller 打包"
pyinstaller build/mac.spec --noconfirm --clean

echo "完成: dist/分屏截屏助手.app"
echo "注意: macOS 版支持整屏/区域截图；窗口截图与部分粘贴增强为 Windows 完整版。"
