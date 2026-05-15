# -*- coding: utf-8 -*-
"""
最小自检脚本 (Smoke Test)
-----------------------
在正式使用前运行，验证：
  1. 必需依赖都已安装
  2. 多屏识别正常
  3. 截屏功能正常
  4. 剪贴板写入正常
  5. (不实际触发) 自动按键的库可用

运行: python test_smoke.py
通过: 终端输出 "✅ 自检通过"
"""

import sys
import traceback
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def check(name: str, fn):
    """运行检查项，返回 (ok, msg)"""
    try:
        msg = fn()
        print(f"  ✅ {name}: {msg}")
        return True
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        traceback.print_exc()
        return False


def check_imports():
    import mss, PIL, win32clipboard, keyboard, pyautogui
    return "依赖完整"


def _mss_ctx():
    import mss
    return mss.MSS() if hasattr(mss, "MSS") else mss.mss()


def check_monitors():
    with _mss_ctx() as sct:
        mons = sct.monitors
        if len(mons) < 2:
            raise RuntimeError(f"只检测到 {len(mons)-1} 个屏幕，无法多屏使用")
        info = ", ".join(f"屏幕{i}={m['width']}x{m['height']}" for i, m in enumerate(mons[1:], 1))
        return f"识别到 {len(mons)-1} 个屏幕 ({info})"


def check_capture():
    from PIL import Image
    with _mss_ctx() as sct:
        sct_img = sct.grab(sct.monitors[1])
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
    return f"截屏成功 ({img.size[0]}x{img.size[1]})"


def check_clipboard():
    """写一张 1x1 测试图到剪贴板，再读出来验证"""
    from io import BytesIO
    import win32clipboard
    from PIL import Image

    img = Image.new("RGB", (10, 10), (255, 0, 0))
    output = BytesIO()
    img.save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    finally:
        win32clipboard.CloseClipboard()

    win32clipboard.OpenClipboard()
    try:
        ok = win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB)
    finally:
        win32clipboard.CloseClipboard()
    if not ok:
        raise RuntimeError("写入剪贴板后未检测到 DIB 格式")
    return "剪贴板图片读写正常"


def check_pyautogui():
    import pyautogui
    x, y = pyautogui.position()
    return f"pyautogui 可用 (当前鼠标 {x},{y})"


def check_keyboard():
    import keyboard
    _ = keyboard.is_pressed("a")
    return "keyboard 库可用"


def main():
    print("=" * 50)
    print("  秒截图 (Miao Screenshot) - 自检")
    print("=" * 50)

    items = [
        ("依赖导入", check_imports),
        ("多屏识别", check_monitors),
        ("截屏功能", check_capture),
        ("剪贴板写入", check_clipboard),
        ("pyautogui", check_pyautogui),
        ("keyboard 监听", check_keyboard),
    ]

    results = [check(n, f) for n, f in items]

    print("=" * 50)
    if all(results):
        print("✅ 自检通过 - 可以运行 python main.py")
        sys.exit(0)
    else:
        print("❌ 自检失败 - 请按上面提示修复后重试")
        sys.exit(1)


if __name__ == "__main__":
    main()
