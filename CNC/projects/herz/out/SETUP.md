# Einrichteblatt: herz

_Automatisch erzeugt - nicht von Hand bearbeiten, sondern `job.py` aendern und neu bauen._

**Status:** Pruefungen bestanden

## Material
- holz, **99 x 91 mm**, Dicke **6 mm** (vorher nachmessen!)
- Spannen: ausserhalb der Kontur, Schrauben max. 18 mm in die Opferplatte

## Nullpunkt
- **X0 Y0 = vordere linke Ecke** des Werkstuecks
- **Z0 = Oberseite** des Werkstuecks (mit Papier antasten)

## Datei 1: `herz.nc`
- Fraeser: **flat-4mm-2f** (D 4 mm, 2 Schneiden, flat)
- Spindel manuell: **24000 U/min**
- Geschaetzte Laufzeit: **1.4 min** (ohne Beschleunigung, real eher laenger)
- Vorschau: `herz.png`

Pruefung:

- [INFO] Verfahrbereich X 0.0..89.0  Y 0.0..80.9  Z -6.30..5.00 mm
- [INFO] Vorschuebe 300..800 mm/min
- [INFO] Geschaetzte Laufzeit 1.4 min (ohne Beschleunigung)

## Hinweise
- Erster Test: Vorschub 800 mm/min und 2 mm Zustellung (Lab-Tabelle: 1000 / 4 mm). Wenn es ruhig laeuft, darf der Vorschub waehrend des Laufs erhoeht werden.
- Haltestege nach dem Fraesen mit Cutter/Saege trennen und verschleifen.
- Die Kerbe oben wird mit Radius 2 mm verrundet (Fraeserradius) - das ist normal.

## Ablauf an der Maschine
Siehe Lab-Checkliste. Kurzfassung: Labnet an -> gruener Taster -> Verbinden (Grbl, /dev/ttyACM0, 115200) -> Freigeben -> Referenzfahrt -> Fraeser einspannen -> Nullpunkt setzen -> G-Code laden -> Absaugung + Spindel an -> Gehaeuse zu -> Start -> **dabei bleiben**.

**Erster Lauf einer neuen Datei:** Z-Nullpunkt 10 mm ueber dem Material setzen und als Luftschnitt laufen lassen, danach Z neu nullen.
