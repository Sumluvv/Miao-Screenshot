# -*- coding: utf-8 -*-
"""
鼠标坐标记录小工具
-----------------
用于"点击坐标"发送模式。

使用方法:
  1. python record_pos.py
  2. 把鼠标移动到 AI 网页的"发送按钮"上
  3. 按 空格 记录当前坐标（会显示在控制台）
  4. 按 Esc 退出

记录的坐标手动填到主浮窗 main.py 的"按钮坐标 X / Y"输入框，然后切到"点击坐标"模式即可。
"""

import time
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import pyautogui
    import keyboard
except ImportError as e:
    print("[启动失败] 缺少依赖：", e)
    print("请先运行：pip install -r requirements.txt")
    sys.exit(1)


def main():
    print("=" * 50)
    print("  鼠标坐标记录器")
    print("=" * 50)
    print("  空格 = 记录当前坐标")
    print("  Esc  = 退出")
    print("=" * 50)
    print()

    last_print = ""

    while True:
        if keyboard.is_pressed("esc"):
            print("\n已退出。")
            break

        x, y = pyautogui.position()
        cur = f"当前坐标: X={x:>5}  Y={y:>5}"
        if cur != last_print:
            print(f"\r{cur}", end="", flush=True)
            last_print = cur

        if keyboard.is_pressed("space"):
            print(f"\n[已记录] X={x}, Y={y}  -> 填到主程序 浮窗的坐标输入框")
            time.sleep(0.4)

        time.sleep(0.05)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已中断。")
