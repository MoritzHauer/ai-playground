"""Machining operations. Each operation turns geometry + tool into a Toolpath.

New operation types (Pocket, Drill, VCarve, Relief, ...) only need a
`generate(job) -> Toolpath` method; everything after that is shared.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from shapely.geometry import Polygon

from .toolpath import Move, Toolpath

if TYPE_CHECKING:
    from .job import Job

RETRACT = 1.0  # mm above stock top where rapids stop and feed moves begin


@dataclass
class Tabs:
    """Holding tabs: small bridges left at the bottom so the part does not break loose."""
    count: int = 4
    width: float = 6.0   # mm, width of the remaining material bridge
    height: float = 1.5  # mm, measured from the stock bottom


@dataclass
class Profile:
    """Cut along a contour, outside/inside/on the line, in several depth passes."""
    shape: Polygon
    tool: str
    depth: float                 # mm below stock top (positive)
    side: str = "outside"        # "outside" | "inside" | "on"
    direction: str = "climb"     # "climb" | "conventional"
    stepdown: float | None = None   # max. depth per pass, spread evenly
    feed: float | None = None
    plunge: float | None = None
    rpm: int | None = None
    tabs: Tabs | None = None
    ramp_length: float = 10.0    # mm along the path per depth step; 0 = straight plunge
    label: str = "Kontur"

    def generate(self, job: Job) -> Toolpath:
        tool = job.tool(self.tool)
        preset = tool.preset(job.stock.material)
        stepdown = self.stepdown or preset.stepdown
        feed = self.feed or preset.feed
        plunge = self.plunge or preset.plunge

        pts = _densify(self._ring(tool.radius), 0.5)
        seg = np.linalg.norm(np.diff(np.vstack([pts, pts[:1]]), axis=0), axis=1)
        s = np.concatenate([[0.0], np.cumsum(seg)[:-1]])  # arc length at each point
        length = float(seg.sum())
        ramp = min(self.ramp_length, length / 2)

        tab_top = -job.stock.thickness + self.tabs.height if self.tabs else None
        tab_half = (self.tabs.width + tool.diameter) / 2 if self.tabs else 0.0
        tab_centers = ((np.arange(self.tabs.count) + 0.5) * length / self.tabs.count
                       if self.tabs else np.array([]))

        def lift_for_tabs(z: np.ndarray, at: np.ndarray) -> np.ndarray:
            if tab_top is None:
                return z
            d = np.abs(at[:, None] - tab_centers[None, :])
            in_tab = (np.minimum(d, length - d) < tab_half).any(axis=1)
            return np.where(in_tab, np.maximum(z, tab_top), z)

        # stepdown is a maximum: spread the depth evenly, no thin last pass
        n_passes = int(np.ceil(self.depth / stepdown - 1e-9))
        levels = [self.depth * (i + 1) / n_passes for i in range(n_passes)]
        n = len(pts)
        idx = 0  # index of the point where the current pass starts
        moves = [Move(*pts[0], job.machine.safe_z), Move(*pts[0], RETRACT), Move(*pts[0], 0.0, plunge)]
        z_prev = 0.0
        for level in levels:
            z_pass = -float(level)
            order = (idx + np.arange(n)) % n
            s_loc = (s[order] - s[idx]) % length
            k = max(1, int(np.searchsorted(s_loc, ramp, side="right")))
            # one full lap, back to the start, then repeat the ramp section at full depth
            seq = np.concatenate([order, [idx], order[1:k]])
            s_seq = np.concatenate([s_loc, [length], length + s_loc[1:k]])
            if ramp > 0:
                z = np.where(s_seq < ramp, z_prev + (z_pass - z_prev) * s_seq / ramp, z_pass)
            else:
                z = np.full(len(seq), z_pass)
            z = lift_for_tabs(z, s[seq])
            for i, zz in zip(seq, z):
                last = moves[-1]
                x, y, zz = float(pts[i][0]), float(pts[i][1]), float(zz)
                if (x, y, zz) != (last.x, last.y, last.z):
                    moves.append(Move(x, y, zz, plunge if zz < last.z - 1e-6 else feed))
            idx, z_prev = int(order[k - 1]), z_pass
        moves.append(Move(moves[-1].x, moves[-1].y, job.machine.safe_z))
        return Toolpath(tool.id, self.rpm or preset.rpm, _simplify(moves), self.label)

    def _ring(self, r: float) -> np.ndarray:
        offset = {"outside": r, "inside": -r, "on": 0.0}[self.side]
        geom = self.shape.buffer(offset, quad_segs=16) if offset else self.shape
        if geom.is_empty or geom.geom_type != "Polygon":
            raise ValueError(f"{self.label}: Kontur ist fuer den Fraeser zu klein oder zerfaellt")
        ring = geom.exterior
        want_ccw = (self.side != "inside") == (self.direction == "climb")
        coords = np.array(ring.coords)[:-1]
        if ring.is_ccw != want_ccw:
            coords = coords[::-1]
        # start on the left-most point: away from the heart's notch and point
        return np.roll(coords, -int(np.argmin(coords[:, 0])), axis=0)


def _densify(pts: np.ndarray, max_step: float) -> np.ndarray:
    out = []
    for a, b in zip(pts, np.roll(pts, -1, axis=0)):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / max_step)))
        out.append(a + (b - a) * np.arange(n)[:, None] / n)
    return np.vstack(out)


def _simplify(moves: list[Move], tol: float = 1e-3) -> list[Move]:
    """Drop feed moves that lie on a straight line between their neighbours."""
    out = moves[:2]
    for m in moves[2:]:
        a, b = out[-2], out[-1]
        if not (a.rapid or b.rapid or m.rapid) and a.feed == b.feed == m.feed:
            p, q, r = (np.array([v.x, v.y, v.z]) for v in (a, b, m))
            if np.linalg.norm(np.cross(q - p, r - p)) <= tol * np.linalg.norm(r - p) and np.dot(q - p, r - q) >= 0:
                out[-1] = m
                continue
        out.append(m)
    return out
