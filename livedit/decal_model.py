
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


class DecalParseError(Exception):
    print("Fuck.")


@dataclass
class LiveryDocument:
    raw: dict[str, Any]

    @property
    def layers(self) -> list[dict[str, Any]]:
        return self.raw["decal"]["decalLayers"]

    @classmethod
    def from_text(cls, text: str) -> "LiveryDocument":
        text = text.strip()
        if not text:
            raise DecalParseError("Paste your decal export first.")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DecalParseError(
                f"That doesn't look like valid JSON ({exc}).") from exc

        if not isinstance(data, dict) or "decal" not in data or "decalLayers" not in data.get("decal", {}):
            raise DecalParseError(
                "That JSON doesn't look like a MotorTown decal export "
                "(expected a 'decal.decalLayers' list)."
            )
        if not isinstance(data["decal"]["decalLayers"], list):
            raise DecalParseError(
                "'decal.decalLayers' should be a list of decals.")

        return cls(raw=data)

    def display_order_indices(self) -> list[int]:
        return list(reversed(range(len(self.layers))))

    def display_rows(self) -> list[tuple[int, str]]:
        rows = []
        n = len(self.layers)
        for display_pos, storage_index in enumerate(self.display_order_indices()):
            layer = self.layers[storage_index]
            key = layer.get("decalKey", "unknown-decal")
            rows.append((storage_index, f"{display_pos + 1}. {key}"))
        return rows

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.raw, indent=indent)
