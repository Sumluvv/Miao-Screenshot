# 分屏截屏助手 (Split Screen Snap)

双屏 / 多屏用户的一键截图小工具：截取整屏、窗口或区域，自动复制到剪贴板，并可粘贴到当前输入框后自动发送。适合频繁向 AI、Office、浏览器或聊天工具发送截图的场景。

![version](https://img.shields.io/badge/version-3.0.13-blue)
![Windows](https://img.shields.io/badge/Windows-安装版%20%2F%20免安装-green)
![macOS](https://img.shields.io/badge/macOS-整屏%20%2F%20区域-orange)

## 下载使用

普通用户请打开 [Releases 发布页](https://github.com/Sumluvv/Miao-Screenshot/releases/latest)，不要下载绿色的 `Source code`。

| 系统 | 推荐下载 | 说明 |
| --- | --- | --- |
| Windows | `SplitScreenSnap-Setup.exe` | 安装版，带开始菜单和卸载入口 |
| Windows | `SplitScreenSnap.exe` | 免安装版，下载后双击即可运行 |
| macOS | `SplitScreenSnap-mac.zip` | 解压后打开 `分屏截屏助手.app` |

Windows 首次运行若出现 SmartScreen 提示，请选择“更多信息”→“仍要运行”。macOS 首次运行若被系统拦截，请到“系统设置 → 隐私与安全性”允许打开。

## 验证下载文件

本项目暂未使用付费代码签名证书。浏览器可能会提示“无法验证文件是否安全”，这是未签名小众 exe 的常见提示。

每个 Release 会附带 `SHA256SUMS.txt`。Windows 用户可在下载目录运行：

```powershell
Get-FileHash .\SplitScreenSnap.exe -Algorithm SHA256
```

把输出的哈希值与 Release 附件中的 `SHA256SUMS.txt` 对比；一致说明文件没有被篡改。

## 主要功能

| 功能 | 说明 |
| --- | --- |
| 多屏整屏截图 | 自动识别显示器数量、位置和分辨率 |
| 窗口截图 | Windows 上使用窗口句柄截取，适合浏览器、Office 等应用 |
| 区域截图 | 拖拽框选区域，也可持续使用同一区域 |
| 剪贴板写入 | 截图后自动复制为图片，可直接 `Ctrl+V` |
| 自动粘贴发送 | 可选择粘贴后回车，或点击指定坐标发送 |
| 小浮窗模式 | 只保留截图按钮，适合长时间置顶使用 |
| 置顶开关 | 默认置顶，可用顶部“置顶开/关”按钮切换 |
| 全局快捷键 | 默认 `F8`，可在界面里改成 `ctrl+shift+s` 等组合 |

## 使用步骤

1. 启动程序，把窗口放在顺手的位置。
2. 在目标应用里点一下要粘贴截图的输入框。
3. 选择截图来源：整屏、窗口或区域。
4. 按快捷键，或点击“截图并粘贴”。
5. 如果开启自动发送，程序会等待上传完成后回车或点击发送。

## 开发运行

```powershell
cd "C:\Users\1\webtest script"
pip install -r requirements-win.txt
python main.py
```

macOS 开发环境可使用：

```bash
pip install -r requirements.txt
python main.py
```

## 本地打包

Windows：

```powershell
.\scripts\build_windows.ps1
```

输出文件：

- `dist\SplitScreenSnap.exe`：免安装版
- `dist\SplitScreenSnap-Setup.exe`：安装版，需要本机安装 Inno Setup；未安装时会自动跳过

macOS：

```bash
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh
```

输出文件：`dist/分屏截屏助手.app`

## GitHub 自动发布

仓库已包含 `.github/workflows/release.yml`。推送 `v*` 标签会自动构建并创建 Release：

```powershell
git tag v3.0.13
git push origin v3.0.13
```

Release 附件会包含 Windows 安装版、Windows 免安装版和 macOS zip。发布前可参考 [docs/发布清单.md](docs/发布清单.md)。

## 常见问题

**浏览器提示无法验证文件是否安全怎么办？**  
请确认文件来自本仓库的 GitHub Releases，并按上面的 SHA256 步骤校验。免费方案无法彻底消除 SmartScreen 提示，只有付费代码签名证书能稳定解决。

**窗口截图黑屏怎么办？**  
请确认目标窗口没有最小化。部分硬件加速或受保护窗口可能无法被系统 API 完整截取，可改用整屏或区域截图。

**F8 没反应怎么办？**  
可能被安全软件或系统权限拦截。可改用窗口里的截图按钮，或尝试以管理员身份运行。

**为什么我下载源码后打不开？**  
源码需要 Python 环境。普通用户请在 Releases 页面下载 `SplitScreenSnap-Setup.exe` 或 `SplitScreenSnap.exe`。

## 许可

[MIT](LICENSE) © Sumluvv
