# CNC-as-Code (Shapeoko 3 XXL, FLKA)

Fraesprojekte als Python-Code: Design → G-Code → automatische Pruefung → Simulation →
Einrichteblatt. Gedacht fuer die Zusammenarbeit mit einer AI. Hintergrund und
Fahrplan stehen in [PLAN.md](PLAN.md).

## Schnellstart

```bash
python3 -m venv ../.venv && ../.venv/bin/pip install -r requirements.txt
../.venv/bin/python -m cnc build projects/herz
```

Ergebnis in `projects/herz/out/`:

| Datei | Wofuer |
|---|---|
| `herz.nc` | G-Code fuer die Fraese |
| `SETUP.md` | Einrichteblatt: Material, Fraeser, Nullpunkt, Pruefergebnis |
| `herz.png` | Vorschau: Werkzeugbahn und simuliertes Ergebnis |
| `herz.svg` | Kontur als SVG, z.B. fuer Estlcam |

Eine fremde `.nc`-Datei pruefen (z.B. aus Estlcam):

```bash
../.venv/bin/python -m cnc check meine.nc --stock 100x95x6 --tool flat-4mm-2f --preview vorschau.png
```

## Projekte
- [herz](projects/herz/out/SETUP.md): 75-mm-Herz, 2,5D ausgeschnitten, 4-mm-Zweischneider
