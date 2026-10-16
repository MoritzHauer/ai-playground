"""Part geometry as shapely polygons in machine coordinates (mm, Y points to the back).

Everything downstream (operations, SVG export) works on shapely geometry, so new
shapes - or shapes imported from SVG/DXF later - plug in without changes elsewhere.
"""
from __future__ import annotations

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry


def cubic_bezier(p0, p1, p2, p3, step: float = 0.25) -> np.ndarray:
    """Sample a cubic Bezier curve with roughly `step` mm between points."""
    pts = np.array([p0, p1, p2, p3], dtype=float)
    n = max(8, int(np.ceil(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)) / step)))
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3 * pts[0] + 3 * (1 - t) ** 2 * t * pts[1]
            + 3 * (1 - t) * t ** 2 * pts[2] + t ** 3 * pts[3])


def fit(geom: BaseGeometry, width: float | None = None, origin=(0.0, 0.0)) -> BaseGeometry:
    """Scale uniformly to `width` (mm) and move the bounding box corner to `origin`."""
    minx, miny, maxx, _ = geom.bounds
    if width is not None:
        f = width / (maxx - minx)
        geom = affinity.scale(geom, f, f, origin=(minx, miny))
        minx, miny, *_ = geom.bounds
    return affinity.translate(geom, origin[0] - minx, origin[1] - miny)


def heart(width: float = 75.0) -> Polygon:
    """Classic heart with a sharp notch on top and a point at the front (low Y)."""
    # Control points drawn in a 90 x 82 SVG box (Y down), see Herz.svg history.
    segments = [
        ((45, 20), (45, 8), (30, 1), (18, 4)),
        ((18, 4), (6, 7), (1, 20), (5, 32)),
        ((5, 32), (9, 45), (30, 60), (45, 77)),
        ((45, 77), (60, 60), (81, 45), (85, 32)),
        ((85, 32), (89, 20), (84, 7), (72, 4)),
        ((72, 4), (60, 1), (45, 8), (45, 20)),
    ]
    pts = np.vstack([cubic_bezier(*s)[:-1] for s in segments])
    pts[:, 1] *= -1  # SVG Y down -> machine Y up
    return fit(Polygon(pts), width=width)
