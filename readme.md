# 秒截图 (Miao Screenshot)

> Windows 下一键截图 → 剪贴板 →（可选）自动粘贴到当前应用并发送。适用于网测刷题、办公截图发给 AI、多屏工作流等。

**开源仓库**：[https://github.com/Sumluvv/Miao-Screenshot](https://github.com/Sumluvv/Miao-Screenshot)

---

## 一、功能清单

| 功能 | 说明 |
|------|------|
| 整屏截图 | 多屏下可选屏幕 1 / 2 / … |
| 指定窗口截图 | 下拉列表选择顶层窗口（点「刷新」更新列表） |
| 矩形区域截图 | 全虚拟屏半透明覆盖层拖拽框选 |
| 持续区域 | 勾选后只保存一块区域，之后每次截图沿用该区域 |
| 非持续区域 | 不勾选则每次截图前都会重新框选 |
| 小浮窗模式 | 只保留「📸」与「设置」，减少遮挡 |
| 剪贴板图片 | 支持粘贴到浏览器、Office、IM 等 |
| 自动粘贴 + 发送 | Ctrl+V 后回车或点击坐标发送（适合 AI 网页） |
| 全局快捷键 | 默认 F8（焦点在目标输入框时最稳） |
| 置顶与透明度 | 周期性置顶 + 透明度可调 |

---

## 二、安装与运行

**环境**：Windows 10 / 11，Python 3.8+

```powershell
cd "你的项目目录"
pip install -r requirements.txt
python main.py
```

自检（可选）：

```powershell
python test_smoke.py
```

---

## 三、使用说明（简要）

1. **整屏**：截取来源选「整屏」，选屏幕编号，点「截图并粘贴」或按 **F8**。
2. **窗口**：选「窗口」→「刷新」→ 在下拉里选中目标窗口 → 截图（请尽量让该窗口可见，否则可能截到被遮挡的画面）。
3. **区域**：选「区域」→ 点「选取区域」或首次截图时按提示框选 → 勾选「持续使用同一区域」则之后每次自动截同一矩形；不勾选则每次截图前重新框选。
4. **小浮窗**：勾选「小浮窗模式」后只显示小条；点「设置」可回到完整面板。
5. **发给 AI**：先在 AI 网页输入框里点一下（光标闪烁），再 **F8**；若图大或网速慢，把「上传等待」调到 2～5 秒。

---

## 四、推送到 GitHub（备份）

在已登录 `gh` 或已配置 SSH/HTTPS 凭据的前提下，在项目根目录执行：

```powershell
git init
git add .
git commit -m "秒截图 v2.0: 整屏/窗口/区域、小浮窗、剪贴板与自动发送"
git branch -M main
git remote add origin https://github.com/Sumluvv/Miao-Screenshot.git
git push -u origin main
```

若远程仓库已有内容且非空，请先 `git pull origin main --rebase` 再推送，或按 GitHub 页面说明操作。

### 不想改「全局」Git 用户名时（仅本次提交）

在 PowerShell 里先设环境变量再 `git commit`（不写 `git config --global`）：

```powershell
$env:GIT_AUTHOR_NAME="你的名字"
$env:GIT_AUTHOR_EMAIL="你的邮箱"
$env:GIT_COMMITTER_NAME=$env:GIT_AUTHOR_NAME
$env:GIT_COMMITTER_EMAIL=$env:GIT_AUTHOR_EMAIL
git commit -m "说明本次改动"
```

---

## 五、文件说明

| 文件 | 作用 |
|------|------|
| `main.py` | 主程序 |
| `requirements.txt` | 依赖 |
| `test_smoke.py` | 依赖与截屏自检 |
| `record_pos.py` | 可选：记录「点击坐标发送」用的屏幕坐标 |
| `config.json` | 运行后自动生成（已加入 `.gitignore`，勿提交隐私） |

---

## 六、常见问题

- **`win32gui` DLL 错误**：本版已用 `ctypes` 调用 `user32`，一般不再依赖 `win32gui`。
- **F8 粘贴了但没发送**：调大「上传等待」秒数。
- **按钮截图没贴到 AI**：先点一下 AI 输入框，再看「🎯 目标窗口」是否为目标应用标题。
- **区域模式 F8**：若未勾选「持续」，每次 F8 会先出现框选层，框选后再截图。

---

## 七、版本记录

- **v2.0.0** — 项目更名为「秒截图」；小浮窗模式；窗口截图；区域截图（持续/非持续）；仓库 [Miao-Screenshot](https://github.com/Sumluvv/Miao-Screenshot)。
- v1.x — 原「网测截图助手」能力保留并合并进上述流程。

---

## 八、许可

代码按仓库实际声明为准；若未添加 LICENSE，默认保留作者权利，使用请自行评估风险。
