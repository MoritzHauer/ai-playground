"""Load machine and tool data from config/*.toml."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@dataclass(frozen=True)
class Machine:
    name: str
    controller: str
    travel_x: float
    travel_y: float
    gantry_clearance: float
    spindle_max_rpm: int
    max_feed: float
    rapid_feed: float
    max_spoilboard_cut: float
    safe_z: float


@dataclass(frozen=True)
class Stock:
    """Raw material block. Zero point convention: X0 Y0 front-left corner, Z0 top surface."""
    size_x: float
    size_y: float
    thickness: float
    material: str = "holz"  # key into the tool presets


@dataclass(frozen=True)
class Preset:
    rpm: int
    feed: float
    plunge: float
    stepdown: float


@dataclass(frozen=True)
class Tool:
    id: str
    type: str  # "flat" | "ball" | "vbit"
    diameter: float
    flutes: int
    flute_length: float
    presets: dict[str, Preset] = field(default_factory=dict)

    @property
    def radius(self) -> float:
        return self.diameter / 2

    def preset(self, material: str) -> Preset:
        try:
            return self.presets[material]
        except KeyError:
            raise KeyError(
                f"Fraeser {self.id} hat kein Preset fuer '{material}' "
                f"(vorhanden: {', '.join(self.presets) or '-'})"
            ) from None


def load_machine(path: Path = CONFIG_DIR / "machine.toml") -> Machine:
    return Machine(**tomllib.loads(path.read_text(encoding="utf-8")))


def load_tools(path: Path = CONFIG_DIR / "tools.toml") -> dict[str, Tool]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    tools = {}
    for tool_id, t in data.items():
        presets = {m: Preset(**p) for m, p in t.pop("presets", {}).items()}
        tools[tool_id] = Tool(id=tool_id, presets=presets, **t)
    return tools
