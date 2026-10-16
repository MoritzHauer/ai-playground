"""Material-removal simulation on a height map, plus a preview image.

Works on parsed G-code, so it shows what the machine will really do.
Supports flat and ball end mills; V-bits can be added as another kernel.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource
from matplotlib.patches import Rectangle

from .config import Stock, Tool
from .gcode import Program


def _kernel(tool: Tool, res: float) -> np.ndarray:
    """Height of the tool tip surface relative to its lowest point; inf outside the tool."""
    n = int(np.ceil(tool.radius / res))
    d = np.hypot(*np.meshgrid(np.arange(-n, n + 1) * res, np.arange(-n, n + 1) * res))
    if tool.type == "flat":
        k = np.zeros_like(d)
    elif tool.type == "ball":
        k = tool.radius - np.sqrt(np.clip(tool.radius ** 2 - d ** 2, 0, None))
    else:
        raise NotImplementedError(f"Simulation fuer Fraesertyp {tool.type} fehlt noch")
    k[d > tool.radius] = np.inf
    return k


def simulate(prog: Program, stock: Stock, tool: Tool, res: float = 0.2):
    """Return (heights, extent). heights[iy, ix]: surface Z, 0 = stock top."""
    margin = tool.diameter + 2
    x0, y0 = -margin, -margin
    nx = int(np.ceil((stock.size_x + 2 * margin) / res))
    ny = int(np.ceil((stock.size_y + 2 * margin) / res))
    xs = x0 + np.arange(nx) * res
    ys = y0 + np.arange(ny) * res
    inside = ((xs[None, :] >= 0) & (xs[None, :] <= stock.size_x)
              & (ys[:, None] >= 0) & (ys[:, None] <= stock.size_y))
    h = np.where(inside, 0.0, -stock.thickness)
    k = _kernel(tool, res)
    n = k.shape[0] // 2
    for s in prog.segments:
        if min(s.start[2], s.end[2]) >= 0:
            continue
        a, b = np.array(s.start), np.array(s.end)
        steps = max(1, int(np.ceil(np.linalg.norm((b - a)[:2]) / (res / 2))))
        for p in a + (b - a) * np.linspace(0, 1, steps + 1)[:, None]:
            ix, iy = int(round((p[0] - x0) / res)), int(round((p[1] - y0) / res))
            ya, yb, xa, xb = iy - n, iy + n + 1, ix - n, ix + n + 1
            if ya < 0 or xa < 0 or yb > ny or xb > nx:
                continue  # outside the simulated area, the checker reports this
            win = h[ya:yb, xa:xb]
            np.minimum(win, p[2] + k, out=win)
    return h, (x0, x0 + nx * res, y0, y0 + ny * res)


def render(prog: Program, stock: Stock, heights: np.ndarray, extent, path, title: str = "") -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), constrained_layout=True)

    # Left: toolpath top view
    for s in prog.segments:
        xs, ys = (s.start[0], s.end[0]), (s.start[1], s.end[1])
        if s.rapid:
            ax1.plot(xs, ys, color="0.6", lw=0.6, ls="--")
    cut = [s for s in prog.segments if not s.rapid]
    if cut:
        z = np.array([min(s.start[2], s.end[2]) for s in cut])
        segs = np.array([[s.start[:2], s.end[:2]] for s in cut])
        from matplotlib.collections import LineCollection
        lc = LineCollection(segs, array=z, cmap="viridis_r", lw=1.2)
        ax1.add_collection(lc)
        fig.colorbar(lc, ax=ax1, label="Z [mm]", shrink=0.8)
    ax1.add_patch(Rectangle((0, 0), stock.size_x, stock.size_y, fill=False, ec="k", lw=1))
    ax1.plot(0, 0, "r+", ms=14, mew=2)
    ax1.annotate("Nullpunkt X0 Y0", (0, 0), (4, -8), textcoords="offset points", color="r")
    ax1.set_title("Werkzeugbahn (Draufsicht)")

    # Right: simulated result
    ls = LightSource(azdeg=315, altdeg=45)
    shaded = ls.shade(heights, cmap=plt.cm.copper, vert_exag=3, blend_mode="soft",
                      vmin=-stock.thickness - 1, vmax=0)
    ax2.imshow(shaded, origin="lower", extent=extent)
    ax2.set_title("Simulation: Ergebnis")

    for ax in (ax1, ax2):
        ax.set_aspect("equal")
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_xlabel("X [mm]")
        ax.set_ylabel("Y [mm] (hinten)")
    fig.suptitle(title)
    fig.savefig(path, dpi=130)
    plt.close(fig)
