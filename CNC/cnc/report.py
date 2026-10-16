"""Human-facing outputs: SVG of the parts and the setup sheet (SETUP.md, German)."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from shapely.geometry.base import BaseGeometry

from .config import Stock

if TYPE_CHECKING:
    from .job import Job, Output


def write_svg(parts: list[BaseGeometry], stock: Stock, path: Path) -> None:
    """Parts in stock coordinates, mm units, Y flipped for SVG. Importable in Estlcam/Inkscape."""
    def ring_d(coords) -> str:
        pts = [f"{x:.3f},{stock.size_y - y:.3f}" for x, y in coords]
        return "M " + " L ".join(pts) + " Z"

    paths = []
    for g in parts:
        for poly in getattr(g, "geoms", [g]):
            d = " ".join(ring_d(r.coords) for r in [poly.exterior, *poly.interiors])
            paths.append(f'  <path d="{d}" style="fill:none;stroke:#000;stroke-width:0.3"/>')
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{stock.size_x}mm" height="{stock.size_y}mm" '
        f'viewBox="0 0 {stock.size_x} {stock.size_y}">\n'
        + "\n".join(paths) + "\n</svg>\n", encoding="utf-8")


def setup_sheet(job: Job, outputs: list[Output]) -> str:
    st, m = job.stock, job.machine
    errors = sum(f.level == "FEHLER" for o in outputs for f in o.findings)
    lines = [
        f"# Einrichteblatt: {job.name}",
        "",
        "_Automatisch erzeugt - nicht von Hand bearbeiten, sondern `job.py` aendern und neu bauen._",
        "",
        f"**Status:** {'NICHT FRAESEN - Fehler siehe unten' if errors else 'Pruefungen bestanden'}",
        "",
        "## Material",
        f"- {st.material}, **{st.size_x:g} x {st.size_y:g} mm**, Dicke **{st.thickness:g} mm** (vorher nachmessen!)",
        "- Spannen: ausserhalb der Kontur, Schrauben max. 18 mm in die Opferplatte",
        "",
        "## Nullpunkt",
        "- **X0 Y0 = vordere linke Ecke** des Werkstuecks",
        "- **Z0 = Oberseite** des Werkstuecks (mit Papier antasten)",
        "",
    ]
    for n, o in enumerate(outputs, 1):
        lines += [
            f"## Datei {n}: `{o.nc.name}`",
            f"- Fraeser: **{o.tool.id}** (D {o.tool.diameter:g} mm, {o.tool.flutes} Schneiden, {o.tool.type})",
            f"- Spindel manuell: **{o.rpm} U/min**",
            f"- Geschaetzte Laufzeit: **{o.minutes:.1f} min** (ohne Beschleunigung, real eher laenger)",
            f"- Vorschau: `{o.preview.name}`",
            "",
            "Pruefung:",
            "",
            *[f"- {f}" for f in o.findings],
            "",
        ]
        if n > 1:
            lines += ["> Werkzeugwechsel: neuen Fraeser einspannen, **Z-Nullpunkt neu setzen**, X/Y bleiben.", ""]
    if job.notes:
        lines += ["## Hinweise", *[f"- {t}" for t in job.notes], ""]
    lines += [
        "## Ablauf an der Maschine",
        "Siehe Lab-Checkliste. Kurzfassung: Labnet an -> gruener Taster -> Verbinden (Grbl, "
        "/dev/ttyACM0, 115200) -> Freigeben -> Referenzfahrt -> Fraeser einspannen -> Nullpunkt "
        "setzen -> G-Code laden -> Absaugung + Spindel an -> Gehaeuse zu -> Start -> **dabei bleiben**.",
        "",
        "**Erster Lauf einer neuen Datei:** Z-Nullpunkt 10 mm ueber dem Material setzen und als "
        "Luftschnitt laufen lassen, danach Z neu nullen.",
        "",
    ]
    return "\n".join(lines)
