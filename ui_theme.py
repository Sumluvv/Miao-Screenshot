# -*- coding: utf-8 -*-
"""分屏截屏助手 — Apple-inspired light UI theme（ttk + Tk）"""

import sys
import tkinter as tk
from tkinter import ttk


class Theme:
    """配色与字体"""
    BG = "#f5f5f7"
    CARD = "#ffffff"
    CARD_SOFT = "#fbfbfd"
    PRIMARY = "#0071e3"
    PRIMARY_HOVER = "#0077ed"
    PRIMARY_FG = "#ffffff"
    TEXT = "#1d1d1f"
    TEXT_MUTED = "#6e6e73"
    ACCENT = "#34c759"
    BORDER = "#d2d2d7"
    SUCCESS = "#248a3d"
    WARN = "#bf5b00"
    DANGER = "#d70015"
    SEPARATOR = "#e5e5ea"

    FONT_UI = ("Segoe UI Variable", 9) if sys.platform == "win32" else ("SF Pro Text", 11)
    FONT_TITLE = ("Segoe UI Variable Display", 17, "bold") if sys.platform == "win32" else ("SF Pro Display", 19, "bold")
    FONT_SUB = ("Segoe UI Variable", 9) if sys.platform == "win32" else ("SF Pro Text", 10)
    FONT_BTN = ("Segoe UI Variable", 11, "bold") if sys.platform == "win32" else ("SF Pro Text", 12, "bold")


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
    style.configure("Title.TLabel", background=Theme.BG, foreground=Theme.TEXT, font=Theme.FONT_TITLE)
    style.configure("Sub.TLabel", background=Theme.BG, foreground=Theme.TEXT_MUTED, font=Theme.FONT_SUB)
    style.configure("Target.TLabel", background=Theme.BG, foreground=Theme.ACCENT, font=Theme.FONT_UI)
    style.configure("Status.TLabel", background=Theme.BG, foreground=Theme.TEXT_MUTED, font=Theme.FONT_UI)

    style.configure(
        "Card.TLabelframe",
        background=Theme.CARD,
        borderwidth=0,
        relief="flat",
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=Theme.CARD,
        foreground=Theme.TEXT,
        font=(Theme.FONT_UI[0], 10, "bold"),
    )
    style.configure("Card.TFrame", background=Theme.CARD)
    style.configure("Soft.TFrame", background=Theme.CARD_SOFT)
    style.configure("Card.TLabel", background=Theme.CARD, foreground=Theme.TEXT, font=Theme.FONT_UI)
    style.configure("CardMuted.TLabel", background=Theme.CARD, foreground=Theme.TEXT_MUTED, font=Theme.FONT_SUB)
    style.configure("CardAccent.TLabel", background=Theme.CARD, foreground=Theme.ACCENT, font=Theme.FONT_UI)

    style.configure("TCheckbutton", background=Theme.CARD, font=Theme.FONT_UI)
    style.configure("TRadiobutton", background=Theme.CARD, font=Theme.FONT_UI)
    style.configure("TButton", padding=(12, 6), font=Theme.FONT_UI)
    style.map("TButton", foreground=[("active", Theme.PRIMARY)])
    style.configure("TEntry", padding=(6, 4))
    style.configure("TSpinbox", padding=(6, 4))

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
        padx=14,
        pady=4,
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
        padx=10,
        pady=3,
    )


def style_secondary_button(btn: tk.Button) -> None:
    btn.configure(
        bg="#f2f2f7",
        fg=Theme.TEXT,
        activebackground="#e5e5ea",
        activeforeground=Theme.TEXT,
        relief="flat",
        cursor="hand2",
        bd=0,
        highlightthickness=1,
        highlightbackground=Theme.BORDER,
        font=Theme.FONT_UI,
        padx=8,
        pady=3,
    )


def style_listbox(lb: tk.Listbox) -> None:
    lb.configure(
        bg=Theme.CARD,
        fg=Theme.TEXT,
        selectbackground=Theme.PRIMARY,
        selectforeground=Theme.PRIMARY_FG,
        highlightthickness=1,
        highlightbackground=Theme.SEPARATOR,
        highlightcolor=Theme.PRIMARY,
        borderwidth=0,
        font=Theme.FONT_UI,
    )
