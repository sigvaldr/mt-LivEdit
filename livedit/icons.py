"""
Loads a small preview thumbnail for a decal, keyed by its `decalKey`.

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

Two backends:

- Without Pillow: uses Tkinter's built-in PhotoImage, which only reads
  PNG/GIF/PPM/PGM, and can only *downscale* cleanly (via `subsample`,
  which only shrinks by whole-number factors).
- With Pillow installed (`pip install Pillow`): reads virtually any
  image format and produces a clean, evenly-sized thumbnail regardless
  of the source image's dimensions. Recommended if your decal images
  are JPG/BMP/WEBP or aren't already roughly icon-sized.

Missing/unreadable images simply result in no icon for that row (the
row still shows its name), rather than an error.
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Optional

from .resources import resource_path

try:
    from PIL import Image, ImageTk

    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

_EXTENSIONS_PIL = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
_EXTENSIONS_TK = (".png", ".gif", ".ppm", ".pgm")


class IconCache:
    """Loads each decal's thumbnail once and keeps a live reference to
    it (Tkinter garbage-collects a PhotoImage the moment nothing in
    Python still refers to it, even if it's on screen)."""

    def __init__(self, size: int = 32) -> None:
        self.size = size
        self._icon_cache: dict[str, Optional[tk.PhotoImage]] = {}
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

    def get(self, decal_key: str):
        """Returns a tk-displayable image for this decal, or None."""
        if decal_key in self._icon_cache:
            return self._icon_cache[decal_key]

        if self._file_index is None:
            self._file_index = self._build_index()

        icon = None
        path = self._file_index.get(decal_key.lower())
        if path is not None:
            try:
                icon = self._load(path)
            except Exception:
                icon = None

        self._icon_cache[decal_key] = icon
        return icon

    def _load(self, path: Path):
        if _HAS_PIL:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((self.size, self.size))
            return ImageTk.PhotoImage(img)

        raw = tk.PhotoImage(file=str(path))
        longest_side = max(raw.width(), raw.height())
        factor = max(1, longest_side // self.size)
        return raw.subsample(factor, factor) if factor > 1 else raw

