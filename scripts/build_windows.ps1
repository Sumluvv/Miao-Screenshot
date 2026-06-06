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
python -m PyInstaller packaging/win.spec --noconfirm --clean

$Out = Join-Path $Root "dist\SplitScreenSnap.exe"
if (Test-Path $Out) {
    Write-Host "完成: $Out"
} else {
    Write-Error "未找到输出文件"
}

$Iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if ($Iscc) {
    Write-Host "==> 生成 Windows 安装器"
    Push-Location (Join-Path $Root "packaging")
    & $Iscc.Source "windows-installer.iss"
    Pop-Location
    $Installer = Join-Path $Root "dist\SplitScreenSnap-Setup.exe"
    if (Test-Path $Installer) {
        Write-Host "安装器完成: $Installer"
    } else {
        Write-Warning "未找到安装器输出文件"
    }
} else {
    Write-Host "未检测到 Inno Setup，已跳过安装器。若要生成 SplitScreenSnap-Setup.exe，请安装 Inno Setup。"
}
