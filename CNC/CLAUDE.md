# CNC-as-Code – Anweisungen fuer AI-Sitzungen

Werkzeugkette fuer die Shapeoko 3 XXL im FLKA. Plan und Fahrplan: `PLAN.md`.

## Befehle (aus `CNC/`)
```bash
../.venv/bin/pip install -r requirements.txt           # einmalig, venv liegt im Repo-Root
../.venv/bin/python -m cnc build projects/<name>        # baut .nc, .png, .svg, SETUP.md nach out/
../.venv/bin/python -m cnc check datei.nc --stock 100x95x6 --tool flat-4mm-2f --preview p.png
../.venv/bin/python -m pytest -q
```

## Konventionen
- Einheiten mm. **X0 Y0 = vordere linke Werkstueckecke, Z0 = Werkstueckoberseite.** Negative Z gehen ins Material.
- Ein Projekt ist `projects/<name>/job.py` mit einer Funktion `job() -> Job`. `out/` ist erzeugt, wird mit eingecheckt (damit man die Datei im Lab von GitHub laden kann) und nie von Hand bearbeitet.
- Eine `.nc`-Datei pro Fraeser. Werkzeugwechsel ist manuell, danach wird der Z-Nullpunkt neu gesetzt.
- G-Code: nur ASCII, G21/G90, kein M3 (die Spindel wird von Hand geschaltet), erste Bewegung ist ein senkrechtes `G0 Z<safe>`.
- Code-Kommentare englisch, alles fuer den Menschen (Einrichteblatt, Meldungen) deutsch.

## Datenherkunft (nicht verwechseln)
- `tools.toml` Presets = Lab-Checkliste: die verbindliche Obergrenze. `flute_length` ist geschaetzt.
- `machine.toml`: Arbeitsraum und Portalhoehe stammen aus den Kursfolien. `max_feed` und `rapid_feed` sind Schaetzungen.
- Werte nie stillschweigend erhoehen. Vorschuebe ueber dem Preset nur auf ausdruecklichen Wunsch.

## Bevor du "fertig" sagst
1. Build ohne `FEHLER`, `pytest` gruen.
2. **Das Vorschaubild `out/*.png` ansehen.** Stimmen Form, Groesse, Haltestege und Lage auf dem Material?
3. Pruefen, ob `SETUP.md` die richtige Materialstaerke und den richtigen Fraeser nennt.

## Erweitern
- Neue Operation: Klasse mit `generate(job) -> Toolpath` (siehe `Profile` in `cnc/ops.py`), dazu ein Test, der das Ergebnis per Simulation nachweist (Beispiel: `test_herz_has_tabs_and_cuts_through`).
- Neue Sicherheitsregel: in `cnc/check.py`, mit einem Test in `test_checker_catches`.
- Der Checker arbeitet nur auf geparstem G-Code. So soll es bleiben, damit er auch fremde Dateien prueft.
