"""
Loads a small preview thumbnail for a decal, keyed by its `decalKey`
and, when available, tinted to match that layer's `color` from the
JSON.

Decal images are organized under `assets/decals/` in category
subfolders (as they're organized when exported from the game), e.g.:

    assets/decals/Recycling/Recycle_1.png
    assets/decals/Ambulance_01/Ambulance_cross.png

A decal's `decalKey` in the JSON combines the two, e.g.
`"Recycling_Recycle_1"` or `"Ambulance_01_Ambulance_cross"`. So this
module recursively indexes every image under `assets/decals/` once,
keyed by both the bare filename (`recycle_1`) and
`<subfolder>_<filename>` (`recycling_recycle_1`), and matches whichever
one equals the decal's `decalKey` (case-insensitive).

Recoloring: the source images are typically white/greyscale masks that
the game itself tints using each layer's `color` field, so the same
tint is reproduced here by multiplying the image's R/G/B/A channels by
the layer's color (this is only done when Pillow is installed - see
below). Since the same base graphic can appear multiple times with
different colors, thumbnails are cached per `(decalKey, color)` pair,
not just per `decalKey`.

Two backends:

- Without Pillow: uses Tkinter's built-in PhotoImage, which only reads
  PNG/GIF/PPM/PGM, can only *downscale* cleanly (via `subsample`,
  which only shrinks by whole-number factors), and cannot recolor at
  all - thumbnails show the image's original, untinted colors.
- With Pillow installed (`pip install Pillow`): reads virtually any
  image format, produces a clean, evenly-sized thumbnail regardless of
  the source image's dimensions, and recolors to match each layer's
  `color`. Recommended.

Missing/unreadable images simply result in no icon for that row (the
row still shows its name), rather than an error.
"""
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
    """Loads each decal's thumbnail once and keeps a live reference to
    it (Tkinter garbage-collects a PhotoImage the moment nothing in
    Python still refers to it, even if it's on screen)."""

    def __init__(self, size: int = 32) -> None:
        self.size = size
        self._icon_cache: dict[tuple[str, Optional[ColorTuple]], Optional[tk.PhotoImage]] = {}
        self._file_index: Optional[dict[str, Path]] = None

    def _decals_folder(self) -> Path:
        return resource_path("decals")

    def _build_index(self) -> dict[str, Path]:
        """Walks assets/decals/ (including subfolders) once, mapping
        both `filename` and `subfolder_filename` (lowercased, no
        extension) to that file's path."""
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
        """Accepts the JSON `color` dict (keys r/g/b/a, any order,
        0-255) and returns a plain (r, g, b, a) tuple, or None if it's
        missing/malformed."""
        if not color:
            return None
        try:
            r = int(color.get("r", 255))
            g = int(color.get("g", 255))
            b = int(color.get("b", 255))
            a = int(color.get("a", 255))
        except (TypeError, AttributeError, ValueError):
            return None
        clamp = lambda v: max(0, min(255, v))
        return (clamp(r), clamp(g), clamp(b), clamp(a))

    def get(self, decal_key: str, color: Optional[dict] = None):
        """Returns a tk-displayable image for this decal (tinted to
        `color` when Pillow is available), or None."""
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
        """Multiplies img's R/G/B/A channels by `color`, matching how
        the game tints a white/greyscale decal mask with its layer
        color. Works on non-white source images too, just as a
        proportional tint rather than an exact recolor."""
        r, g, b, a = img.split()
        tint = Image.new("RGBA", img.size, color)
        tr, tg, tb, ta = tint.split()
        r = ImageChops.multiply(r, tr)
        g = ImageChops.multiply(g, tg)
        b = ImageChops.multiply(b, tb)
        a = ImageChops.multiply(a, ta)
        return Image.merge("RGBA", (r, g, b, a))


