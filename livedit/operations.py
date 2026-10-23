from __future__ import annotations

from typing import Any, Iterable, Literal

Direction4 = Literal["up", "right", "down", "left"]
RotateDirection = Literal["clockwise", "counterclockwise"]
ScaleDirection = Literal["larger", "smaller"]


def move(layers: Iterable[dict[str, Any]], direction: Direction4, amount: float) -> None:
    if amount < 0:
        raise ValueError(
            "Move amount must be zero or positive; pick a direction instead of a sign.")

    dx, dy = {
        "up": (0.0, amount),
        "down": (0.0, -amount),
        "right": (amount, 0.0),
        "left": (-amount, 0.0),
    }[direction]

    for layer in layers:
        pos = layer["position"]
        pos["x"] = pos["x"] + dx
        pos["y"] = pos["y"] + dy


def rotate(layers: Iterable[dict[str, Any]], direction: RotateDirection, degrees: float) -> None:
    if degrees < 0:
        raise ValueError(
            "Degrees must be zero or positive; pick a direction instead of a sign.")

    delta = degrees if direction == "clockwise" else -degrees

    for layer in layers:
        rot = layer["rotation"]
        rot["roll"] = rot["roll"] + delta


def scale(layers: Iterable[dict[str, Any]], direction: ScaleDirection, percent: float) -> None:
    if percent < 0:
        raise ValueError(
            "Percent must be zero or positive; pick a direction instead of a sign.")

    factor = (1 + percent /
              100.0) if direction == "larger" else (1 - percent / 100.0)
    if factor < 0:
        raise ValueError(
            "That percentage would shrink decals to a negative size.")

    for layer in layers:
        layer["decalScale"] = layer["decalScale"] * factor


# ---------------------------------------------------------------------------
# color
# ---------------------------------------------------------------------------

def parse_hex_color(text: str) -> tuple[int, int, int, int | None]:
    """Parse '#RRGGBB' or '#RRGGBBAA' (leading '#' optional).

    Returns (r, g, b, a). `a` is None when the text had no alpha part, so
    callers can keep each decal's existing alpha.
    """
    cleaned = text.strip().lstrip("#")
    if len(cleaned) not in (6, 8):
        raise ValueError(
            "Enter a hex color like #RRGGBB or #RRGGBBAA (6 or 8 hex digits).")
    try:
        r, g, b = (int(cleaned[i:i + 2], 16) for i in (0, 2, 4))
        a = int(cleaned[6:8], 16) if len(cleaned) == 8 else None
    except ValueError:
        raise ValueError(
            "That isn't a valid hex color - use only 0-9 and A-F.") from None
    return r, g, b, a


def color_to_hex(color: dict[str, Any], include_alpha: bool | None = None) -> str:
    """Layer color dict -> '#RRGGBB' (or '#RRGGBBAA' when alpha isn't 255)."""
    r, g, b = (int(color.get(k, 255)) for k in ("r", "g", "b"))
    a = int(color.get("a", 255))
    if include_alpha is None:
        include_alpha = a != 255
    text = f"#{r:02X}{g:02X}{b:02X}"
    return text + f"{a:02X}" if include_alpha else text


def set_color(layers: Iterable[dict[str, Any]], hex_text: str) -> None:
    """Set r/g/b on every layer. Alpha changes only if the hex includes it."""
    r, g, b, a = parse_hex_color(hex_text)
    for layer in layers:
        color = layer.setdefault("color", {})
        color["r"], color["g"], color["b"] = r, g, b
        if a is not None:
            color["a"] = a
        else:
            color.setdefault("a", 255)
