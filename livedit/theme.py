
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

BLUE = "#00B5FF"
BLACK = "#000000"
# slightly-off-black for fields/panels, to stay readable on pure black
PANEL = "#0a0a0a"
PANEL_HOVER = "#062633"  # dark blue-black for hover/active states


def apply_theme(root: tk.Tk) -> None:
    root.configure(background=BLACK)

    style = ttk.Style(root)
    # "clam" is the most reliably themeable built-in ttk theme across
    # both Windows and Linux; the default themes on some platforms
    # ignore background/foreground options entirely.
    style.theme_use("clam")

    style.configure(".", background=BLACK, foreground=BLUE,
                    fieldbackground=PANEL, bordercolor=BLUE,
                    lightcolor=BLACK, darkcolor=BLACK,
                    troughcolor=PANEL, focuscolor=BLUE)

    style.configure("TFrame", background=BLACK)
    style.configure("TLabel", background=BLACK, foreground=BLUE)
    style.configure("TSeparator", background=BLUE)

    style.configure("TButton", background=PANEL, foreground=BLUE,
                    bordercolor=BLUE, padding=6)
    style.map("TButton",
              background=[("active", PANEL_HOVER), ("disabled", BLACK)],
              foreground=[("disabled", "#0a4d66")])

    style.configure("TRadiobutton", background=BLACK, foreground=BLUE)
    style.map("TRadiobutton", background=[("active", BLACK)])

    style.configure("TEntry", fieldbackground=PANEL, foreground=BLUE,
                    insertcolor=BLUE, bordercolor=BLUE)

    style.configure("TScrollbar", background=PANEL, troughcolor=BLACK,
                    bordercolor=BLUE, arrowcolor=BLUE)


def style_listbox(listbox: tk.Listbox) -> None:
    """Classic tk.Listbox ignores ttk styles entirely, so color it by hand."""
    listbox.configure(
        background=PANEL,
        foreground=BLUE,
        selectbackground=BLUE,
        selectforeground=BLACK,
        highlightbackground=BLUE,
        highlightcolor=BLUE,
        highlightthickness=1,
    )
