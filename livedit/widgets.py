
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from . import theme

ROW_HEIGHT_PADDING = 6


class SelectableIconList(ttk.Frame):
    def __init__(self, parent: tk.Widget, rows: list[tuple[int, str, Optional[tk.PhotoImage]]]) -> None:
        super().__init__(parent)

        self._order: list[int] = [
            storage_index for storage_index, _, _ in rows]
        self._row_frames: dict[int, tk.Frame] = {}
        self._selected: set[int] = set()

        self._canvas = tk.Canvas(
            self, background=theme.PANEL, highlightthickness=0)
        vscroll = ttk.Scrollbar(self, orient="vertical",
                                command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vscroll.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        self._inner = tk.Frame(self._canvas, background=theme.PANEL)
        self._inner_id = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", lambda _e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._inner_id, width=e.width))

        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

        for storage_index, text, icon in rows:
            self._add_row(storage_index, text, icon)

    # -- scrolling -----------------------------------------------------
    def _bind_mousewheel(self, _event) -> None:
        # Windows / macOS
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all(
            "<Button-4>", self._on_mousewheel_linux)  # Linux scroll up
        # Linux scroll down
        self._canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

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
            icon_label = tk.Label(row, text="", width=5,
                                  background=theme.PANEL)
            icon_label.pack(side="left", padx=(8, 10), pady=ROW_HEIGHT_PADDING)

        text_label = tk.Label(
            row, text=text, background=theme.PANEL, foreground=theme.BLUE,
            anchor="w", font=("TkDefaultFont", 11),
        )
        text_label.pack(side="left", fill="x", expand=True,
                        pady=ROW_HEIGHT_PADDING)

        for widget in (row, icon_label, text_label):
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", lambda _e,
                        si=storage_index: self._toggle(si))

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


class ColorWheel(ttk.Frame):
    """HSV color wheel (hue = angle, saturation = distance) plus a brightness
    slider. Pure Tk, no Pillow needed. `on_change(r, g, b)` fires on user
    interaction only, never from set_rgb()."""

    def __init__(self, parent: tk.Widget, on_change, size: int = 220) -> None:
        super().__init__(parent)
        self._on_change = on_change
        self._size = size
        self._radius = size / 2
        self._h, self._s, self._v = 0.0, 0.0, 1.0
        self._quiet = False

        self._canvas = tk.Canvas(self, width=size, height=size,
                                 background=theme.BLACK, highlightthickness=0,
                                 cursor="crosshair")
        self._canvas.pack()
        self._wheel_img = self._build_wheel_image()
        self._canvas.create_image(0, 0, image=self._wheel_img, anchor="nw")
        self._marker = self._canvas.create_oval(0, 0, 0, 0, outline="#FFFFFF",
                                                width=2)
        self._canvas.bind("<Button-1>", self._on_pick)
        self._canvas.bind("<B1-Motion>", self._on_pick)

        ttk.Label(self, text="Brightness").pack(anchor="w", pady=(6, 0))
        # classic tk.Scale: ttk.Scale can fire its command with a stale value
        # when first mapped, which would reset brightness to 0.
        self._slider = tk.Scale(
            self, from_=0, to=100, orient="horizontal", showvalue=False,
            command=self._on_slider, background=theme.BLUE,
            troughcolor=theme.PANEL, activebackground="#66D2FF",
            highlightthickness=0, bd=0, sliderrelief="flat")
        self._quiet = True          # don't fire on_change while setting up
        self._slider.set(100)
        self._quiet = False
        self._slider.pack(fill="x")
        self._move_marker()

    def _build_wheel_image(self) -> tk.PhotoImage:
        import colorsys
        import math
        size, rad = self._size, self._radius
        img = tk.PhotoImage(width=size, height=size)
        for y in range(size):
            row = []
            for x in range(size):
                dx, dy = x + 0.5 - rad, y + 0.5 - rad
                dist = math.hypot(dx, dy)
                if dist > rad:
                    row.append(theme.BLACK)
                    continue
                hue = (math.atan2(-dy, dx) / (2 * math.pi)) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, dist / rad, 1.0)
                row.append(f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}")
            img.put("{" + " ".join(row) + "}", to=(0, y))
        return img

    def _move_marker(self) -> None:
        import math
        angle = self._h * 2 * math.pi
        dist = self._s * self._radius
        cx = self._radius + math.cos(angle) * dist
        cy = self._radius - math.sin(angle) * dist
        self._canvas.coords(self._marker, cx - 6, cy - 6, cx + 6, cy + 6)

    def _emit(self) -> None:
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(self._h, self._s, self._v)
        self._on_change(round(r * 255), round(g * 255), round(b * 255))

    def _on_pick(self, event) -> None:
        import math
        dx, dy = event.x - self._radius, event.y - self._radius
        self._s = min(1.0, math.hypot(dx, dy) / self._radius)
        self._h = (math.atan2(-dy, dx) / (2 * math.pi)) % 1.0
        if self._v == 0:
            # Picking a hue at zero brightness would always yield black.
            self._v = 1.0
            self._slider.set(100)
        self._move_marker()
        self._emit()

    def _on_slider(self, _value: str) -> None:
        # Tk delivers Scale commands late (on idle), sometimes with a stale
        # value, so ignore the argument and compare the slider's real position
        # with our state: programmatic set() calls then match and are ignored.
        current = int(self._slider.get())
        if current == round(self._v * 100):
            return
        self._v = current / 100.0
        self._emit()

    def set_rgb(self, r: int, g: int, b: int) -> None:
        """Move the marker/slider to a color without firing on_change."""
        import colorsys
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if v > 0 and s > 0:
            self._h = h          # hue is meaningless for grays/black; keep old
        if v > 0:
            self._s = s
        self._v = v
        self._quiet = True
        self._slider.set(round(v * 100))
        self._quiet = False
        self._move_marker()
