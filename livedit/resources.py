
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
