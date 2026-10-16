"""Minimal G-code reader for checking and simulating any .nc file (ours or Estlcam's).

Understands G0/G1/G2/G3 (XY plane, I/J centres), G20/G21, G90/G91, F, S.
Everything it does not understand is reported, never silently ignored.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np

WORD = re.compile(r"([A-Z])\s*([-+]?\d*\.?\d+)")


@dataclass
class Segment:
    start: tuple[float, float, float]
    end: tuple[float, float, float]
    rapid: bool
    feed: float | None
    line: int


@dataclass
class Program:
    segments: list[Segment] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)   # things that make the file unsafe to judge
    notes: list[str] = field(default_factory=list)
    seen: set[str] = field(default_factory=set)         # modal codes seen, e.g. "G21"
    spindle: list[float] = field(default_factory=list)

    def points(self) -> np.ndarray:
        if not self.segments:
            return np.zeros((0, 3))
        return np.array([self.segments[0].start] + [s.end for s in self.segments])


def parse(text: str) -> Program:
    prog = Program()
    pos = [0.0, 0.0, 0.0]
    motion, feed, absolute, metric = None, None, True, None
    for no, raw in enumerate(text.splitlines(), 1):
        line = re.sub(r"\(.*?\)|;.*", "", raw).upper().strip()
        if not line or line == "%":
            continue
        words = WORD.findall(line)
        leftover = WORD.sub("", line).strip()
        if leftover:
            prog.problems.append(f"Zeile {no}: nicht verstanden: '{raw.strip()}'")
        target = list(pos)
        has_xyz, ij = False, {}
        for letter, val in words:
            v = float(val)
            if letter == "G":
                code = f"G{v:g}"
                prog.seen.add(code)
                if v in (0, 1, 2, 3):
                    motion = int(v)
                elif v == 20:
                    metric = False
                elif v == 21:
                    metric = True
                elif v == 90:
                    absolute = True
                elif v == 91:
                    absolute = False
                elif v in (17, 94, 54, 40, 49, 80, 4):
                    pass
                else:
                    prog.problems.append(f"Zeile {no}: {code} wird vom Pruefer nicht unterstuetzt")
            elif letter in "XYZ":
                i = "XYZ".index(letter)
                target[i] = v if absolute else pos[i] + v
                has_xyz = True
            elif letter in "IJ":
                ij[letter] = v
            elif letter == "F":
                feed = v
            elif letter == "S":
                prog.spindle.append(v)
            elif letter == "M":
                prog.seen.add(f"M{v:g}")
            elif letter in "NT":
                pass
            elif letter == "R":
                prog.problems.append(f"Zeile {no}: Boegen mit R werden nicht unterstuetzt")
            else:
                prog.notes.append(f"Zeile {no}: Wort {letter}{val} ignoriert")
        if not has_xyz:
            continue
        if metric is None:
            prog.problems.append(f"Zeile {no}: Bewegung bevor G21 (mm) gesetzt ist")
            metric = True
        if motion is None:
            prog.problems.append(f"Zeile {no}: Bewegung ohne G0/G1")
            continue
        if motion in (0, 1):
            prog.segments.append(Segment(tuple(pos), tuple(target), motion == 0, feed, no))
        else:
            for a, b in _arc(pos, target, ij.get("I", 0.0), ij.get("J", 0.0), motion == 2):
                prog.segments.append(Segment(a, b, False, feed, no))
        pos = target
    return prog


def _arc(start, end, i, j, clockwise, step=0.5):
    cx, cy = start[0] + i, start[1] + j
    r = np.hypot(start[0] - cx, start[1] - cy)
    a0 = np.arctan2(start[1] - cy, start[0] - cx)
    a1 = np.arctan2(end[1] - cy, end[0] - cx)
    sweep = a1 - a0
    if clockwise and sweep >= 0:
        sweep -= 2 * np.pi
    elif not clockwise and sweep <= 0:
        sweep += 2 * np.pi
    n = max(2, int(np.ceil(abs(sweep) * r / step)))
    t = np.linspace(0, 1, n + 1)
    pts = [(cx + r * np.cos(a0 + sweep * k), cy + r * np.sin(a0 + sweep * k),
            start[2] + (end[2] - start[2]) * k) for k in t]
    pts[-1] = tuple(end)
    return list(zip(pts[:-1], pts[1:]))
