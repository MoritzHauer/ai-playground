"""Toolpath intermediate representation: a flat list of moves.

Every operation produces moves, the post-processor turns them into G-code.
Checks and simulation deliberately do NOT use this - they re-parse the G-code,
so they verify what the machine will actually receive.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    x: float
    y: float
    z: float
    feed: float | None = None  # None = rapid (G0)

    @property
    def rapid(self) -> bool:
        return self.feed is None


@dataclass
class Toolpath:
    tool_id: str
    rpm: int
    moves: list[Move]
    label: str = ""
