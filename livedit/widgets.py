"""
A scrollable list of rows (icon + text), each independently toggleable
as "selected" - used instead of a plain tk.Listbox so that decal
thumbnails can be shown next to each name. Plain tk.Listbox can only
ever show text, never images, which is why this exists.

Usage:
    rows = [(storage_index, "1. some-decal", icon_or_None), ...]
    widget = SelectableIconList(parent, rows)
    widget.select_all()
    widget.get_selection()  # -> set of storage_index currently selected
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from . import theme

ROW_HEIGHT_PADDING = 6


class SelectableIconList(ttk.Frame):
    def __init__(self, parent: tk.Widget, rows: list[tuple[int, str, Optional[tk.PhotoImage]]]) -> None:
        super().__init__(parent)

        self._order: list[int] = [storage_index for storage_index, _, _ in rows]
        self._row_frames: dict[int, tk.Frame] = {}
        self._selected: set[int] = set()

        self._canvas = tk.Canvas(self, background=theme.PANEL, highlightthickness=0)
        vscroll = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vscroll.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        self._inner = tk.Frame(self._canvas, background=theme.PANEL)
        self._inner_id = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", lambda _e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(self._inner_id, width=e.width))

        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

        for storage_index, text, icon in rows:
            self._add_row(storage_index, text, icon)

    # -- scrolling -----------------------------------------------------
    def _bind_mousewheel(self, _event) -> None:
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)      # Windows / macOS
        self._canvas.bind_all("<Button-4>", self._on_mousewheel_linux)  # Linux scroll up
        self._canvas.bind_all("<Button-5>", self._on_mousewheel_linux)  # Linux scroll down

    def _unbind_mousewheel(self, _event) -> None:
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event) -> None:
        self._canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def _on_mousewheel_linux(self, event) -> None:
        self._canvas.yview_scroll(-1 if event.num == 4 else 1, "units")

    # -- building rows ---------------------------------------------------
    def _add_row(self, storage_index: int, text: str, icon: Optional[tk.PhotoImage]) -> None:
        row = tk.Frame(self._inner, background=theme.PANEL)
        row.pack(fill="x")

        if icon is not None:
            icon_label = tk.Label(row, image=icon, background=theme.PANEL)
            icon_label.image = icon  # keep a live reference or Tk will garbage-collect it
            icon_label.pack(side="left", padx=(8, 10), pady=ROW_HEIGHT_PADDING)
        else:
            # keep every row the same height/indent whether or not it has an icon
            icon_label = tk.Label(row, text="", width=5, background=theme.PANEL)
            icon_label.pack(side="left", padx=(8, 10), pady=ROW_HEIGHT_PADDING)

        text_label = tk.Label(
            row, text=text, background=theme.PANEL, foreground=theme.BLUE,
            anchor="w", font=("TkDefaultFont", 11),
        )
        text_label.pack(side="left", fill="x", expand=True, pady=ROW_HEIGHT_PADDING)

        for widget in (row, icon_label, text_label):
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", lambda _e, si=storage_index: self._toggle(si))

        self._row_frames[storage_index] = row

    # -- selection state ---------------------------------------------------
    def _toggle(self, storage_index: int) -> None:
        if storage_index in self._selected:
            self._selected.discard(storage_index)
        else:
            self._selected.add(storage_index)
        self._restyle_row(storage_index)

    def _restyle_row(self, storage_index: int) -> None:
        row = self._row_frames[storage_index]
        selected = storage_index in self._selected
        bg = theme.BLUE if selected else theme.PANEL
        fg = theme.BLACK if selected else theme.BLUE
        row.configure(background=bg)
        for child in row.winfo_children():
            child.configure(background=bg)
            if not child.cget("image"):
                child.configure(foreground=fg)

    def select_all(self) -> None:
        self._selected = set(self._order)
        for storage_index in self._order:
            self._restyle_row(storage_index)

    def select_none(self) -> None:
        self._selected = set()
        for storage_index in self._order:
            self._restyle_row(storage_index)

    def set_selection(self, indices: set[int]) -> None:
        self._selected = set(indices) & set(self._order)
        for storage_index in self._order:
            self._restyle_row(storage_index)

    def get_selection(self) -> set[int]:
        return set(self._selected)
