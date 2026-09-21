"""
Locates bundled asset files (e.g. decal preview images) whether the app
is running normally from source or frozen into a PyInstaller --onefile
executable.

When PyInstaller builds a --onefile exe, any files passed via
`--add-data` get unpacked at runtime into a temporary folder whose path
PyInstaller exposes as `sys._MEIPASS`. This helper checks for that and
falls back to the real project folder otherwise, so the rest of the
app can just call `resource_path("decals", "some_decal.png")` and not
care which mode it's running in.
"""
from __future__ import annotations

import sys
from pathlib import Path


def resource_path(*parts: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        # Running as a frozen PyInstaller --onefile exe.
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        # Running from source: project root is one level up from livedit/.
        base = Path(__file__).resolve().parent.parent

    return base.joinpath("assets", *parts)
