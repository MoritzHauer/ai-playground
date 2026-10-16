# CNC-as-Code – Plan

Ziel: Ein stark automatisierbarer Workflow fuer die Shapeoko 3 XXL im FLKA, bei dem
**jeder Schritt Text oder Code ist**. So kann eine AI Designs erzeugen, G-Code
berechnen, das Ergebnis selbst pruefen und verbessern, und Git haelt jede Version fest.
Anfangs: einfache 2,5D-Teile. Spaeter: V-Carving, 3D-Reliefs und AI-generierte Kunst.

## Grundprinzipien

1. **Alles ist Code.** Ein Projekt ist eine `job.py`. Alles in `out/` wird erzeugt und nie von Hand bearbeitet.
2. **Pruefen ist unabhaengig vom Erzeugen.** Checker und Simulation lesen den fertigen
   G-Code neu ein, nicht die internen Daten. Sie pruefen also, was die Maschine wirklich
   bekommt, und funktionieren genauso fuer G-Code aus Estlcam, FreeCAD oder F-Engrave.
3. **Die AI prueft sich selbst.** Jeder Build erzeugt ein Vorschaubild der Simulation.
   Eine AI-Sitzung schaut es an, bevor sie etwas als fertig meldet.
4. **Die Maschine bleibt beim Menschen.** Einspannen, Nullpunkt setzen, Luftschnitt und
   Beaufsichtigen werden nicht automatisiert, so wie es die Lab-Regeln verlangen.
5. **Klein anfangen, an echten Laeufen kalibrieren.** Jede neue Faehigkeit wird erst an
   der Maschine bestaetigt, bevor die naechste darauf aufbaut.

## Architektur

```
projects/<name>/job.py          Projekt: Material + Geometrie + Operationen
        │
        ▼
cnc/shapes.py                   Geometrie (shapely-Polygone, mm, X0Y0 vorne links)
cnc/ops.py                      Operationen -> Toolpath   (Profile; spaeter Pocket, Drill, VCarve, Relief)
cnc/toolpath.py                 Zwischenformat: Liste von Moves
cnc/post.py                     Toolpath -> Grbl-G-Code   (eine Datei pro Fraeser)
        │  .nc-Datei
        ▼
cnc/gcode.py                    G-Code neu einlesen (G0-G3)   ◄── auch fuer fremde .nc-Dateien
cnc/check.py                    Sicherheitspruefung gegen config/machine.toml + tools.toml
cnc/sim.py                      Materialabtrag auf Hoehenkarte + Vorschaubild
cnc/report.py                   SETUP.md (Einrichteblatt) + SVG
```

**Erweiterungspunkte.** Neue Faehigkeiten kommen dazu, ohne bestehenden Code umzubauen:

| Neu | Wo | Bedingung |
|---|---|---|
| Form / Import (SVG, DXF, Text) | `shapes.py` oder neues Modul | liefert shapely-Geometrie |
| Operation (Tasche, V-Carve, Relief) | `ops.py` oder eigenes Modul | Methode `generate(job) -> Toolpath` |
| Fraesertyp (Kugel, V) | `tools.toml` + Kernel in `sim.py` | Kugel ist schon simuliert |
| Externes CAM (FreeCAD, F-Engrave) | erzeugt `.nc` | wird mit `python -m cnc check` geprueft |
| Andere Maschine / Steuerung | neue `machine.toml`, eigener Post | Toolpath bleibt gleich |

**Bewusst einfach gehalten:** Fuer Konturen, Taschen und Bohrungen schreiben wir den
CAM-Teil selbst. Das sind wenige, gut testbare Zeilen. Fuer schwere Faelle (echtes 3D
aus STL, V-Carving) binden wir spaeter vorhandene Bibliotheken oder Tools ein, sobald
der Bedarf konkret ist. Die Grenze dorthin ist die `.nc`-Datei.

## Fahrplan

### Phase 0 – Grundgeruest ✅
- Paket `cnc/`, Maschinen- und Fraeserdaten aus Kursfolien und Checkliste
- Kontur-Operation mit Mehrfachzustellung, Rampe und Haltestegen
- G-Code-Checker, Simulation mit Vorschau, Einrichteblatt, Tests
- Erstes Projekt `projects/herz`: 75-mm-Herz, 4-mm-Zweischneider, ausgeschnitten

### Phase 1 – Erster echter Lauf und Kalibrierung
- Herz fraesen (Luftschnitt, dann echt). Ergebnis in `projects/herz/LOG.md` festhalten: Fotos, Laufzeit, Auffaelligkeiten.
- Klaeren, ob die Lab-Oberflaeche (vermutlich CNCjs) unsere Dateien ohne Murren laedt.
- Echte Schneidenlaengen in `tools.toml` eintragen, Eilgang und Vorschuebe in `machine.toml` an der gemessenen Laufzeit nachjustieren.
- **Fertig, wenn:** ein Herz sauber ausgeschnitten ist und die Laufzeit-Schaetzung stimmt (±30 %).

### Phase 2 – 2,5D ausbauen
- Operationen: `Pocket` (Taschen, Inseln), `Profile` innen, `Drill`
- Import: SVG (z.B. `svgelements`), DXF (`ezdxf`), Text als Pfade (`fonttools`)
- Projekt: Herz-Schale (Aussenkontur + Tasche, wie `Schalen.svg`)
- Optional: GitHub Action, die bei jedem Push alle Projekte baut und die Tests laufen laesst

### Phase 3 – V-Carving
- V-Fraeser in `tools.toml` und Simulation
- Entscheidung nach einem Versuch: eigene Medial-Axis-Berechnung oder F-Engrave per Kommandozeile
- Projekt: Schild mit Schrift

### Phase 4 – 3D-Reliefs
- Operation `Relief` aus Hoehenkarte (PNG oder numpy): Schruppen mit Flachfraeser in Z-Stufen mit Aufmass, Schlichten mit Kugelfraeser als Raster ("drop cutter" auf der Hoehenkarte)
- STL in eine Hoehenkarte umrechnen
- Laufzeit wird wichtig (Stunden): Schaetzung und Aufteilung in mehrere Dateien
- Projekt: gewoelbtes Herz-Relief, ca. 80 × 80 mm in MDF

### Phase 5 – AI-Kunst-Pipeline
- Bild (generiert oder Foto) -> Tiefenschaetzung (z.B. Depth Anything) -> bereinigte Hoehenkarte -> Relief
- Bild -> Vektorisierung (potrace) -> V-Carving oder Gravur
- Eine Projektvorlage oder ein Claude-Skill, der aus einem Satz ("Untersetzer mit Eule, 90 mm, Linde") ein fertiges Projekt baut

## Offene Fragen (im Lab klaeren)
- Welche Fraeser gibt es wirklich (Kugel-, V-, Gravierfraeser)? Wie lang sind die Schneiden?
- Welche Software laeuft an der Fraese (CNCjs?), und versteht sie unsere Kommentare?
- Welche Materialien und Brettstaerken liegen vorraetig?
- Welche Skala hat der Drehzahlregler der Spindel?

## Sicherheitsregeln (nicht verhandelbar)
- Eine Datei mit **FEHLER** im Einrichteblatt wird nicht gefraest.
- Jede neue Datei laeuft zuerst als **Luftschnitt** (Z-Null 10 mm ueber dem Material).
- Vorschuebe ueber der Lab-Tabelle nur nach bewusster Entscheidung des Menschen.
- Waehrend des Fraesens ist immer jemand an der Maschine.
