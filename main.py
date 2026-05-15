# -*- coding: utf-8 -*-
"""
秒截图 (Miao Screenshot) — 主程序

通用截图 → 剪贴板 →（可选）自动粘贴到前台应用并发送。
支持：整屏 / 指定窗口 / 矩形区域（含「持续使用同一区域」）。
支持：小浮窗模式（仅保留主按钮，减少遮挡）。

版本: 2.0.0
平台: Windows 10/11
仓库: https://github.com/Sumluvv/Miao-Screenshot
"""

import json
import sys
import threading
import time
import traceback
from datetime import datetime
from io import BytesIO
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import tkinter as tk
from tkinter import ttk

try:
    import mss
    from PIL import Image
    import win32clipboard
    import keyboard
    import pyautogui
except ImportError as e:
    print("[启动失败] 缺少依赖：", e)
    print("请先运行：pip install -r requirements.txt")
    sys.exit(1)

import ctypes
from ctypes import wintypes

# ---------- user32 ----------
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.GetForegroundWindow.restype = wintypes.HWND
_user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_user32.GetWindowTextLengthW.restype = ctypes.c_int
_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetWindowTextW.restype = ctypes.c_int
_user32.IsIconic.argtypes = [wintypes.HWND]
_user32.IsIconic.restype = wintypes.BOOL
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.IsWindowVisible.restype = wintypes.BOOL
_user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.ShowWindow.restype = wintypes.BOOL
_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.SetForegroundWindow.restype = wintypes.BOOL
_user32.GetWindow.argtypes = [wintypes.HWND, ctypes.c_uint]
_user32.GetWindow.restype = wintypes.HWND

GW_OWNER = 4
SW_RESTORE = 9


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


_user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
_user32.GetWindowRect.restype = wintypes.BOOL

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
_user32.EnumWindows.restype = wintypes.BOOL

APP_TITLE = "秒截图"
APP_TITLE_EN = "Miao Screenshot"
REPO_URL = "https://github.com/Sumluvv/Miao-Screenshot"

APP_DIR = Path(__file__).parent
CONFIG_FILE = APP_DIR / "config.json"
SCREENSHOT_DIR = APP_DIR / "screenshots"

DEFAULT_CONFIG = {
    "screen_index": 1,
    "auto_send": True,
    "save_backup": False,
    "compress": True,
    "switch_delay": 2.0,
    "upload_delay": 1.5,
    "send_mode": "enter",
    "click_x": 0,
    "click_y": 0,
    "hotkey": "f8",
    "max_width": 1600,
    "opacity": 1.0,
    "topmost_refresh_ms": 2000,
    # v2
    "compact_mode": False,
    "capture_source": "screen",  # screen | window | region
    "capture_window_hwnd": 0,
    "region_left": 0,
    "region_top": 0,
    "region_width": 0,
    "region_height": 0,
    "region_continuous": True,
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(cfg)
            if "delay_seconds" in cfg and "switch_delay" not in cfg:
                merged["switch_delay"] = float(cfg["delay_seconds"])
            merged.pop("delay_seconds", None)
            return merged
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[配置保存失败]", e)


def _mss():
    return mss.MSS() if hasattr(mss, "MSS") else mss.mss()


def list_monitors():
    with _mss() as sct:
        return list(sct.monitors[1:])


def virtual_screen_dict():
    """mss monitors[0] 为虚拟桌面整体矩形"""
    with _mss() as sct:
        return dict(sct.monitors[0])


def capture_screen(screen_index: int = 1) -> Image.Image:
    with _mss() as sct:
        mons = sct.monitors
        if screen_index < 1 or screen_index >= len(mons):
            raise ValueError(f"屏幕序号 {screen_index} 超范围，可用 1~{len(mons)-1}")
        monitor = mons[screen_index]
        sct_img = sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")


def capture_region(left: int, top: int, width: int, height: int) -> Image.Image:
    if width < 2 or height < 2:
        raise ValueError("区域太小")
    area = {"left": int(left), "top": int(top), "width": int(width), "height": int(height)}
    with _mss() as sct:
        sct_img = sct.grab(area)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")


def capture_window(hwnd: int) -> Image.Image:
    rect = RECT()
    if not _user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
        raise ValueError("无法获取窗口矩形（窗口可能已关闭）")
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    if w < 2 or h < 2:
        raise ValueError("窗口太小或已最小化到不可见")
    return capture_region(rect.left, rect.top, w, h)


def capture_from_cfg(cfg: dict) -> Image.Image:
    src = cfg.get("capture_source", "screen")
    if src == "screen":
        return capture_screen(int(cfg.get("screen_index", 1)))
    if src == "window":
        hwnd = int(cfg.get("capture_window_hwnd", 0) or 0)
        if hwnd <= 0:
            raise ValueError("请先在「窗口」模式下选择要截取的窗口")
        return capture_window(hwnd)
    if src == "region":
        w = int(cfg.get("region_width", 0) or 0)
        h = int(cfg.get("region_height", 0) or 0)
        if w < 2 or h < 2:
            raise ValueError("请先「选取区域」，或勾选「持续使用同一区域」并完成一次选取")
        return capture_region(
            int(cfg["region_left"]),
            int(cfg["region_top"]),
            w,
            h,
        )
    raise ValueError(f"未知截取来源: {src}")


def region_rect_valid(cfg: dict) -> bool:
    return int(cfg.get("region_width", 0) or 0) >= 2 and int(cfg.get("region_height", 0) or 0) >= 2


def region_needs_pick(cfg: dict) -> bool:
    if cfg.get("capture_source") != "region":
        return False
    if cfg.get("region_continuous"):
        return not region_rect_valid(cfg)
    return True


def compress_image(image: Image.Image, max_width: int = 1600) -> Image.Image:
    w, h = image.size
    if w <= max_width:
        return image
    ratio = max_width / w
    return image.resize((max_width, int(h * ratio)), Image.LANCZOS)


def save_backup(image: Image.Image) -> Path:
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SCREENSHOT_DIR / f"snap_{ts}.png"
    image.save(path, "PNG", optimize=True)
    return path


def copy_image_to_clipboard(image: Image.Image) -> None:
    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    finally:
        win32clipboard.CloseClipboard()


def get_foreground_window_info():
    try:
        hwnd = _user32.GetForegroundWindow()
        if not hwnd:
            return None, ""
        length = _user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return hwnd, ""
        buf = ctypes.create_unicode_buffer(length + 1)
        _user32.GetWindowTextW(hwnd, buf, length + 1)
        return hwnd, buf.value or ""
    except Exception:
        return None, ""


def activate_window(hwnd) -> bool:
    if not hwnd:
        return False
    try:
        if _user32.IsIconic(hwnd):
            _user32.ShowWindow(hwnd, SW_RESTORE)
        ok = bool(_user32.SetForegroundWindow(hwnd))
        if not ok:
            try:
                keyboard.press_and_release("alt")
                time.sleep(0.05)
                ok = bool(_user32.SetForegroundWindow(hwnd))
            except Exception as e2:
                print(f"[激活窗口] 备用方案异常: {e2}")
                return False
        return ok
    except Exception as e:
        print(f"[激活窗口失败] {e}")
        return False


def enum_top_level_windows():
    """返回 [(hwnd, title), ...] 可见、有标题、非子窗口(owner)"""
    out = []

    @WNDENUMPROC
    def _cb(hwnd, _lparam):
        if not _user32.IsWindowVisible(hwnd):
            return True
        if _user32.GetWindow(hwnd, GW_OWNER):
            return True
        length = _user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        _user32.GetWindowTextW(hwnd, buf, length + 1)
        title = (buf.value or "").strip()
        if not title:
            return True
        if APP_TITLE in title or APP_TITLE_EN in title:
            return True
        out.append((int(hwnd), title))
        return True

    _user32.EnumWindows(_cb, 0)
    out.sort(key=lambda x: x[1].lower())
    return out


def auto_paste_and_send(
    auto_send: bool,
    send_mode: str = "enter",
    click_x: int = 0,
    click_y: int = 0,
    upload_delay: float = 1.5,
    status_cb=None,
) -> None:
    def report(msg):
        print(f"[发送] {msg}")
        if status_cb:
            status_cb(msg)

    report("Ctrl+V 粘贴图片...")
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)

    if not auto_send:
        report("已粘贴，未发送（自动发送未勾选）")
        return

    upload_delay = max(0.0, float(upload_delay))
    if upload_delay > 0:
        report(f"等待 {upload_delay:.1f}s 让图片上传完成...")
        time.sleep(upload_delay)

    if send_mode == "enter":
        report("按回车发送")
        pyautogui.press("enter")
    elif send_mode == "click":
        if click_x > 0 and click_y > 0:
            report(f"点击坐标 ({click_x},{click_y}) 发送")
            pyautogui.click(click_x, click_y)
        else:
            raise ValueError("点击坐标未设置，请用 record_pos.py 记录后填入浮窗")
    else:
        raise ValueError(f"未知发送方式: {send_mode}")


def pick_region_overlay(parent: tk.Tk):
    """
    全虚拟屏半透明覆盖层，拖拽矩形选区；松开鼠标确认，Esc 取消。
    返回 dict: left, top, width, height 或 None
    """
    mon = virtual_screen_dict()
    vx, vy = mon["left"], mon["top"]
    vw, vh = mon["width"], mon["height"]

    done = tk.IntVar(value=0)
    result = {"rect": None}
    start = {"x": 0, "y": 0}
    cur_rect = {"id": None}

    topw = tk.Toplevel(parent)
    topw.title("选取区域")
    topw.attributes("-topmost", True)
    try:
        topw.attributes("-alpha", 0.28)
    except Exception:
        pass
    topw.overrideredirect(True)
    topw.geometry(f"{vw}x{vh}+{vx}+{vy}")

    cv = tk.Canvas(topw, highlightthickness=0, bg="#000000")
    cv.pack(fill="both", expand=True)

    hint = tk.Label(
        topw,
        text="拖拽框选截图区域 | 松开鼠标确认 | Esc 取消",
        fg="white",
        bg="#222",
        font=("Microsoft YaHei", 11),
    )
    hint.place(relx=0.5, y=8, anchor="n")

    def to_screen(ex, ey):
        return int(vx + ex), int(vy + ey)

    def on_press(e):
        start["x"], start["y"] = e.x, e.y
        if cur_rect["id"] is not None:
            cv.delete(cur_rect["id"])
            cur_rect["id"] = None

    def on_drag(e):
        x0, y0 = start["x"], start["y"]
        x1, y1 = e.x, e.y
        if cur_rect["id"] is not None:
            cv.delete(cur_rect["id"])
        cur_rect["id"] = cv.create_rectangle(x0, y0, x1, y1, outline="#00ff88", width=2)

    def on_release(e):
        x0, y0 = start["x"], start["y"]
        x1, y1 = e.x, e.y
        rx0, ry0 = min(x0, x1), min(y0, y1)
        rw, rh = abs(x1 - x0), abs(y1 - y0)
        if rw < 5 or rh < 5:
            return
        sx, sy = to_screen(rx0, ry0)
        result["rect"] = {"left": sx, "top": sy, "width": rw, "height": rh}
        done.set(1)

    def on_esc(_e=None):
        result["rect"] = None
        done.set(1)

    cv.bind("<ButtonPress-1>", on_press)
    cv.bind("<B1-Motion>", on_drag)
    cv.bind("<ButtonRelease-1>", on_release)
    topw.bind("<Escape>", on_esc)
    topw.focus_force()
    parent.wait_variable(done)
    try:
        topw.destroy()
    except Exception:
        pass
    parent.update_idletasks()
    return result["rect"]


def run_pipeline(cfg: dict, status_cb=None, from_hotkey: bool = False) -> str:
    def report(msg):
        print(f"[流程] {msg}")
        if status_cb:
            status_cb(msg)

    src = cfg.get("capture_source", "screen")
    report(f"开始截图 (来源={src})...")
    img = capture_from_cfg(cfg)

    if cfg["compress"]:
        img = compress_image(img, cfg["max_width"])
        report(f"压缩到 {img.size[0]}x{img.size[1]}")

    if cfg["save_backup"]:
        path = save_backup(img)
        report(f"备份: {path.name}")

    copy_image_to_clipboard(img)
    report("已复制到剪贴板")

    if not from_hotkey:
        switch_delay = max(0.0, float(cfg["switch_delay"]))
        if switch_delay > 0:
            report(f"切窗延迟 {switch_delay:.1f}s（按钮模式）...")
            time.sleep(switch_delay)

    auto_paste_and_send(
        auto_send=cfg["auto_send"],
        send_mode=cfg["send_mode"],
        click_x=cfg["click_x"],
        click_y=cfg["click_y"],
        upload_delay=cfg["upload_delay"],
        status_cb=status_cb,
    )

    return "✅ 已粘贴并发送" if cfg["auto_send"] else "✅ 已粘贴（未发送）"


class FloatingApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg = load_config()
        self._busy = False
        self._last_hwnd = None
        self._last_title = ""
        self._window_hwnds: list = []

        self.root.title(f"{APP_TITLE} v2.0")
        self.root.resizable(False, False)
        self.root.geometry("+50+50")

        self.full_frame = ttk.Frame(self.root, padding=8)
        self.mini_frame = ttk.Frame(self.root, padding=6)

        self._build_full_ui(self.full_frame)
        self._build_mini_ui(self.mini_frame)

        if self.cfg.get("compact_mode"):
            self.mini_frame.pack(fill="both", expand=True)
        else:
            self.full_frame.pack(fill="both", expand=True)

        self._apply_window_attrs()
        self._register_hotkey()
        self._schedule_topmost_refresh()
        self._schedule_track_window()

    def _build_mini_ui(self, frame: ttk.Frame):
        row = ttk.Frame(frame)
        row.pack(fill="x")
        self.run_btn_mini = tk.Button(
            row,
            text="📸",
            font=("Microsoft YaHei", 16, "bold"),
            bg="#4CAF50",
            fg="white",
            width=4,
            height=1,
            command=self.trigger_async,
        )
        self.run_btn_mini.pack(side="left", padx=2)
        ttk.Button(row, text="设置", width=6, command=self._expand_from_compact).pack(side="left", padx=2)
        ttk.Label(row, text="F8", foreground="gray").pack(side="left", padx=4)
        self.status_mini = ttk.Label(frame, textvariable=self.status_var, foreground="gray", wraplength=200)
        self.status_mini.pack(fill="x", pady=(4, 0))

    def _build_full_ui(self, frame: ttk.Frame):
        pad = {"padx": 6, "pady": 2}
        row = 0

        self.compact_var = tk.BooleanVar(value=bool(self.cfg.get("compact_mode")))
        ttk.Checkbutton(
            frame,
            text="小浮窗模式（只保留截图按钮）",
            variable=self.compact_var,
            command=self._toggle_compact,
        ).grid(row=row, column=0, columnspan=2, sticky="w", **pad)
        row += 1

        ttk.Separator(frame, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
        row += 1

        ttk.Label(frame, text="截取来源:").grid(row=row, column=0, sticky="w", **pad)
        self.capture_source_var = tk.StringVar(value=self.cfg.get("capture_source", "screen"))
        src_fr = ttk.Frame(frame)
        src_fr.grid(row=row, column=1, sticky="w", **pad)
        for val, lab in (
            ("screen", "整屏"),
            ("window", "窗口"),
            ("region", "区域"),
        ):
            ttk.Radiobutton(
                src_fr,
                text=lab,
                variable=self.capture_source_var,
                value=val,
                command=self._on_source_change,
            ).pack(side="left")
        row += 1

        ttk.Label(frame, text="截取屏幕:").grid(row=row, column=0, sticky="w", **pad)
        self.screen_var = tk.IntVar(value=self.cfg["screen_index"])
        mon_count = max(1, len(list_monitors()))
        screen_frame = ttk.Frame(frame)
        screen_frame.grid(row=row, column=1, sticky="w", **pad)
        for i in range(1, mon_count + 1):
            ttk.Radiobutton(
                screen_frame,
                text=f"屏幕{i}",
                variable=self.screen_var,
                value=i,
                command=self._save_now,
            ).pack(side="left")
        self._screen_row = row
        row += 1

        ttk.Label(frame, text="目标窗口:").grid(row=row, column=0, sticky="nw", **pad)
        win_fr = ttk.Frame(frame)
        win_fr.grid(row=row, column=1, sticky="ew", **pad)
        self.window_combo = ttk.Combobox(win_fr, width=42, state="readonly")
        self.window_combo.pack(side="left")
        ttk.Button(win_fr, text="刷新", width=5, command=self._refresh_window_list).pack(side="left", padx=4)
        self._window_row = row
        row += 1

        reg_fr = ttk.Frame(frame)
        reg_fr.grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        self.region_continuous_var = tk.BooleanVar(value=bool(self.cfg.get("region_continuous", True)))
        ttk.Checkbutton(
            reg_fr,
            text="持续使用同一区域（否则每次截图前都重新框选）",
            variable=self.region_continuous_var,
            command=self._save_now,
        ).pack(anchor="w")
        btn_line = ttk.Frame(reg_fr)
        btn_line.pack(anchor="w", pady=2)
        ttk.Button(btn_line, text="选取区域", command=self._pick_region_clicked).pack(side="left", padx=2)
        ttk.Button(btn_line, text="清除区域", command=self._clear_region_clicked).pack(side="left", padx=2)
        self.region_info_var = tk.StringVar(value=self._region_info_text())
        ttk.Label(reg_fr, textvariable=self.region_info_var, foreground="#555", wraplength=360).pack(anchor="w")
        self._region_row = row
        row += 1

        self.auto_send_var = tk.BooleanVar(value=self.cfg["auto_send"])
        ttk.Checkbutton(
            frame, text="截图后自动发送（粘贴后回车/点击）",
            variable=self.auto_send_var,
            command=self._save_now,
        ).grid(row=row, column=0, columnspan=2, sticky="w", **pad)
        row += 1

        self.save_var = tk.BooleanVar(value=self.cfg["save_backup"])
        ttk.Checkbutton(
            frame, text="保存本地备份 (screenshots/)",
            variable=self.save_var,
            command=self._save_now,
        ).grid(row=row, column=0, columnspan=2, sticky="w", **pad)
        row += 1

        self.compress_var = tk.BooleanVar(value=self.cfg["compress"])
        ttk.Checkbutton(
            frame, text="压缩图片 (上传更快)",
            variable=self.compress_var,
            command=self._save_now,
        ).grid(row=row, column=0, columnspan=2, sticky="w", **pad)
        row += 1

        ttk.Label(frame, text="发送方式:").grid(row=row, column=0, sticky="w", **pad)
        self.send_mode_var = tk.StringVar(value=self.cfg["send_mode"])
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=row, column=1, sticky="w", **pad)
        ttk.Radiobutton(mode_frame, text="回车", variable=self.send_mode_var, value="enter", command=self._save_now).pack(
            side="left"
        )
        ttk.Radiobutton(mode_frame, text="点击坐标", variable=self.send_mode_var, value="click", command=self._save_now).pack(
            side="left"
        )
        row += 1

        coord_frame = ttk.Frame(frame)
        coord_frame.grid(row=row, column=0, columnspan=2, sticky="w", **pad)
        ttk.Label(coord_frame, text="发送按钮坐标 X:").pack(side="left")
        self.x_var = tk.IntVar(value=self.cfg["click_x"])
        ttk.Entry(coord_frame, textvariable=self.x_var, width=6).pack(side="left")
        ttk.Label(coord_frame, text=" Y:").pack(side="left")
        self.y_var = tk.IntVar(value=self.cfg["click_y"])
        ttk.Entry(coord_frame, textvariable=self.y_var, width=6).pack(side="left")
        ttk.Button(coord_frame, text="保存", command=self._save_now, width=5).pack(side="left", padx=4)
        row += 1

        ttk.Separator(frame, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
        row += 1

        ttk.Label(frame, text="切窗延迟(秒)[按钮]:", foreground="#555").grid(row=row, column=0, sticky="w", **pad)
        self.switch_delay_var = tk.DoubleVar(value=self.cfg["switch_delay"])
        ttk.Spinbox(
            frame, from_=0.0, to=10.0, increment=0.5, width=6,
            textvariable=self.switch_delay_var, command=self._save_now,
        ).grid(row=row, column=1, sticky="w", **pad)
        row += 1

        ttk.Label(frame, text="上传等待(秒)[发送前]:", foreground="#c0392b").grid(row=row, column=0, sticky="w", **pad)
        self.upload_delay_var = tk.DoubleVar(value=self.cfg["upload_delay"])
        ttk.Spinbox(
            frame, from_=0.0, to=15.0, increment=0.5, width=6,
            textvariable=self.upload_delay_var, command=self._save_now,
        ).grid(row=row, column=1, sticky="w", **pad)
        row += 1

        ttk.Label(frame, text="浮窗透明度:").grid(row=row, column=0, sticky="w", **pad)
        self.opacity_var = tk.DoubleVar(value=self.cfg["opacity"])
        ttk.Scale(
            frame, from_=0.3, to=1.0, orient="horizontal",
            variable=self.opacity_var, command=self._on_opacity_change,
        ).grid(row=row, column=1, sticky="ew", **pad)
        row += 1

        ttk.Separator(frame, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
        row += 1

        self.run_btn = tk.Button(
            frame,
            text="📸  截 图 并 粘 贴  (F8)",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            command=self.trigger_async,
            width=26,
            height=2,
        )
        self.run_btn.grid(row=row, column=0, columnspan=2, **pad)
        row += 1

        self.status_var = tk.StringVar(value="就绪 — 网测/办公通用，建议 F8")
        self.status_label = ttk.Label(frame, textvariable=self.status_var, foreground="gray", wraplength=380)
        self.status_label.grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        row += 1

        self.target_var = tk.StringVar(value="🎯 目标窗口: (点一下要粘贴的应用输入框)")
        ttk.Label(frame, textvariable=self.target_var, foreground="#1976d2", wraplength=380).grid(
            row=row, column=0, columnspan=2, sticky="w", **pad
        )
        row += 1

        ttk.Label(
            frame,
            text=f"开源: {REPO_URL}",
            foreground="#888",
            cursor="hand2",
        ).grid(row=row, column=0, columnspan=2, sticky="w", **pad)

        self._refresh_window_list(select_hwnd=int(self.cfg.get("capture_window_hwnd", 0) or 0))
        self._update_source_rows_visibility()

    def _region_info_text(self) -> str:
        c = self.cfg
        if region_rect_valid(c):
            return (
                f"当前区域: ({c['region_left']}, {c['region_top']}) "
                f"{c['region_width']}×{c['region_height']}"
            )
        return "当前区域: 未设定"

    def _on_source_change(self):
        self._update_source_rows_visibility()
        self._save_now()

    def _update_source_rows_visibility(self):
        src = self.capture_source_var.get()
        full = self.full_frame
        for w in full.grid_slaves(row=self._screen_row):
            if int(w.grid_info().get("column", -1)) >= 0:
                if src == "screen":
                    w.grid()
                else:
                    w.grid_remove()
        for w in full.grid_slaves(row=self._window_row):
            if src == "window":
                w.grid()
            else:
                w.grid_remove()
        for w in full.grid_slaves(row=self._region_row):
            if src == "region":
                w.grid()
            else:
                w.grid_remove()

    def _refresh_window_list(self, select_hwnd: int = 0):
        pairs = enum_top_level_windows()
        self._window_hwnds = [p[0] for p in pairs]
        labels = []
        for hwnd, title in pairs:
            short = title if len(title) <= 48 else title[:45] + "..."
            labels.append(f"{short}  [{hwnd}]")
        self.window_combo["values"] = labels
        if select_hwnd and select_hwnd in self._window_hwnds:
            idx = self._window_hwnds.index(select_hwnd)
            self.window_combo.current(idx)
        elif labels:
            self.window_combo.current(0)
        else:
            self.window_combo.set("")
        self._save_now()

    def _pick_region_clicked(self):
        rect = pick_region_overlay(self.root)
        if not rect:
            self._set_status("已取消选取区域", "gray")
            return
        self.cfg["region_left"] = rect["left"]
        self.cfg["region_top"] = rect["top"]
        self.cfg["region_width"] = rect["width"]
        self.cfg["region_height"] = rect["height"]
        self.region_info_var.set(self._region_info_text())
        self._save_now()
        self._set_status("区域已保存", "green")

    def _clear_region_clicked(self):
        self.cfg["region_left"] = 0
        self.cfg["region_top"] = 0
        self.cfg["region_width"] = 0
        self.cfg["region_height"] = 0
        self.region_info_var.set(self._region_info_text())
        self._save_now()
        self._set_status("已清除区域", "gray")

    def _apply_region_from_dict(self, rect: dict):
        self.cfg["region_left"] = int(rect["left"])
        self.cfg["region_top"] = int(rect["top"])
        self.cfg["region_width"] = int(rect["width"])
        self.cfg["region_height"] = int(rect["height"])
        if hasattr(self, "region_info_var"):
            self.region_info_var.set(self._region_info_text())

    def _toggle_compact(self):
        on = bool(self.compact_var.get())
        self.cfg["compact_mode"] = on
        save_config(self.cfg)
        if on:
            self.full_frame.pack_forget()
            self.mini_frame.pack(fill="both", expand=True)
            try:
                self.root.geometry("+50+50")
            except Exception:
                pass
        else:
            self.mini_frame.pack_forget()
            self.full_frame.pack(fill="both", expand=True)

    def _expand_from_compact(self):
        self.compact_var.set(False)
        self._toggle_compact()

    def _apply_window_attrs(self):
        try:
            self.root.attributes("-topmost", True)
        except Exception:
            pass
        try:
            self.root.attributes("-alpha", float(self.cfg["opacity"]))
        except Exception:
            pass

    def _schedule_topmost_refresh(self):
        interval = int(self.cfg.get("topmost_refresh_ms", 2000))
        try:
            self.root.attributes("-topmost", True)
        except Exception:
            pass
        self.root.after(interval, self._schedule_topmost_refresh)

    def _schedule_track_window(self):
        try:
            hwnd, title = get_foreground_window_info()
            if hwnd and title and not self._is_self_window(title):
                if hwnd != self._last_hwnd:
                    self._last_hwnd = hwnd
                    self._last_title = title
                    short = title if len(title) <= 38 else title[:35] + "..."
                    if hasattr(self, "target_var"):
                        self.target_var.set(f"🎯 目标窗口: {short}")
        except Exception as e:
            print(f"[窗口跟踪] {e}")
        self.root.after(300, self._schedule_track_window)

    def _is_self_window(self, title: str) -> bool:
        if not title:
            return True
        for key in (APP_TITLE, APP_TITLE_EN, "网测截图助手"):
            if key in title:
                return True
        return False

    def _on_opacity_change(self, val):
        try:
            op = float(val)
            self.root.attributes("-alpha", op)
            self.cfg["opacity"] = op
            save_config(self.cfg)
        except Exception as e:
            print("[透明度调整失败]", e)

    def _collect_cfg(self) -> dict:
        cfg = self.cfg.copy()
        cfg["compact_mode"] = bool(self.compact_var.get())
        cfg["capture_source"] = str(self.capture_source_var.get())
        cfg["screen_index"] = int(self.screen_var.get())
        cfg["auto_send"] = bool(self.auto_send_var.get())
        cfg["save_backup"] = bool(self.save_var.get())
        cfg["compress"] = bool(self.compress_var.get())
        cfg["switch_delay"] = float(self.switch_delay_var.get())
        cfg["upload_delay"] = float(self.upload_delay_var.get())
        cfg["opacity"] = float(self.opacity_var.get())
        cfg["send_mode"] = str(self.send_mode_var.get())
        cfg["region_continuous"] = bool(self.region_continuous_var.get())
        try:
            cfg["click_x"] = int(self.x_var.get())
            cfg["click_y"] = int(self.y_var.get())
        except Exception:
            cfg["click_x"], cfg["click_y"] = 0, 0
        idx = self.window_combo.current()
        if idx is not None and idx >= 0 and idx < len(self._window_hwnds):
            cfg["capture_window_hwnd"] = int(self._window_hwnds[idx])
        else:
            cfg["capture_window_hwnd"] = 0
        if cfg["capture_source"] == "region":
            cfg["region_left"] = int(self.cfg.get("region_left", 0))
            cfg["region_top"] = int(self.cfg.get("region_top", 0))
            cfg["region_width"] = int(self.cfg.get("region_width", 0))
            cfg["region_height"] = int(self.cfg.get("region_height", 0))
        return cfg

    def _save_now(self):
        self.cfg = self._collect_cfg()
        save_config(self.cfg)

    def _set_status(self, msg: str, color: str = "gray"):
        self.status_var.set(msg)
        if hasattr(self, "status_label"):
            self.status_label.configure(foreground=color)
        if hasattr(self, "status_mini"):
            self.status_mini.configure(foreground=color)

    def _set_status_safe(self, msg: str, color: str = "gray"):
        self.root.after(0, lambda: self._set_status(msg, color))

    def _maybe_pick_region_before_run(self) -> bool:
        """主线程调用。若需要框选则弹出覆盖层。返回 False 表示取消。"""
        self._save_now()
        cfg = self._collect_cfg()
        if not region_needs_pick(cfg):
            return True
        self._busy = True
        self._set_status("请拖拽框选截图区域…", "blue")
        try:
            rect = pick_region_overlay(self.root)
        finally:
            self._busy = False
        if not rect:
            self._set_status("已取消", "gray")
            return False
        self._apply_region_from_dict(rect)
        self._save_now()
        return True

    def trigger_async(self):
        if self._busy:
            return
        if not self._maybe_pick_region_before_run():
            return
        self._busy = True
        self._save_now()
        cfg = self._collect_cfg()
        for b in (getattr(self, "run_btn", None), getattr(self, "run_btn_mini", None)):
            if b is not None:
                b.configure(state="disabled")
        self._set_status("运行中…", "blue")
        threading.Thread(target=lambda: self._worker_button(cfg), daemon=True).start()

    def _worker_button(self, cfg: dict):
        try:
            report = lambda m: self._set_status_safe(m, "blue")
            report(f"截图({cfg.get('capture_source')})…")
            img = capture_from_cfg(cfg)
            if cfg["compress"]:
                img = compress_image(img, cfg["max_width"])
                report(f"压缩 {img.size[0]}×{img.size[1]}")
            if cfg["save_backup"]:
                path = save_backup(img)
                report(f"备份 {path.name}")
            copy_image_to_clipboard(img)
            report("已复制到剪贴板")

            if self._last_hwnd:
                short = (self._last_title or "")[:28]
                report(f"切换到: {short}…")
                ok = activate_window(self._last_hwnd)
                if ok:
                    time.sleep(0.4)
                else:
                    report("⚠️ 自动切窗失败，使用切窗延迟")
                    time.sleep(max(1.0, float(cfg["switch_delay"])))
            else:
                sw = float(cfg["switch_delay"])
                report(f"未记录目标，等待 {sw}s …")
                time.sleep(sw)

            auto_paste_and_send(
                auto_send=cfg["auto_send"],
                send_mode=cfg["send_mode"],
                click_x=cfg["click_x"],
                click_y=cfg["click_y"],
                upload_delay=cfg["upload_delay"],
                status_cb=report,
            )
            msg = "✅ 已粘贴并发送" if cfg["auto_send"] else "✅ 已粘贴（未发送）"
            self._set_status_safe(msg, "green")
        except Exception as e:
            err = f"❌ 失败: {e}"
            print(err)
            traceback.print_exc()
            self._set_status_safe(err, "red")
        finally:
            self.root.after(800, self._after_run)

    def _after_run(self):
        self._busy = False
        for b in (getattr(self, "run_btn", None), getattr(self, "run_btn_mini", None)):
            if b is not None:
                b.configure(state="normal")

    def _register_hotkey(self):
        hk = self.cfg.get("hotkey", "f8")
        try:
            keyboard.add_hotkey(hk, self._on_hotkey)
            print(f"[快捷键] 已注册: {hk}")
        except Exception as e:
            print(f"[快捷键] 注册失败: {e}")

    def _on_hotkey(self):
        if self._busy:
            return

        def on_main():
            if self._busy:
                return
            self._save_now()
            cfg0 = self._collect_cfg()
            if region_needs_pick(cfg0):
                self._busy = True
                self._set_status("F8: 请框选区域…", "blue")
                try:
                    rect = pick_region_overlay(self.root)
                finally:
                    self._busy = False
                if not rect:
                    self._set_status("已取消", "gray")
                    return
                self._apply_region_from_dict(rect)
                self._save_now()
            cfg = self._collect_cfg()
            self._busy = True
            self._set_status("运行中(F8)…", "blue")

            def worker():
                try:
                    msg = run_pipeline(
                        cfg,
                        status_cb=lambda m: self._set_status_safe(m, "blue"),
                        from_hotkey=True,
                    )
                    self._set_status_safe(msg, "green")
                except Exception as e:
                    err = f"❌ 失败: {e}"
                    print(err)
                    traceback.print_exc()
                    self._set_status_safe(err, "red")
                finally:
                    self.root.after(800, lambda: setattr(self, "_busy", False))

            threading.Thread(target=worker, daemon=True).start()

        self.root.after(0, on_main)


def main():
    try:
        pyautogui.FAILSAFE = False
    except Exception:
        pass

    root = tk.Tk()
    FloatingApp(root)

    def on_close():
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
