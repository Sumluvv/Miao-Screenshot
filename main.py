# -*- coding: utf-8 -*-
"""
分屏截屏助手 (Split Screen Snap)

多屏截图 → 剪贴板 →（可选）自动粘贴到输入框并发送。
支持：整屏 / 窗口(Windows) / 区域 / 小浮窗模式。

仓库: https://github.com/Sumluvv/Miao-Screenshot
"""

import json
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import ctypes
from datetime import datetime
from io import BytesIO
from pathlib import Path


def _early_enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


_early_enable_dpi_awareness()

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import tkinter as tk
from tkinter import ttk

from app_meta import (
    APP_DIR,
    APP_NAME,
    APP_NAME_EN,
    ASSETS_DIR,
    CONFIG_FILE,
    IS_MAC,
    IS_WINDOWS,
    REPO_URL,
    SCREENSHOT_DIR,
    VERSION,
    get_app_dir,
)
from ui_theme import (
    Theme,
    apply_app_theme,
    style_listbox,
    style_mini_button,
    style_primary_button,
    style_secondary_button,
)

try:
    import mss
    from PIL import Image
    import pyautogui
except ImportError as e:
    print("[启动失败] 缺少依赖：", e)
    print("请先运行：pip install -r requirements.txt")
    sys.exit(1)

try:
    import keyboard
except ImportError:
    keyboard = None

if IS_WINDOWS:
    try:
        import win32clipboard
    except ImportError as e:
        print("[启动失败] Windows 需要 pywin32：", e)
        sys.exit(1)
else:
    win32clipboard = None

from ctypes import wintypes


# ---------- Windows user32 / gdi32（仅 Win）----------
GW_OWNER = 4
SW_RESTORE = 9
PW_CLIENTONLY = 0x00000001
PW_RENDERFULLCONTENT = 0x00000002
DIB_RGB_COLORS = 0
BI_RGB = 0
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
ENUM_CURRENT_SETTINGS = -1
_enum_windows_cb_ref = None
_monitor_enum_proc_ref = None
_display_monitors_cache = None

if IS_WINDOWS:

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
            ("szDevice", wintypes.WCHAR * 32),
        ]

    class DEVMODEW(ctypes.Structure):
        _fields_ = [
            ("dmDeviceName", wintypes.WCHAR * 32),
            ("dmSpecVersion", wintypes.WORD),
            ("dmDriverVersion", wintypes.WORD),
            ("dmSize", wintypes.WORD),
            ("dmDriverExtra", wintypes.WORD),
            ("dmFields", wintypes.DWORD),
            ("dmPositionX", wintypes.LONG),
            ("dmPositionY", wintypes.LONG),
            ("dmDisplayOrientation", wintypes.DWORD),
            ("dmDisplayFixedOutput", wintypes.DWORD),
            ("dmColor", wintypes.SHORT),
            ("dmDuplex", wintypes.SHORT),
            ("dmYResolution", wintypes.SHORT),
            ("dmTTOption", wintypes.SHORT),
            ("dmCollate", wintypes.SHORT),
            ("dmFormName", wintypes.WCHAR * 32),
            ("dmLogPixels", wintypes.WORD),
            ("dmBitsPerPel", wintypes.DWORD),
            ("dmPelsWidth", wintypes.DWORD),
            ("dmPelsHeight", wintypes.DWORD),
            ("dmDisplayFlags", wintypes.DWORD),
            ("dmDisplayFrequency", wintypes.DWORD),
        ]

    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
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
    _gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    _gdi32.CreateCompatibleDC.restype = wintypes.HDC
    _gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    _gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    _gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    _gdi32.SelectObject.restype = wintypes.HGDIOBJ
    _gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    _gdi32.DeleteObject.restype = wintypes.BOOL
    _gdi32.DeleteDC.argtypes = [wintypes.HDC]
    _gdi32.DeleteDC.restype = wintypes.BOOL
    _gdi32.GetDIBits.argtypes = [
        wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
        ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT,
    ]
    _gdi32.GetDIBits.restype = ctypes.c_int
    _user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
    _user32.GetWindowRect.restype = wintypes.BOOL
    _user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
    _user32.GetClientRect.restype = wintypes.BOOL
    _user32.GetWindowDC.argtypes = [wintypes.HWND]
    _user32.GetWindowDC.restype = wintypes.HDC
    _user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    _user32.ReleaseDC.restype = ctypes.c_int
    _user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
    _user32.PrintWindow.restype = wintypes.BOOL
    _user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.GetClassNameW.restype = ctypes.c_int
    _user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    _user32.GetWindowLongW.restype = ctypes.c_long
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    _user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    _user32.EnumWindows.restype = wintypes.BOOL
    MONITORINFOF_PRIMARY = 1
    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM,
    )
    _user32.EnumDisplayMonitors.argtypes = [
        wintypes.HDC, ctypes.POINTER(RECT), MONITORENUMPROC, wintypes.LPARAM,
    ]
    _user32.EnumDisplayMonitors.restype = wintypes.BOOL
    _user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFOEXW)]
    _user32.GetMonitorInfoW.restype = wintypes.BOOL
    _user32.EnumDisplaySettingsW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(DEVMODEW)]
    _user32.EnumDisplaySettingsW.restype = wintypes.BOOL
else:
    BITMAPINFOHEADER = RECT = MONITORINFOEXW = DEVMODEW = None  # type: ignore
    _user32 = _gdi32 = None
    WNDENUMPROC = MONITORENUMPROC = None  # type: ignore
    MONITORINFOF_PRIMARY = 1

# 无标题时的类名 → 显示名
_CLASS_FRIENDLY = {
    "Chrome_WidgetWin_1": "Google Chrome",
    "Chrome_WidgetWin_0": "Google Chrome",
    "MozillaWindowClass": "Firefox",
    "ApplicationFrameWindow": "UWP 应用",
    "CabinetWClass": "资源管理器",
    "ExploreWClass": "资源管理器",
    "Notepad": "记事本",
    "TkTopLevel": "Tk 窗口",
}

# 不适合截图的系统壳窗口（标题完全匹配时跳过）
_SKIP_TITLES = frozenset({
    "Program Manager",
    "Windows Input Experience",
    "Microsoft Text Input Application",
})

_SKIP_CLASSES = frozenset({
    "Shell_TrayWnd",
    "Shell_SecondaryTrayWnd",
    "Progman",
    "WorkerW",
    "DV2ControlHost",
    "EdgeUiInputTopWndClass",
})

# 兼容旧代码中的名称
APP_TITLE = APP_NAME
APP_TITLE_EN = APP_NAME_EN

DEFAULT_CONFIG = {
    "screen_index": 0,
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
    "window_x": -1,
    "window_y": -1,
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


def _label_monitors(raw: list) -> list:
    raw.sort(key=lambda m: (m["left"], m["top"]))
    for i, m in enumerate(raw, 1):
        tag = "主屏" if m.get("primary") else "副屏"
        source = m.get("source", "")
        source_label = f" · {source}" if source else ""
        m["index"] = i
        m["label"] = f"屏幕{i}  {m['width']}×{m['height']}  [{tag}]{source_label}"
    return raw


def _get_mss_monitors() -> list:
    with _mss() as sct:
        raw = [dict(m) for m in sct.monitors[1:]]
        for i, m in enumerate(raw):
            m["primary"] = bool(m.get("is_primary", i == 0))
            m["source"] = "mss"
    return raw


def _get_windows_display_settings_monitors() -> list:
    if not IS_WINDOWS:
        return []
    raw = []

    @MONITORENUMPROC
    def _enum_proc(hmon, _hdc, _rect, _lparam):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if not _user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            return True

        dev = DEVMODEW()
        dev.dmSize = ctypes.sizeof(DEVMODEW)
        ok = bool(_user32.EnumDisplaySettingsW(info.szDevice, ENUM_CURRENT_SETTINGS, ctypes.byref(dev)))
        if ok and int(dev.dmPelsWidth) >= 8 and int(dev.dmPelsHeight) >= 8:
            raw.append({
                "left": int(dev.dmPositionX),
                "top": int(dev.dmPositionY),
                "width": int(dev.dmPelsWidth),
                "height": int(dev.dmPelsHeight),
                "primary": bool(info.dwFlags & MONITORINFOF_PRIMARY),
                "device": str(info.szDevice),
                "source": "系统",
            })
            return True

        r = info.rcMonitor
        w, h = int(r.right - r.left), int(r.bottom - r.top)
        if w >= 8 and h >= 8:
            raw.append({
                "left": int(r.left),
                "top": int(r.top),
                "width": w,
                "height": h,
                "primary": bool(info.dwFlags & MONITORINFOF_PRIMARY),
                "device": str(info.szDevice),
                "source": "系统",
            })
        return True

    global _monitor_enum_proc_ref
    _monitor_enum_proc_ref = _enum_proc
    if _user32.EnumDisplayMonitors(None, None, _enum_proc, 0):
        return raw
    return []


def get_display_monitors(refresh: bool = False) -> list:
    """
    枚举显示器，按从左到右、从上到下排序。
    返回 [{"left","top","width","height","primary","label"}, ...]
    屏幕 1、2… 与 UI 单选一致；截屏用物理像素矩形（修复多屏/DPI 下截不全）。
    """
    global _display_monitors_cache, _monitor_enum_proc_ref
    if _display_monitors_cache is not None and not refresh:
        return _display_monitors_cache

    if IS_WINDOWS:
        raw = _get_windows_display_settings_monitors()
        if not raw:
            raw = _get_mss_monitors()
    else:
        raw = _get_mss_monitors()

    _display_monitors_cache = _label_monitors(raw)
    return _display_monitors_cache


def list_monitors():
    """兼容旧调用：返回显示器区域字典列表"""
    return [
        {k: m[k] for k in ("left", "top", "width", "height")}
        for m in get_display_monitors()
    ]


def virtual_screen_dict():
    """虚拟桌面整体矩形。Windows 优先用系统显示器模式合成，避免 mss 枚举缩放误差。"""
    monitors = get_display_monitors()
    if monitors:
        left = min(int(m["left"]) for m in monitors)
        top = min(int(m["top"]) for m in monitors)
        right = max(int(m["left"]) + int(m["width"]) for m in monitors)
        bottom = max(int(m["top"]) + int(m["height"]) for m in monitors)
        return {"left": left, "top": top, "width": right - left, "height": bottom - top}
    with _mss() as sct:
        return dict(sct.monitors[0])


def capture_screen(screen_index: int = 1) -> Image.Image:
    if int(screen_index) == 0:
        area = virtual_screen_dict()
        area = {
            "left": int(area["left"]),
            "top": int(area["top"]),
            "width": int(area["width"]),
            "height": int(area["height"]),
        }
        with _mss() as sct:
            sct_img = sct.grab(area)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    monitors = get_display_monitors()
    if screen_index < 1 or screen_index > len(monitors):
        raise ValueError(f"屏幕序号 {screen_index} 超范围，当前共 {len(monitors)} 个屏幕")
    m = monitors[screen_index - 1]
    area = {
        "left": int(m["left"]),
        "top": int(m["top"]),
        "width": int(m["width"]),
        "height": int(m["height"]),
    }
    with _mss() as sct:
        sct_img = sct.grab(area)
    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
    if img.size != (area["width"], area["height"]):
        print(
            f"[整屏截图] 屏幕{screen_index} 期望 {area['width']}×{area['height']}，"
            f"实际 {img.size[0]}×{img.size[1]}"
        )
    return img


def capture_region(left: int, top: int, width: int, height: int) -> Image.Image:
    if width < 2 or height < 2:
        raise ValueError("区域太小")
    area = {"left": int(left), "top": int(top), "width": int(width), "height": int(height)}
    with _mss() as sct:
        sct_img = sct.grab(area)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")


def _get_window_rect_screen(hwnd: int) -> RECT:
    """窗口在屏幕上的外接矩形（优先 DWM 扩展边框，与肉眼所见一致）"""
    rect = RECT()
    try:
        dwm = ctypes.WinDLL("dwmapi")
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        dwm.DwmGetWindowAttribute.argtypes = [
            wintypes.HWND, wintypes.DWORD, ctypes.POINTER(RECT), wintypes.DWORD,
        ]
        dwm.DwmGetWindowAttribute.restype = ctypes.HRESULT
        if dwm.DwmGetWindowAttribute(
            wintypes.HWND(hwnd), DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(rect), ctypes.sizeof(rect),
        ) == 0:
            if rect.right > rect.left and rect.bottom > rect.top:
                return rect
    except Exception:
        pass
    if not _user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
        raise ValueError("无法获取窗口矩形（窗口可能已关闭）")
    return rect


def _image_mostly_black(img: Image.Image, threshold: float = 12.0) -> bool:
    """判断是否为无效黑屏（PrintWindow 失败时常见）"""
    if img.width < 2 or img.height < 2:
        return True
    sample = img.resize((min(80, img.width), min(80, img.height)))
    pixels = list(sample.getdata())
    if not pixels:
        return True
    total = sum(p[0] + p[1] + p[2] for p in pixels)
    return (total / (len(pixels) * 3.0)) < threshold


def _capture_window_printwindow(hwnd: int, client_only: bool = False) -> Image.Image:
    """
    用 PrintWindow 把窗口内容画到内存位图（可截 Chrome/Edge 等 GPU 合成窗口）。
    client_only: True 只截客户区（无标题栏）
    """
    hwnd = wintypes.HWND(int(hwnd))
    rect = RECT()
    if client_only:
        if not _user32.GetClientRect(hwnd, ctypes.byref(rect)):
            raise ValueError("无法获取窗口客户区")
    else:
        if not _user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            raise ValueError("无法获取窗口矩形")
    w, h = rect.right - rect.left, rect.bottom - rect.top
    if w < 2 or h < 2:
        raise ValueError("窗口太小或已最小化")

    hwnd_dc = _user32.GetWindowDC(hwnd)
    if not hwnd_dc:
        raise ValueError("GetWindowDC 失败")
    mem_dc = None
    bmp = None
    old_obj = None
    try:
        mem_dc = _gdi32.CreateCompatibleDC(hwnd_dc)
        if not mem_dc:
            raise ValueError("CreateCompatibleDC 失败")
        bmp = _gdi32.CreateCompatibleBitmap(hwnd_dc, w, h)
        if not bmp:
            raise ValueError("CreateCompatibleBitmap 失败")
        old_obj = _gdi32.SelectObject(mem_dc, bmp)

        flags = PW_CLIENTONLY if client_only else 0
        ok = bool(_user32.PrintWindow(hwnd, mem_dc, flags | PW_RENDERFULLCONTENT))
        if not ok:
            ok = bool(_user32.PrintWindow(hwnd, mem_dc, flags))
        if not ok:
            raise ValueError("PrintWindow 失败")

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = w
        bmi.biHeight = -h  # 自上而下
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = BI_RGB

        buf_size = w * h * 4
        buffer = ctypes.create_string_buffer(buf_size)
        lines = _gdi32.GetDIBits(
            mem_dc, bmp, 0, h, buffer, ctypes.byref(bmi), DIB_RGB_COLORS,
        )
        if lines == 0:
            raise ValueError("GetDIBits 失败")

        return Image.frombuffer("RGB", (w, h), bytes(buffer), "raw", "BGRX", 0, 1)
    finally:
        if mem_dc and old_obj:
            _gdi32.SelectObject(mem_dc, old_obj)
        if bmp:
            _gdi32.DeleteObject(bmp)
        if mem_dc:
            _gdi32.DeleteDC(mem_dc)
        _user32.ReleaseDC(hwnd, hwnd_dc)


def capture_window(hwnd: int) -> Image.Image:
    """
    截取指定 hwnd 窗口。
    优先 PrintWindow（避免 GPU 窗口黑屏）；失败或全黑时再尝试屏幕区域截取。
    """
    if not IS_WINDOWS:
        raise RuntimeError("窗口截图仅支持 Windows")
    hwnd = int(hwnd)
    if _user32.IsIconic(wintypes.HWND(hwnd)):
        _user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)
        time.sleep(0.25)

    # 客户区对多数应用更稳；完整窗口含标题栏
    attempts = [
        ("PrintWindow 客户区", lambda: _capture_window_printwindow(hwnd, True)),
        ("PrintWindow 完整窗口", lambda: _capture_window_printwindow(hwnd, False)),
    ]
    last_err = None
    for name, fn in attempts:
        try:
            img = fn()
            if not _image_mostly_black(img):
                print(f"[窗口截图] 成功: {name} {img.size}")
                return img
            print(f"[窗口截图] {name} 结果偏黑，尝试下一方案…")
            last_err = ValueError(f"{name} 得到黑屏")
        except Exception as e:
            print(f"[窗口截图] {name} 失败: {e}")
            last_err = e

    rect = _get_window_rect_screen(hwnd)
    w, h = rect.right - rect.left, rect.bottom - rect.top
    try:
        img = capture_region(rect.left, rect.top, w, h)
        if not _image_mostly_black(img):
            print("[窗口截图] 回退: 屏幕区域截取")
            return img
    except Exception as e:
        last_err = e

    raise ValueError(
        "窗口截图失败（得到黑屏）。请确保目标窗口未最小化、未被完全遮挡；"
        "浏览器可尝试先点一下该窗口再截图。详情: " + str(last_err)
    )


def capture_from_cfg(cfg: dict) -> Image.Image:
    src = cfg.get("capture_source", "screen")
    if src == "screen":
        return capture_screen(int(cfg.get("screen_index", 0)))
    if src == "window":
        if not IS_WINDOWS:
            raise ValueError("窗口截图目前仅支持 Windows，请改用「整屏」或「区域」")
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
    if IS_WINDOWS:
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
        return
    if IS_MAC:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            path = tmp.name
        image.save(path, "PNG")
        script = f'set the clipboard to (read (POSIX file "{path}") as «class PNGf»)'
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            pass
        return
    raise RuntimeError("当前系统不支持剪贴板图片写入")


def get_foreground_window_info():
    if not IS_WINDOWS:
        return None, ""
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
    if not IS_WINDOWS or not hwnd:
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


def _get_window_class(hwnd) -> str:
    buf = ctypes.create_unicode_buffer(256)
    if _user32.GetClassNameW(hwnd, buf, 256) <= 0:
        return ""
    return buf.value or ""


def _get_window_display_name(hwnd) -> str:
    length = _user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buf = ctypes.create_unicode_buffer(length + 1)
        _user32.GetWindowTextW(hwnd, buf, length + 1)
        title = (buf.value or "").strip()
        if title:
            return title
    cls = _get_window_class(hwnd)
    if cls in _CLASS_FRIENDLY:
        return _CLASS_FRIENDLY[cls]
    if cls:
        return f"[{cls}]"
    return f"窗口 {int(hwnd)}"


def _window_rect_size(hwnd) -> tuple:
    rect = RECT()
    if not _user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
        return 0, 0
    return rect.right - rect.left, rect.bottom - rect.top


def _should_skip_capture_window(hwnd, display_name: str) -> bool:
    if not _user32.IsWindowVisible(hwnd):
        return True
    if _user32.GetWindow(hwnd, GW_OWNER):
        return True
    cls = _get_window_class(hwnd)
    if cls in _SKIP_CLASSES:
        return True
    w, h = _window_rect_size(hwnd)
    if w < 8 or h < 8:
        return True
    if display_name in _SKIP_TITLES:
        return True
    for key in (APP_TITLE, APP_TITLE_EN, "网测截图助手"):
        if key in display_name:
            return True
    return False


def enum_top_level_windows():
    """返回 [(hwnd, display_name), ...] 当前可见、可截图的顶层窗口"""
    if not IS_WINDOWS:
        return []
    global _enum_windows_cb_ref
    out = []
    seen = set()

    @WNDENUMPROC
    def _cb(hwnd, _lparam):
        hwnd = int(hwnd)
        name = _get_window_display_name(hwnd)
        if _should_skip_capture_window(hwnd, name):
            return True
        key = (hwnd, name)
        if key in seen:
            return True
        seen.add(key)
        out.append((hwnd, name))
        return True

    _enum_windows_cb_ref = _cb
    if not _user32.EnumWindows(_cb, 0):
        print("[窗口枚举] EnumWindows 调用失败")
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

        apply_app_theme(self.root)
        self.root.title(f"{APP_NAME}  v{VERSION}")
        self.root.resizable(False, False)
        ico = ASSETS_DIR / ("icon.ico" if IS_WINDOWS else "icon.png")
        if ico.exists():
            try:
                self.root.iconbitmap(str(ico))
            except Exception:
                pass

        self.status_var = tk.StringVar(value="就绪")

        self.full_frame = ttk.Frame(self.root, padding=18)
        self.mini_frame = ttk.Frame(self.root, padding=10)

        self._build_full_ui(self.full_frame)
        self._build_mini_ui(self.mini_frame)

        if self.cfg.get("compact_mode"):
            self.mini_frame.pack(fill="both", expand=True)
        else:
            self.full_frame.pack(fill="both", expand=True)

        self._load_window_geometry()
        self._apply_window_attrs()
        self._register_hotkey()
        self._schedule_topmost_refresh()
        self._schedule_track_window()

    def _build_mini_ui(self, frame: ttk.Frame):
        row = ttk.Frame(frame)
        row.pack(fill="x")
        self.run_btn_mini = tk.Button(row, text="截图", width=7, height=1, command=self.trigger_async)
        style_mini_button(self.run_btn_mini)
        self.run_btn_mini.pack(side="left", padx=(0, 6))
        self.settings_btn_mini = tk.Button(row, text="设置", width=7, command=self._expand_from_compact)
        style_secondary_button(self.settings_btn_mini)
        self.settings_btn_mini.pack(side="left")
        ttk.Label(row, text="F8", style="Muted.TLabel").pack(side="left", padx=8)
        self.status_mini = ttk.Label(frame, textvariable=self.status_var, style="Status.TLabel", wraplength=220)
        self.status_mini.pack(fill="x", pady=(6, 0))

    def _build_full_ui(self, frame: ttk.Frame):
        pad = {"padx": 10, "pady": 5}
        row = 0

        hdr = tk.Frame(frame, bg=Theme.BG, bd=0)
        hdr.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        hdr.grid_columnconfigure(0, weight=1)
        title_col = tk.Frame(hdr, bg=Theme.BG)
        title_col.grid(row=0, column=0, sticky="ew")
        tk.Label(
            title_col,
            text="Split Screen Snap",
            bg=Theme.BG,
            fg=Theme.TEXT,
            font=Theme.FONT_TITLE,
            anchor="w",
        ).pack(anchor="w")
        plat = "Windows 完整功能" if IS_WINDOWS else "macOS（整屏/区域）"
        tk.Label(
            title_col,
            text=f"{APP_NAME} · 多屏截图 · 自动粘贴发送 · {plat}",
            bg=Theme.BG,
            fg=Theme.TEXT_MUTED,
            font=Theme.FONT_SUB,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))
        hotkey = tk.Label(
            hdr,
            text="F8",
            bg=Theme.PRIMARY,
            fg=Theme.PRIMARY_FG,
            font=Theme.FONT_BTN,
            padx=14,
            pady=5,
        )
        hotkey.grid(row=0, column=1, padx=(12, 0), pady=(2, 0))
        row += 1

        card_cap = tk.Frame(frame, bg=Theme.CARD, highlightbackground=Theme.SEPARATOR, highlightthickness=1, bd=0)
        card_cap.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        row += 1
        cap_inner = ttk.Frame(card_cap, padding=14, style="Card.TFrame")
        cap_inner.pack(fill="both", expand=True)
        self._cap_inner = cap_inner
        cr = 0
        ttk.Label(cap_inner, text="截图", style="Card.TLabel", font=(Theme.FONT_UI[0], 11, "bold")).grid(
            row=cr, column=0, sticky="w", **pad
        )
        ttk.Label(cap_inner, text="默认截取全部屏幕，也可指定单个显示器。", style="CardMuted.TLabel").grid(
            row=cr, column=1, sticky="w", **pad
        )
        cr += 1

        ttk.Label(cap_inner, text="来源", style="Card.TLabel").grid(row=cr, column=0, sticky="w", **pad)
        self.capture_source_var = tk.StringVar(value=self.cfg.get("capture_source", "screen"))
        src_fr = ttk.Frame(cap_inner, style="Card.TFrame")
        src_fr.grid(row=cr, column=1, sticky="w", **pad)
        src_items = [("screen", "整屏"), ("region", "区域")]
        if IS_WINDOWS:
            src_items.insert(1, ("window", "窗口"))
        for val, lab in src_items:
            ttk.Radiobutton(
                src_fr, text=lab, variable=self.capture_source_var,
                value=val, command=self._on_source_change,
            ).pack(side="left", padx=(0, 8))
        cr += 1

        self._screen_label = ttk.Label(cap_inner, text="显示器", style="Card.TLabel")
        self._screen_label.grid(row=cr, column=0, sticky="nw", **pad)
        self.screen_var = tk.IntVar(value=self.cfg["screen_index"])
        self._screen_col = ttk.Frame(cap_inner, style="Card.TFrame")
        self._screen_col.grid(row=cr, column=1, sticky="w", **pad)
        self._screen_frame = ttk.Frame(self._screen_col, style="Card.TFrame")
        self._screen_frame.pack(anchor="w")
        ttk.Button(
            self._screen_col, text="刷新", width=8, command=self._rebuild_screen_radios,
        ).pack(anchor="w", pady=(2, 0))
        self._screen_row = cr
        self._screen_grid = [
            (self._screen_label, {"row": cr, "column": 0, "sticky": "nw", **pad}),
            (self._screen_col, {"row": cr, "column": 1, "sticky": "nw", **pad}),
        ]
        cr += 1

        self._window_label = ttk.Label(cap_inner, text="截取窗口", style="Card.TLabel")
        self._window_label.grid(row=cr, column=0, sticky="nw", **pad)
        self.win_fr = ttk.Frame(cap_inner, style="Card.TFrame")
        self.win_fr.grid(row=cr, column=1, sticky="nsew", **pad)
        btn_row = ttk.Frame(self.win_fr, style="Card.TFrame")
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="刷新列表", width=10, command=self._refresh_window_list).pack(side="left")
        ttk.Button(
            btn_row, text="拾取当前窗口", width=12, command=self._pick_foreground_capture_window,
        ).pack(side="left", padx=4)
        list_wrap = ttk.Frame(self.win_fr, style="Card.TFrame")
        list_wrap.pack(fill="both", expand=True, pady=4)
        scroll = ttk.Scrollbar(list_wrap, orient="vertical")
        self.window_listbox = tk.Listbox(
            list_wrap,
            height=6,
            width=42,
            activestyle="dotbox",
            exportselection=False,
            yscrollcommand=scroll.set,
        )
        style_listbox(self.window_listbox)
        scroll.config(command=self.window_listbox.yview)
        self.window_listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.window_listbox.bind("<<ListboxSelect>>", self._on_window_list_select)
        self.window_count_var = tk.StringVar(value="共 0 个可截窗口")
        ttk.Label(self.win_fr, textvariable=self.window_count_var, style="CardMuted.TLabel").pack(anchor="w")
        self._window_row = cr
        self._window_grid = [
            (self._window_label, {"row": cr, "column": 0, "sticky": "nw", **pad}),
            (self.win_fr, {"row": cr, "column": 1, "sticky": "nsew", **pad}),
        ]
        self._list_refreshing = False
        cr += 1

        self.reg_fr = ttk.Frame(cap_inner, style="Card.TFrame")
        self.reg_fr.grid(row=cr, column=0, columnspan=2, sticky="ew", **pad)
        self.region_continuous_var = tk.BooleanVar(value=bool(self.cfg.get("region_continuous", True)))
        ttk.Checkbutton(
            self.reg_fr,
            text="持续使用同一区域（否则每次截图前都重新框选）",
            variable=self.region_continuous_var,
            command=self._save_now,
        ).pack(anchor="w")
        btn_line = ttk.Frame(self.reg_fr, style="Card.TFrame")
        btn_line.pack(anchor="w", pady=2)
        ttk.Button(btn_line, text="选取区域", command=self._pick_region_clicked).pack(side="left", padx=2)
        ttk.Button(btn_line, text="清除区域", command=self._clear_region_clicked).pack(side="left", padx=2)
        self.region_info_var = tk.StringVar(value=self._region_info_text())
        ttk.Label(self.reg_fr, textvariable=self.region_info_var, style="CardMuted.TLabel", wraplength=380).pack(anchor="w")
        self._region_row = cr
        self._region_grid = [
            (self.reg_fr, {"row": cr, "column": 0, "columnspan": 2, "sticky": "ew", **pad}),
        ]
        cr += 1

        card_paste = tk.Frame(frame, bg=Theme.CARD, highlightbackground=Theme.SEPARATOR, highlightthickness=1, bd=0)
        card_paste.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        row += 1
        paste = ttk.Frame(card_paste, padding=14, style="Card.TFrame")
        paste.pack(fill="both", expand=True)

        self.auto_send_var = tk.BooleanVar(value=self.cfg["auto_send"])
        pr = 0
        ttk.Label(paste, text="发送", style="Card.TLabel", font=(Theme.FONT_UI[0], 11, "bold")).grid(
            row=pr, column=0, sticky="w", **pad
        )
        self.compact_var = tk.BooleanVar(value=bool(self.cfg.get("compact_mode")))
        ttk.Checkbutton(
            paste,
            text="小浮窗模式",
            variable=self.compact_var,
            command=self._toggle_compact,
        ).grid(row=pr, column=1, sticky="w", **pad)
        pr += 1

        ttk.Checkbutton(
            paste, text="截图后自动发送（粘贴后回车/点击）",
            variable=self.auto_send_var,
            command=self._save_now,
        ).grid(row=pr, column=0, columnspan=2, sticky="w", **pad)
        pr += 1

        self.save_var = tk.BooleanVar(value=self.cfg["save_backup"])
        ttk.Checkbutton(
            paste, text="保存本地备份",
            variable=self.save_var,
            command=self._save_now,
        ).grid(row=pr, column=0, columnspan=2, sticky="w", **pad)
        pr += 1

        self.compress_var = tk.BooleanVar(value=self.cfg["compress"])
        ttk.Checkbutton(
            paste, text="压缩图片",
            variable=self.compress_var,
            command=self._save_now,
        ).grid(row=pr, column=0, columnspan=2, sticky="w", **pad)
        pr += 1

        ttk.Label(paste, text="发送方式", style="Card.TLabel").grid(row=pr, column=0, sticky="w", **pad)
        self.send_mode_var = tk.StringVar(value=self.cfg["send_mode"])
        mode_frame = ttk.Frame(paste, style="Card.TFrame")
        mode_frame.grid(row=pr, column=1, sticky="w", **pad)
        ttk.Radiobutton(mode_frame, text="回车", variable=self.send_mode_var, value="enter", command=self._save_now).pack(
            side="left"
        )
        ttk.Radiobutton(mode_frame, text="点击坐标", variable=self.send_mode_var, value="click", command=self._save_now).pack(
            side="left"
        )
        pr += 1

        coord_frame = ttk.Frame(paste, style="Card.TFrame")
        coord_frame.grid(row=pr, column=0, columnspan=2, sticky="w", **pad)
        ttk.Label(coord_frame, text="发送按钮坐标 X:", style="Card.TLabel").pack(side="left")
        self.x_var = tk.IntVar(value=self.cfg["click_x"])
        ttk.Entry(coord_frame, textvariable=self.x_var, width=6).pack(side="left")
        ttk.Label(coord_frame, text=" Y:", style="Card.TLabel").pack(side="left")
        self.y_var = tk.IntVar(value=self.cfg["click_y"])
        ttk.Entry(coord_frame, textvariable=self.y_var, width=6).pack(side="left")
        ttk.Button(coord_frame, text="保存", command=self._save_now, width=5).pack(side="left", padx=4)
        pr += 1

        ttk.Label(paste, text="切窗延迟(秒)", style="Card.TLabel").grid(row=pr, column=0, sticky="w", **pad)
        self.switch_delay_var = tk.DoubleVar(value=self.cfg["switch_delay"])
        ttk.Spinbox(
            paste, from_=0.0, to=10.0, increment=0.5, width=6,
            textvariable=self.switch_delay_var, command=self._save_now,
        ).grid(row=pr, column=1, sticky="w", **pad)
        pr += 1

        ttk.Label(paste, text="上传等待(秒)", style="Card.TLabel").grid(row=pr, column=0, sticky="w", **pad)
        self.upload_delay_var = tk.DoubleVar(value=self.cfg["upload_delay"])
        ttk.Spinbox(
            paste, from_=0.0, to=15.0, increment=0.5, width=6,
            textvariable=self.upload_delay_var, command=self._save_now,
        ).grid(row=pr, column=1, sticky="w", **pad)
        pr += 1

        ttk.Label(paste, text="浮窗透明度", style="Card.TLabel").grid(row=pr, column=0, sticky="w", **pad)
        self.opacity_var = tk.DoubleVar(value=self.cfg["opacity"])
        ttk.Scale(
            paste, from_=0.3, to=1.0, orient="horizontal",
            variable=self.opacity_var, command=self._on_opacity_change,
        ).grid(row=pr, column=1, sticky="ew", **pad)

        self.run_btn = tk.Button(
            frame,
            text="截图并粘贴  ·  F8",
            command=self.trigger_async,
            width=30,
            height=2,
        )
        style_primary_button(self.run_btn)
        self.run_btn.grid(row=row, column=0, columnspan=2, padx=pad["padx"], pady=(12, 7))
        row += 1

        self.status_label = ttk.Label(frame, textvariable=self.status_var, style="Status.TLabel", wraplength=430, anchor="center")
        self.status_label.grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        row += 1

        ttk.Label(frame, text=REPO_URL, style="Muted.TLabel", cursor="hand2").grid(
            row=row, column=0, columnspan=2, sticky="ew", **pad
        )

        self._last_capture_source = self.cfg.get("capture_source", "screen")
        self._rebuild_screen_radios()
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
        prev = getattr(self, "_last_capture_source", None)
        src = self.capture_source_var.get()
        self._update_source_rows_visibility()
        if src == "window" and prev != "window":
            self._refresh_window_list(
                select_hwnd=int(self.cfg.get("capture_window_hwnd", 0) or 0),
            )
        self._last_capture_source = src
        self._save_now()

    def _set_grid_section(self, grid_spec: list, visible: bool) -> None:
        """显式 grid / grid_remove。不能用 grid_slaves：grid_remove 后 slaves 为空，无法再显示。"""
        for widget, opts in grid_spec:
            if visible:
                widget.grid(**opts)
            else:
                widget.grid_remove()

    def _update_source_rows_visibility(self):
        src = self.capture_source_var.get()
        self._set_grid_section(self._screen_grid, src == "screen")
        self._set_grid_section(self._window_grid, src == "window")
        self._set_grid_section(self._region_grid, src == "region")
        if src == "window":
            getattr(self, "_cap_inner", self.full_frame).update_idletasks()

    def _on_window_list_select(self, _event=None):
        if self._list_refreshing:
            return
        if not self.window_listbox.curselection():
            return
        self._save_now()

    def _refresh_window_list(self, select_hwnd: int = 0):
        pairs = enum_top_level_windows()
        self._window_hwnds = [p[0] for p in pairs]
        self._list_refreshing = True
        try:
            self.window_listbox.delete(0, tk.END)
            for hwnd, title in pairs:
                short = title if len(title) <= 52 else title[:49] + "..."
                self.window_listbox.insert(tk.END, f"{short}   (hwnd:{hwnd})")
            n = len(pairs)
            self.window_count_var.set(
                f"共 {n} 个可截窗口" if n else "未检测到窗口，请点「刷新列表」或「拾取当前窗口」"
            )
            pick_idx = -1
            if select_hwnd and select_hwnd in self._window_hwnds:
                pick_idx = self._window_hwnds.index(select_hwnd)
            elif n > 0:
                pick_idx = 0
            if pick_idx >= 0:
                self.window_listbox.selection_clear(0, tk.END)
                self.window_listbox.selection_set(pick_idx)
                self.window_listbox.see(pick_idx)
                self.window_listbox.activate(pick_idx)
        finally:
            self._list_refreshing = False
        self._save_now()

    def _pick_foreground_capture_window(self):
        """把当前前台窗口加入列表并选中（先切到要截的应用再点）"""
        hwnd, title = get_foreground_window_info()
        if not hwnd:
            self._set_status("无法获取当前前台窗口", "red")
            return
        if self._is_self_window(title or ""):
            self._set_status("请先切换到要截图的应用窗口，再点「拾取当前窗口」", "orange")
            return
        self._refresh_window_list(select_hwnd=int(hwnd))
        self._set_status(f"已选中: {(title or '')[:40]}", "green")

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

    def _get_window_xy(self) -> tuple:
        self.root.update_idletasks()
        return int(self.root.winfo_x()), int(self.root.winfo_y())

    def _place_window_at(self, x: int, y: int) -> None:
        self.root.geometry(f"+{x}+{y}")

    def _load_window_geometry(self) -> None:
        x, y = int(self.cfg.get("window_x", -1)), int(self.cfg.get("window_y", -1))
        if x >= 0 and y >= 0:
            self._place_window_at(x, y)
        else:
            self._place_window_at(50, 50)

    def _save_window_geometry(self) -> None:
        x, y = self._get_window_xy()
        self.cfg["window_x"] = x
        self.cfg["window_y"] = y
        save_config(self.cfg)

    def _rebuild_screen_radios(self) -> None:
        """按本机实际显示器数量重建「截取屏幕」选项（含分辨率）"""
        monitors = get_display_monitors(refresh=True)
        for w in self._screen_frame.winfo_children():
            w.destroy()
        if not monitors:
            ttk.Label(self._screen_frame, text="未检测到显示器", foreground="red").pack(anchor="w")
            return
        cur = int(self.screen_var.get())
        if cur < 0 or cur > len(monitors):
            cur = 0
            self.screen_var.set(0)
        try:
            all_screen = virtual_screen_dict()
            ttk.Radiobutton(
                self._screen_frame,
                text=f"全部屏幕  {all_screen['width']}×{all_screen['height']}",
                variable=self.screen_var,
                value=0,
                command=self._save_now,
            ).pack(anchor="w")
        except Exception:
            pass
        for m in monitors:
            ttk.Radiobutton(
                self._screen_frame,
                text=m["label"],
                variable=self.screen_var,
                value=m["index"],
                command=self._save_now,
            ).pack(anchor="w")
        self._save_now()

    def _toggle_compact(self):
        x, y = self._get_window_xy()
        on = bool(self.compact_var.get())
        self.cfg["compact_mode"] = on
        if on:
            self.full_frame.pack_forget()
            self.mini_frame.pack(fill="both", expand=True)
        else:
            self.mini_frame.pack_forget()
            self.full_frame.pack(fill="both", expand=True)
        self.root.update_idletasks()
        self._place_window_at(x, y)
        self._save_window_geometry()

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
                    print(f"[目标窗口] {short}")
        except Exception as e:
            print(f"[窗口跟踪] {e}")
        self.root.after(300, self._schedule_track_window)

    def _is_self_window(self, title: str) -> bool:
        if not title:
            return True
        for key in (APP_TITLE, APP_TITLE_EN, "网测截图助手", "秒截图", "分屏截屏"):
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
        sel = self.window_listbox.curselection()
        if sel and len(self._window_hwnds) > 0:
            idx = int(sel[0])
            if 0 <= idx < len(self._window_hwnds):
                cfg["capture_window_hwnd"] = int(self._window_hwnds[idx])
            else:
                cfg["capture_window_hwnd"] = 0
        elif self._window_hwnds:
            cfg["capture_window_hwnd"] = int(self._window_hwnds[0])
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
                report(f"等待切回目标应用 {sw}s …")
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
        if keyboard is None:
            print("[快捷键] 未安装 keyboard 库，仅可用按钮触发")
            return
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
            app._save_window_geometry()
        except Exception:
            pass
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
