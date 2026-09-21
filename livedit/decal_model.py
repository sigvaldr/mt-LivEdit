"""
Data model for a MotorTown livery export.

Key fact learned from working with real exports: the decal that appears
at the TOP of the in-game decal list is stored LAST in the JSON's
``decalLayers`` array (and the one at the bottom of the in-game list is
stored first). So whenever we show the list to the user we display it
in reverse order, while all edits are applied back to the original
(non-reversed) array so the exported JSON keeps the game's expected
layout.

Key fact learned about the coordinate system: increasing ``position.y``
moves a decal UP on the vehicle, not down. So "move down" means
subtracting from y, and "move up" means adding to y.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


class DecalParseError(Exception):
    """Raised when pasted text isn't a valid livery export."""


@dataclass
class LiveryDocument:
    """Wraps a parsed livery export and lets the UI work in display order."""

    raw: dict[str, Any]

    @property
    def layers(self) -> list[dict[str, Any]]:
        """The actual decalLayers array, in JSON (storage) order."""
        return self.raw["decal"]["decalLayers"]

    @classmethod
    def from_text(cls, text: str) -> "LiveryDocument":
        text = text.strip()
        if not text:
            raise DecalParseError("Paste your decal export first.")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DecalParseError(f"That doesn't look like valid JSON ({exc}).") from exc

        if not isinstance(data, dict) or "decal" not in data or "decalLayers" not in data.get("decal", {}):
            raise DecalParseError(
                "That JSON doesn't look like a MotorTown decal export "
                "(expected a 'decal.decalLayers' list)."
            )
        if not isinstance(data["decal"]["decalLayers"], list):
            raise DecalParseError("'decal.decalLayers' should be a list of decals.")

        return cls(raw=data)

    def display_order_indices(self) -> list[int]:
        """
        Storage indices, ordered the way they appear in-game (top of the
        in-game list first). This is simply the reverse of storage order.
        """
        return list(reversed(range(len(self.layers))))

    def display_rows(self) -> list[tuple[int, str]]:
        """
        Returns (storage_index, label) pairs in display (in-game) order,
        ready to hand straight to a listbox.
        """
        rows = []
        n = len(self.layers)
        for display_pos, storage_index in enumerate(self.display_order_indices()):
            layer = self.layers[storage_index]
            key = layer.get("decalKey", "unknown-decal")
            rows.append((storage_index, f"{display_pos + 1}. {key}"))
        return rows

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.raw, indent=indent)
