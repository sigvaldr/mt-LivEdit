"""
The three edit operations: Move, Rotate, Scale.

These mutate layer dicts in place. All functions take an iterable of
the actual layer dicts to modify (already filtered down to the user's
selection by the caller).
"""
from __future__ import annotations

from typing import Any, Iterable, Literal

Direction4 = Literal["up", "right", "down", "left"]
RotateDirection = Literal["clockwise", "counterclockwise"]
ScaleDirection = Literal["larger", "smaller"]


def move(layers: Iterable[dict[str, Any]], direction: Direction4, amount: float) -> None:
    """
    Shift each layer's position by `amount` in the given screen direction.

    Coordinate convention (confirmed by trial and error against the game):
    increasing y moves a decal UP, so "down" subtracts from y.
    Increasing x moves a decal RIGHT.
    """
    if amount < 0:
        raise ValueError("Move amount must be zero or positive; pick a direction instead of a sign.")

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
    """
    Rotate each layer in-plane by `degrees`.

    Assumption: the decal's own in-plane spin is the `roll` component of
    its rotation (pitch/yaw orient the decal's projector onto the body
    panel; roll spins the decal image itself). Clockwise adds to roll,
    counterclockwise subtracts. If this comes out backwards in-game,
    just use the opposite direction option - the amount will still be
    correct, only the sign differs.
    """
    if degrees < 0:
        raise ValueError("Degrees must be zero or positive; pick a direction instead of a sign.")

    delta = degrees if direction == "clockwise" else -degrees

    for layer in layers:
        rot = layer["rotation"]
        rot["roll"] = rot["roll"] + delta


def scale(layers: Iterable[dict[str, Any]], direction: ScaleDirection, percent: float) -> None:
    """
    Proportionally scale each layer's `decalScale` by `percent`.

    "25% bigger" -> decalScale *= 1.25
    "25% smaller" -> decalScale *= 0.75
    Only decalScale is touched (not `stretch`), matching how scaling was
    done previously - `stretch` is a separate width multiplier some
    decals use and is left alone so aspect-ratio tweaks aren't erased.
    """
    if percent < 0:
        raise ValueError("Percent must be zero or positive; pick a direction instead of a sign.")

    factor = (1 + percent / 100.0) if direction == "larger" else (1 - percent / 100.0)
    if factor < 0:
        raise ValueError("That percentage would shrink decals to a negative size.")

    for layer in layers:
        layer["decalScale"] = layer["decalScale"] * factor
