"""Safety checks on parsed G-code against machine, stock and tool data.

Levels: FEHLER = do not run this file, WARNUNG = look at it, INFO = facts.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import Machine, Preset, Stock, Tool
from .gcode import Program


@dataclass
class Finding:
    level: str  # "FEHLER" | "WARNUNG" | "INFO"
    text: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.text}"


def estimate_minutes(prog: Program, machine: Machine) -> float:
    total = 0.0
    for s in prog.segments:
        d = float(np.linalg.norm(np.subtract(s.end, s.start)))
        total += d / (machine.rapid_feed if s.rapid else (s.feed or machine.max_feed))
    return total


def check(prog: Program, machine: Machine, stock: Stock, tool: Tool | None = None,
          preset: Preset | None = None) -> list[Finding]:
    f: list[Finding] = []
    err = lambda t: f.append(Finding("FEHLER", t))
    warn = lambda t: f.append(Finding("WARNUNG", t))
    info = lambda t: f.append(Finding("INFO", t))

    for p in prog.problems:
        err(p)
    if "G21" not in prog.seen:
        err("G21 (Millimeter) fehlt")
    if "G20" in prog.seen:
        err("G20 (Zoll) im Programm")
    if "G91" in prog.seen:
        err("G91 (relative Koordinaten) im Programm - Pruefer und Simulation nicht verlaesslich")
    if not prog.segments:
        err("Keine Bewegungen gefunden")
        return f

    r = tool.radius if tool else 0.0
    cut = [s for s in prog.segments if not s.rapid]
    pts = prog.points()
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    info(f"Verfahrbereich X {lo[0]:.1f}..{hi[0]:.1f}  Y {lo[1]:.1f}..{hi[1]:.1f}  Z {lo[2]:.2f}..{hi[2]:.2f} mm")

    # Machine limits
    if hi[0] - lo[0] + 2 * r > machine.travel_x or hi[1] - lo[1] + 2 * r > machine.travel_y:
        err("Job ist groesser als der Arbeitsraum der Maschine")
    if stock.thickness > machine.gantry_clearance - 40:
        warn(f"Werkstueck {stock.thickness} mm dick: Portalhoehe {machine.gantry_clearance} mm "
             "abzueglich Spindel/Fraeser pruefen")

    # Depth
    floor = -stock.thickness - machine.max_spoilboard_cut
    if lo[2] < floor - 1e-6:
        err(f"Fraest {-(lo[2] + stock.thickness):.2f} mm in die Opferplatte "
            f"(erlaubt {machine.max_spoilboard_cut} mm)")
    if tool and -lo[2] > tool.flute_length:
        err(f"Tiefe {-lo[2]:.1f} mm > Schneidenlaenge {tool.flute_length} mm von {tool.id}")
    if lo[2] > -stock.thickness + 1e-6:
        info(f"Nicht durchgefraest: tiefster Punkt {lo[2]:.2f} mm, Material {stock.thickness} mm")

    # Rapids must never touch material
    # (a straight vertical retract out of the cut is fine)
    for s in prog.segments:
        if not s.rapid:
            continue
        moves_xy = abs(s.start[0] - s.end[0]) + abs(s.start[1] - s.end[1]) > 1e-6
        if (moves_xy and min(s.start[2], s.end[2]) < 0.5) or (s.end[2] < s.start[2] and s.end[2] < 0.5):
            err(f"Zeile {s.line}: Eilgang (G0) im oder knapp ueber dem Material")
            break

    # Cutting outside the stock -> clamps, screws, tape
    in_material = [s for s in cut if min(s.start[2], s.end[2]) < 0]
    if in_material:
        xy = np.array([p for s in in_material for p in (s.start[:2], s.end[:2])])
        over = max(-xy[:, 0].min(), -xy[:, 1].min(),
                   xy[:, 0].max() - stock.size_x, xy[:, 1].max() - stock.size_y)
        if over > r + 1e-6:
            err(f"Fraeser verlaesst das Werkstueck um {over - r:.1f} mm (Nullpunkt/Groesse pruefen)")
        elif over > 1e-6:
            warn("Fraeserbahn reicht bis an die Werkstueckkante")

    # Feeds
    feeds = [s.feed for s in cut]
    if any(v is None for v in feeds):
        err("G1 ohne Vorschub (F)")
    feeds = [v for v in feeds if v]
    if feeds:
        info(f"Vorschuebe {min(feeds):.0f}..{max(feeds):.0f} mm/min")
        if max(feeds) > machine.max_feed:
            err(f"Vorschub {max(feeds):.0f} mm/min > Maschinengrenze {machine.max_feed:.0f}")
        elif preset and max(feeds) > preset.feed * 1.001:
            warn(f"Vorschub {max(feeds):.0f} mm/min ueber der Lab-Empfehlung {preset.feed:.0f}")
    if preset:
        plunges = [s.feed for s in cut if s.feed and s.end[2] < s.start[2] - 1e-6
                   and np.hypot(s.end[0] - s.start[0], s.end[1] - s.start[1]) < 1e-6
                   and s.end[2] < 0]
        if plunges and max(plunges) > preset.plunge * 1.001:
            warn(f"Eintauchen mit {max(plunges):.0f} mm/min (Empfehlung {preset.plunge:.0f})")
    if prog.spindle and max(prog.spindle) > machine.spindle_max_rpm:
        err(f"Drehzahl S{max(prog.spindle):.0f} > {machine.spindle_max_rpm}")

    # End
    if pts[-1][2] < machine.safe_z - 1e-6:
        warn(f"Programm endet nicht auf Sicherheitshoehe (Z={pts[-1][2]:.2f})")

    info(f"Geschaetzte Laufzeit {estimate_minutes(prog, machine):.1f} min (ohne Beschleunigung)")
    return f
