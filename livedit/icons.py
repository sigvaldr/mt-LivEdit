
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Optional

from .resources import resource_path

try:
    from PIL import Image, ImageChops, ImageTk

    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

_EXTENSIONS_PIL = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
_EXTENSIONS_TK = (".png", ".gif", ".ppm", ".pgm")

ColorTuple = tuple[int, int, int, int]


class IconCache:

    def __init__(self, size: int = 32) -> None:
        self.size = size
        self._icon_cache: dict[tuple[str, Optional[ColorTuple]],
                               Optional[tk.PhotoImage]] = {}
        self._file_index: Optional[dict[str, Path]] = None

    def _decals_folder(self) -> Path:
        return resource_path("decals")

    def _build_index(self) -> dict[str, Path]:
        index: dict[str, Path] = {}
        folder = self._decals_folder()
        if not folder.is_dir():
            return index

        extensions = _EXTENSIONS_PIL if _HAS_PIL else _EXTENSIONS_TK
        for path in folder.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in extensions:
                continue
            stem_lower = path.stem.lower()
            index.setdefault(stem_lower, path)
            index.setdefault(f"{path.parent.name}_{path.stem}".lower(), path)
        return index

    @staticmethod
    def _normalize_color(color) -> Optional[ColorTuple]:
        if not color:
            return None
        try:
            r = int(color.get("r", 255))
            g = int(color.get("g", 255))
            b = int(color.get("b", 255))
            a = int(color.get("a", 255))
        except (TypeError, AttributeError, ValueError):
            return None

        def clamp(v): return max(0, min(255, v))
        return (clamp(r), clamp(g), clamp(b), clamp(a))

    def get(self, decal_key: str, color: Optional[dict] = None):
        color_tuple = self._normalize_color(color)
        cache_key = (decal_key, color_tuple)
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        if self._file_index is None:
            self._file_index = self._build_index()

        icon = None
        path = self._file_index.get(decal_key.lower())
        if path is not None:
            try:
                icon = self._load(path, color_tuple)
            except Exception:
                icon = None

        self._icon_cache[cache_key] = icon
        return icon

    def _load(self, path: Path, color: Optional[ColorTuple]):
        if _HAS_PIL:
            img = Image.open(path).convert("RGBA")
            if color is not None:
                img = self._tint(img, color)
            img.thumbnail((self.size, self.size))
            return ImageTk.PhotoImage(img)

        # No Pillow: no recoloring possible, just show the raw image.
        raw = tk.PhotoImage(file=str(path))
        longest_side = max(raw.width(), raw.height())
        factor = max(1, longest_side // self.size)
        return raw.subsample(factor, factor) if factor > 1 else raw

    @staticmethod
    def _tint(img: "Image.Image", color: ColorTuple) -> "Image.Image":
        r, g, b, a = img.split()
        tint = Image.new("RGBA", img.size, color)
        tr, tg, tb, ta = tint.split()
        r = ImageChops.multiply(r, tr)
        g = ImageChops.multiply(g, tg)
        b = ImageChops.multiply(b, tb)
        a = ImageChops.multiply(a, ta)
        return Image.merge("RGBA", (r, g, b, a))
