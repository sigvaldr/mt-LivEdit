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
