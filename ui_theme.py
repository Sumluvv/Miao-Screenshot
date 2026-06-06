# -*- coding: utf-8 -*-
"""分屏截屏助手 — compact professional UI theme（ttk + Tk）"""

import sys
import tkinter as tk
from tkinter import ttk


class Theme:
    """配色与字体"""
    BG = "#f4f2ee"
    CARD = "#fffdf8"
    CARD_SOFT = "#f0eee8"
    PRIMARY = "#0f766e"
    PRIMARY_HOVER = "#115e59"
    PRIMARY_FG = "#ffffff"
    BUTTON_BG = "#ffffff"
    BUTTON_BG_HOVER = "#e7f3f1"
    BUTTON_FG = "#173f3b"
    BUTTON_BORDER = "#8bb8b1"
    TOOLTIP_BG = "#101918"
    TOOLTIP_TEXT = "#f7faf8"
    TEXT = "#24231f"
    TEXT_MUTED = "#756f63"
    ACCENT = "#0f766e"
    BORDER = "#d8d2c6"
    SUCCESS = "#0f766e"
    WARN = "#a15c08"
    DANGER = "#b42318"
    SEPARATOR = "#e5dfd3"

    FONT_UI = ("Segoe UI", 9) if sys.platform == "win32" else ("SF Pro Text", 11)
    FONT_TITLE = ("Segoe UI Semibold", 13, "bold") if sys.platform == "win32" else ("SF Pro Display", 15, "bold")
    FONT_SUB = ("Segoe UI", 8) if sys.platform == "win32" else ("SF Pro Text", 10)
    FONT_BTN = ("Segoe UI Semibold", 10, "bold") if sys.platform == "win32" else ("SF Pro Text", 11, "bold")
    FONT_MONO = ("Consolas", 8) if sys.platform == "win32" else ("SF Mono", 9)


def apply_app_theme(root: tk.Tk) -> ttk.Style:
    root.configure(bg=Theme.BG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=Theme.BG, foreground=Theme.TEXT, font=Theme.FONT_UI)
    style.configure("TFrame", background=Theme.BG)
    style.configure("TLabel", background=Theme.BG, foreground=Theme.TEXT, font=Theme.FONT_UI)
    style.configure("Muted.TLabel", background=Theme.BG, foreground=Theme.TEXT_MUTED, font=Theme.FONT_SUB)
    style.configure("Title.TLabel", background=Theme.BG, foreground=Theme.TEXT, font=Theme.FONT_TITLE)
    style.configure("Sub.TLabel", background=Theme.BG, foreground=Theme.TEXT_MUTED, font=Theme.FONT_SUB)
    style.configure("Target.TLabel", background=Theme.BG, foreground=Theme.ACCENT, font=Theme.FONT_UI)
    style.configure("Status.TLabel", background=Theme.BG, foreground=Theme.TEXT_MUTED, font=Theme.FONT_UI)
    style.configure("Card.TFrame", background=Theme.CARD)
    style.configure("Soft.TFrame", background=Theme.CARD_SOFT)
    style.configure("Card.TLabel", background=Theme.CARD, foreground=Theme.TEXT, font=Theme.FONT_UI)
    style.configure("CardMuted.TLabel", background=Theme.CARD, foreground=Theme.TEXT_MUTED, font=Theme.FONT_SUB)
    style.configure("CardAccent.TLabel", background=Theme.CARD, foreground=Theme.ACCENT, font=Theme.FONT_UI)
    style.configure("SectionTitle.TLabel", background=Theme.CARD, foreground=Theme.TEXT_MUTED, font=Theme.FONT_MONO)

    style.configure("TCheckbutton", background=Theme.CARD, font=Theme.FONT_UI)
    style.configure("TRadiobutton", background=Theme.CARD, font=Theme.FONT_UI)
    style.map(
        "TCheckbutton",
        background=[("active", Theme.CARD)],
        foreground=[("active", Theme.TEXT)],
    )
    style.map(
        "TRadiobutton",
        background=[("active", Theme.CARD)],
        foreground=[("active", Theme.TEXT)],
    )
    style.configure(
        "TButton",
        padding=(8, 4),
        font=Theme.FONT_UI,
        background=Theme.CARD_SOFT,
        foreground=Theme.TEXT,
        bordercolor=Theme.BORDER,
        lightcolor=Theme.CARD_SOFT,
        darkcolor=Theme.CARD_SOFT,
        relief="flat",
    )
    style.map(
        "TButton",
        background=[("active", Theme.SEPARATOR)],
        foreground=[("active", Theme.TEXT)],
    )
    style.configure(
        "TEntry",
        padding=(5, 3),
        fieldbackground=Theme.CARD_SOFT,
        foreground=Theme.TEXT,
        insertcolor=Theme.TEXT,
        bordercolor=Theme.BORDER,
    )
    style.configure(
        "TSpinbox",
        padding=(5, 3),
        fieldbackground=Theme.CARD_SOFT,
        foreground=Theme.TEXT,
        arrowcolor=Theme.TEXT_MUTED,
        bordercolor=Theme.BORDER,
    )

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
        padx=12,
        pady=3,
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
        font=("Segoe UI Semibold", 12, "bold") if sys.platform == "win32" else ("SF Pro Text", 13, "bold"),
        padx=8,
        pady=2,
    )


def style_secondary_button(btn: tk.Button) -> None:
    btn.configure(
        bg=Theme.BUTTON_BG,
        fg=Theme.BUTTON_FG,
        activebackground=Theme.BUTTON_BG_HOVER,
        activeforeground=Theme.BUTTON_FG,
        relief="flat",
        cursor="hand2",
        bd=0,
        highlightthickness=1,
        highlightbackground=Theme.BUTTON_BORDER,
        font=Theme.FONT_BTN,
        padx=7,
        pady=2,
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
