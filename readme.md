# 分屏截屏助手 (Split Screen Snap)

> 双屏 / 多屏下一键截图，自动写入剪贴板，并粘贴到任意应用的**输入框**（AI、Office、浏览器等）。

## 下载即用（普通用户请看这里）

**不要下载绿色的 “Source code”**，那是源码，需要装 Python 才能跑。

请打开 **[Releases 发布页](https://github.com/Sumluvv/Miao-Screenshot/releases/latest)**，下载：

| 你的电脑 | 下载这个文件 | 怎么用 |
|----------|--------------|--------|
| **Windows** | `SplitScreenSnap.exe` | 双击运行，无需安装 |
| **macOS** | `SplitScreenSnap-mac.zip` | 解压后打开「分屏截屏助手.app」 |

首次运行若安全软件拦截，选择「仍要运行」即可。

---

![版本](https://img.shields.io/badge/version-3.0.0-blue)
![平台](https://img.shields.io/badge/Windows-完整功能-green)
![平台](https://img.shields.io/badge/macOS-整屏%2F区域-orange)

维护者发布新版本说明见 [docs/发布清单.md](docs/发布清单.md)。

---

## 功能一览

| 功能 | 说明 |
|------|------|
| 多屏整屏截图 | 自动识别显示器数量与分辨率，按物理坐标完整截取 |
| 窗口截图 | **Windows**：PrintWindow，支持 Chrome / Edge 等（避免黑屏） |
| 区域截图 | 拖拽框选；可「持续使用同一区域」 |
| 剪贴板 | 截图自动复制，目标处 `Ctrl+V` 即可粘贴 |
| 自动发送 | 可选粘贴后自动回车（适合 AI 网页） |
| 小浮窗模式 | 仅保留截图按钮，位置与完整面板一致 |
| 全局快捷键 | 默认 **F8**（焦点在输入框时最顺） |

---

## 快速开始

### 方式 A：Python 运行（开发）

```powershell
cd "你的项目目录"
pip install -r requirements-win.txt   # Windows
# pip install -r requirements.txt     # macOS
python main.py
```

### 方式 B：下载发布包（推荐）

在 GitHub [Releases](https://github.com/Sumluvv/Miao-Screenshot/releases) 下载：

| 平台 | 文件 | 说明 |
|------|------|------|
| Windows | `SplitScreenSnap.exe` | 单文件，双击运行 |
| macOS | `分屏截屏助手.app` | 拖入「应用程序」；首次需在「隐私与安全性」允许运行 |

---

## 自己打包

### Windows（生成 exe）

```powershell
.\scripts\build_windows.ps1
```

输出：`dist\SplitScreenSnap.exe`

### macOS（生成 .app）

```bash
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh
```

输出：`dist/分屏截屏助手.app`

> macOS 版：**整屏 + 区域 + 剪贴板 + F8**；**窗口截图**与 Win32 粘贴增强仅 Windows 提供。

---

## 使用步骤

1. 启动程序，将浮窗放在顺手位置。  
2. 在要粘贴的应用里**点一下输入框**（底部蓝字会显示「输入框窗口: xxx」）。  
3. 选择截图来源：**整屏 / 窗口(Win) / 区域**。  
4. 按 **F8** 或点 **「截图并粘贴到输入框」**。  
5. 若开启自动发送，等待「上传等待」时间（图大或网慢可调 2~5 秒）。

**小浮窗**：勾选「小浮窗模式」→ 仅显示截图按钮；点「设置」展开完整面板（**位置不变**）。

---

## 项目结构

```
├── main.py              # 程序入口
├── app_meta.py          # 名称、版本、路径
├── ui_theme.py          # 界面主题
├── assets/              # 图标（打包用）
├── packaging/           # PyInstaller spec（会提交到 Git）
├── build/               # PyInstaller 缓存（本地，不提交）
├── scripts/             # 打包与图标脚本
├── requirements*.txt
├── LICENSE
└── readme.md
```

---

## 推送到 GitHub

```powershell
git add .
git commit -m "release: 分屏截屏助手 v3.0 UI与打包"
git push origin main
```

建议在 GitHub 创建 **Release**，上传 `SplitScreenSnap.exe` 与 `分屏截屏助手.app`（或 zip）。

---

## 常见问题

**Q：窗口截图黑屏？**  
A：v3 已用 PrintWindow；请更新到最新版，并确保窗口未最小化。

**Q：屏幕 2 截不全？**  
A：v3 使用系统显示器枚举；点「刷新」后重选屏幕 2。

**Q：F8 没反应？**  
A：以管理员运行或检查是否被安全软件拦截；仍可用浮窗按钮。

**Q：Mac 没有窗口选项？**  
A：窗口截图为 Windows 专用；Mac 请用整屏或区域。

---

## 许可证

[MIT](LICENSE) © Sumluvv
