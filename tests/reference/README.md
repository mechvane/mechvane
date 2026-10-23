# Referenzteile

Eigene Teile mit von Hand gerechneten Sollwerten, gegen die jede
SolidCraft-Version (und später Mechvane selbst) geprüft wird.

```sh
python3 tests/reference/check.py            # alle Teile, ~10 s
python3 tests/reference/check.py scharnier  # ein Teil
```

Braucht nur `solidcraft-cli` im `PATH` (getestet mit v0.16.2 und v0.19.0), kein pytest.
Jedes `<teil>.build.json` ist ein Befehlsskript, wie es auch ein MCP-`batch`
nimmt. `check.py` hängt einen Parameter-Walk an, lässt alles in einer Sitzung
laufen (`solidcraft-cli run --results`) und vergleicht mit den Formeln in
`check.py`.

| Teil | Deckt ab | Geprüft |
|---|---|---|
| `flansch` | Skizze, Extrusion, Fase, Zylinderschnitt, Kreismuster mit Anzahl-Parameter | Volumen, Bounding-Box bei n = 4/6 und T = 8/10 |
| `gehaeuse` | Druckteil: Eckenrundung, Schale, Dome als Ringprofil, Rechteckmuster mit Ausdrucksabständen | Volumen und Schwerpunkt-Z bei L = 80/120, Wand 2/3, Domhöhe 20/28 |
| `blechwinkel` | Blechregel, Grundlasche, Kantenlasche, Bohrungen M6 (ISO 273), Abwicklung | Volumen, Biegezugabe π/2·(R+K·t), Abwickellänge, Laschenhöhe 30/50 |
| `scharnier` | Komponenten, Festlegen, Drehgelenk mit Grenzen, Kontaktsätze | Deckel-Schwerpunkt bei 0/45/90°, Stopp bei Kontakt (180°), kein Weiterdrehen |
| `welle` | Drehteil per solid.revolve, 3 Durchmesserabsätze, Sicherungsring-Einstich (Revolve-Cut), Endfase | Volumen (Zylindersumme minus Einstich minus Kegelstumpffase), Bounding-Box und Länge bei d1=16/18, L1=20/25, d2=24/28, L2=30/35, d3=18/20, L3=20/25 |
| `rohrhalter` | Rohrschelle per solid.sweep (Linie-Bogen-Linie-Pfad), Flachsenkungen per solid.hole (counterbore) | Volumen (Pappus-Bandvolumen minus 2 Senkbohrungen), Flanschlänge bei R = 40/50, W = 24/30, Lf = 25/30 |
| `rippenplatte` | Platte mit Rippen (Extrusion), lineares Muster mit Anzahl-Parameter, Mittelebenenspiegelung (solid.mirror), Kehlnaht-Fillet | Volumen (exakt ungerundet plus Kehlnaht-Viertelkreis A = r²·(1-π/4)), Bounding-Box bei n = 2/3 und Rippenhöhe hr = 15/20 |

Toleranzen: Volumen relativ 2e-4 (gemessen bis 2e-5, SolidCraft misst eine
Tessellierung), Positionen 2e-3 mm. Neue Teile: Build-Skript ablegen, Walk und
Sollwerte als Funktion in `check.py` ergänzen, in `PARTS` eintragen.
