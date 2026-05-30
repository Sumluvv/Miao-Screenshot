# 分屏截屏助手 — Windows 打包脚本
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> 安装依赖"
pip install -r requirements-win.txt
pip install pyinstaller pillow

Write-Host "==> 生成图标"
python scripts/make_icon.py

Write-Host "==> 移除与 PyInstaller 冲突的 pathlib 回退包（若存在）"
pip uninstall -y pathlib 2>$null

Write-Host "==> PyInstaller 打包"
python -m PyInstaller build/win.spec --noconfirm --clean

$Out = Join-Path $Root "dist\SplitScreenSnap.exe"
if (Test-Path $Out) {
    Write-Host "完成: $Out"
} else {
    Write-Error "未找到输出文件"
}
