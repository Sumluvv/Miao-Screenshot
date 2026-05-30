# -*- coding: utf-8 -*-
"""分屏截屏助手 — 简洁现代 UI 主题（ttk + Tk）"""

import sys
import tkinter as tk
from tkinter import ttk


class Theme:
    """配色与字体"""
    BG = "#f4f6f9"
    CARD = "#ffffff"
    PRIMARY = "#2563eb"
    PRIMARY_HOVER = "#1d4ed8"
    PRIMARY_FG = "#ffffff"
    TEXT = "#1e293b"
    TEXT_MUTED = "#64748b"
    ACCENT = "#0ea5e9"
    BORDER = "#e2e8f0"
    SUCCESS = "#16a34a"
    WARN = "#d97706"
    DANGER = "#dc2626"

    FONT_UI = ("Microsoft YaHei UI", 9) if sys.platform == "win32" else ("PingFang SC", 11)
    FONT_TITLE = ("Microsoft YaHei UI", 15, "bold") if sys.platform == "win32" else ("PingFang SC", 16, "bold")
    FONT_SUB = ("Microsoft YaHei UI", 9) if sys.platform == "win32" else ("PingFang SC", 10)
    FONT_BTN = ("Microsoft YaHei UI", 11, "bold") if sys.platform == "win32" else ("PingFang SC", 12, "bold")


def apply_app_theme(root: tk.Tk) -> ttk.Style:
    root.configure(bg=Theme.BG)
    style = ttk.Style(root)
    try:
        if sys.platform == "win32":
            style.theme_use("vista")
        else:
            style.theme_use("clam")
    except tk.TclError:
        style.theme_use("clam")

    style.configure(".", background=Theme.BG, foreground=Theme.TEXT, font=Theme.FONT_UI)
    style.configure("TFrame", background=Theme.BG)
    style.configure("TLabel", background=Theme.BG, foreground=Theme.TEXT, font=Theme.FONT_UI)
    style.configure("Muted.TLabel", background=Theme.BG, foreground=Theme.TEXT_MUTED, font=Theme.FONT_SUB)
    style.configure("Title.TLabel", background=Theme.BG, foreground=Theme.PRIMARY, font=Theme.FONT_TITLE)
    style.configure("Sub.TLabel", background=Theme.BG, foreground=Theme.TEXT_MUTED, font=Theme.FONT_SUB)
    style.configure("Target.TLabel", background=Theme.BG, foreground=Theme.ACCENT, font=Theme.FONT_UI)
    style.configure("Status.TLabel", background=Theme.BG, foreground=Theme.TEXT_MUTED, font=Theme.FONT_UI)

    style.configure(
        "Card.TLabelframe",
        background=Theme.CARD,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=Theme.CARD,
        foreground=Theme.PRIMARY,
        font=(Theme.FONT_UI[0], 10, "bold"),
    )
    style.configure("Card.TFrame", background=Theme.CARD)

    style.configure("TCheckbutton", background=Theme.CARD, font=Theme.FONT_UI)
    style.configure("TRadiobutton", background=Theme.CARD, font=Theme.FONT_UI)
    style.configure("TButton", padding=(10, 4), font=Theme.FONT_UI)
    style.map("TButton", foreground=[("active", Theme.PRIMARY)])

    style.configure("TNotebook", background=Theme.BG)
    style.configure("Horizontal.TScale", background=Theme.CARD)

    return style


def style_primary_button(btn: tk.Button) -> None:
    btn.configure(
        bg=Theme.PRIMARY,
        fg=Theme.PRIMARY_FG,
        activebackground=Theme.PRIMARY_HOVER,
        activeforeground=Theme.PRIMARY_FG,
        relief="flat",
        cursor="hand2",
        bd=0,
        highlightthickness=0,
        font=Theme.FONT_BTN,
    )


def style_mini_button(btn: tk.Button) -> None:
    btn.configure(
        bg=Theme.PRIMARY,
        fg=Theme.PRIMARY_FG,
        activebackground=Theme.PRIMARY_HOVER,
        activeforeground=Theme.PRIMARY_FG,
        relief="flat",
        cursor="hand2",
        bd=0,
        highlightthickness=0,
        font=("Microsoft YaHei UI", 14, "bold") if sys.platform == "win32" else ("PingFang SC", 15, "bold"),
    )


def style_listbox(lb: tk.Listbox) -> None:
    lb.configure(
        bg=Theme.CARD,
        fg=Theme.TEXT,
        selectbackground=Theme.PRIMARY,
        selectforeground=Theme.PRIMARY_FG,
        highlightthickness=1,
        highlightbackground=Theme.BORDER,
        highlightcolor=Theme.PRIMARY,
        borderwidth=0,
        font=Theme.FONT_UI,
    )
