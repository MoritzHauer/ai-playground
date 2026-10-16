"""Erster Test: 2,5D-Herz, ca. 75 mm breit, aus Holz ausgeschnitten, 4-mm-Zweischneider.

Bewusst vorsichtig: halber Vorschub und halbe Zustellung gegenueber der Lab-Tabelle.
"""
from shapely import affinity

from cnc import Job, Stock
from cnc.ops import Profile, Tabs
from cnc.shapes import heart

THICKNESS = 6.0  # mm - an das echte Brett anpassen und neu bauen!
MARGIN = 12.0    # mm Rand rund ums Herz (Platz fuer Fraeser + Schrauben)


def job() -> Job:
    shape = heart(width=75.0)
    _, _, w, h = shape.bounds
    stock = Stock(size_x=round(w + 2 * MARGIN), size_y=round(h + 2 * MARGIN), thickness=THICKNESS)
    shape = affinity.translate(shape, (stock.size_x - w) / 2, (stock.size_y - h) / 2)

    return Job(
        name="herz",
        stock=stock,
        parts=[shape],
        operations=[
            Profile(
                shape, tool="flat-4mm-2f", side="outside",
                depth=THICKNESS + 0.3,   # 0,3 mm in die Opferplatte, damit es sauber durch ist
                stepdown=2.0, feed=800, plunge=300,
                tabs=Tabs(count=4, width=6.0, height=1.5),
                label="Herz Aussenkontur",
            )
        ],
        notes=[
            "Erster Test: Vorschub 800 mm/min und 2 mm Zustellung (Lab-Tabelle: 1000 / 4 mm). "
            "Wenn es ruhig laeuft, darf der Vorschub waehrend des Laufs erhoeht werden.",
            "Haltestege nach dem Fraesen mit Cutter/Saege trennen und verschleifen.",
            "Die Kerbe oben wird mit Radius 2 mm verrundet (Fraeserradius) - das ist normal.",
        ],
    )
