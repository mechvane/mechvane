# UI-Sichtung für den Grafik-Overhaul (2026-11-06)

Methode: Skill `impeccable` critique, zwei getrennte Prüfungen (A: Design-Review auf 17 Screenshots der lokal
gebauten Live-Demo und den Quellen, B: Detektor `impeccable detect` auf `mechvane/ui/static` und im Browser auf
`?demo=bracket` und `?demo=bolted_plates`). Screenshots: `docs/galerie/2026-11-06-ui-sichtung/`.

**Gesamturteil:** Abläufe und Aufbau sind klar CAD- und Inventor-spezifisch (Ribbon, Browser mit „End of Part“,
Eigenschaften, Freiheitsgrade, Abhängigkeitssymbole). Die visuelle Schicht ist generisches Dark-Dashboard:
Systemschrift ohne Skala, Grau ohne Akzent, Kernel-Sprache als Inhalt. Nielsen 23/40.

| # | Heuristik | Note | Hauptproblem |
|---|---|---|---|
| 1 | Systemstatus | 3 | Kern lädt (~50 MB) nur mit Statuszeile, UI wirkt schon bedienbar |
| 2 | Sprache der Nutzer | 2 | `[BoxFeature]`, `F4:csink:base`, Schwerpunkt-Floats, `fdm_0.4`, `d1/d2` |
| 3 | Kontrolle | 2 | Kontextmenü nur Edit/Delete; End of Part nicht ziehbar |
| 4 | Konsistenz | 2 | EN-Oberfläche mit DE-Werten; „noch nicht gebaut“ und „hier nicht anwendbar“ gleich grau |
| 5 | Fehlervermeidung | 2 | Bohrungsdialog: leere X/Y/Z, „Edge 1: None“, Pflichtfelder unklar |
| 6 | Wiedererkennen | 2 | Keine Typ-Symbole im Baum, 7 Text-Knöpfe „Constrain“ |
| 7 | Effizienz | 3 | Kürzel gut; kein Markierungsmenü/Rechtsklick in der Ansicht, keine Befehlssuche |
| 8 | Ästhetik | 2 | Design-Check-Panel immer halbe Spalte, auch im Skizzenmodus; „ok“-Badge je Baugruppenzeile |
| 9 | Fehler beheben | 3 | FAIL-Karten mit Begründung stark; kein Sprung zum Feature, rohe Vektoren |
| 10 | Hilfe | 2 | Keine Bild-Tooltips, keine Erklärung für graue Befehle |

**Stärken:** Design Check (Badge, Kartenrand, rote Fläche im Modell), Skizzierumgebung (Freiheitsgrade, Symbole,
`name = Ausdruck`), saubere Inventor-Grundstruktur, helles Thema ohne Brüche.

## Lückenliste (ohne die schon geplanten Punkte: Baum-Symbole, Bildknöpfe in Dialogen, eigener Symbolsatz, Modell tritt im Skizzenmodus zurück)

**P1, verhindert ein fertiges Aussehen**
1. Baum: `[BoxFeature]` in Monospace weg, Symbol + Name, Typ im Tooltip; kein Umbruch langer Namen.
2. Kernel-IDs und rohe Zahlen aus sichtbaren Texten: `Highlighted face: F4:csink:base`, Schwerpunkt-Floats,
   `fdm_0.4`, Flächen-Chips, Parameter `d1/d2/d3` ohne Bezug.
3. Ansicht: Teil schwebt flach auf Schwarz. Verlauf, Bodenschatten oder -raster, deutlichere Silhouettenkanten.
4. Skizzenebene: hartes Rechteck, 1-px-Linien kaum sichtbar; Raster, kräftigere Linien und Punkte, deutlichere
   Farbe für voll bestimmt (vorhanden, aber Weiß gegen Blau ist schwach).
5. Typografie: eine feste UI-Schrift mit 3–4 Stufen statt Systemschrift (Ribbon, Baum und Karten gleich laut).
6. Mobil: Ribbon abgeschnitten ohne Scroll-Hinweis, kein Browser, Agent nicht erreichbar.

**P2**
7. Design-Check-Panel einklappen, wenn alles OK oder ein Befehl/Skizze aktiv ist.
8. Baugruppen-Browser zu dicht: Gelenke in eigenen Ordner, Status nur bei Problemen.
9. Parameterpanel im Skizzenmodus zeigt Bauteil-Parameter statt der Skizzenmaße.
10. Eigenschaftenpanel: Umbrüche („Middle of face“), Ausrichtung, kontrastarmer OK-Knopf, Pflichtfelder.
11. Graue Befehle: „kommt noch“ ausblenden oder kennzeichnen, „hier nicht anwendbar“ mit Grund im Tooltip.
12. Ladezustand des Demo-Kerns als Overlay statt stiller Statuszeile.
13. Agent-Panel: in 1440×900 nicht sichtbar, im Skizzenmodus gequetscht. Platz für das Kernversprechen festlegen.
14. Kontextmenü: Gruppen, Trenner, Symbole, Löschen abgesetzt; Unterdrücken, Umbenennen, Ein-/Ausblenden.

**P3**
15. File-Menü zeigt die Beispiele doppelt (Auswahl und Liste).
16. Sprachmix DE/EN in Werten und Profilnamen („FDM 3D-Druck“).
17. Barrierefreiheit: kein `:focus-visible`, keine aria-Attribute in `features.js`, graue Badges unter 4,5:1.
18. Kein `prefers-reduced-motion`, nur ein Umbruchpunkt (760 px); 1180 px eng.
19. Achsenkreuz und Home-Knopf provisorisch; ViewCube wäre Inventor-Standard.

## Detektor (Prüfung B)

Echte Befunde, unabhängig vom Overhaul behebbar:
- **Überdeckung:** `file-doc-item` „Bolted connection (assem…“ zu 53 % von `ribbon-group-title` verdeckt;
  im Baugruppen-Baum `tree-meta` „Z Axis“ zu 83 % vom `badge-ok` verdeckt.
- **Kontrast:** `#fff` auf `#d97757` (Senden-Knopf des Agenten) 3,1:1, Soll 4,5:1.
- `model.html`: Fließtext 11,5 px.

Bewusst dicht und für ein CAD-Ribbon üblich (Fehlalarm im Sinne der Konvention, metrisch aber korrekt): 20×
Gruppentitel 10 px, Baum und Badges 11 px. Seitenstreifen 4 px an Meldungskarten (style.css:949) sind
Statuskodierung, kein Schmuck. `#e6edf3` auf `#1c2d48` ist heller Text auf dunklem Navy: Fehlalarm.

## Fragen an den Nutzer (aus Prüfung A)

- Der Agent ist das Versprechen („You and your agent on the same model“), aber in der Standardansicht unsichtbar,
  während der Design Check die halbe rechte Spalte belegt.
- Soll Mechvane wie Inventor aussehen oder nur so funktionieren? Ein Symbolsatz im Inventor-Stil lädt zum direkten
  Vergleich ein.
- Die Demo öffnet mit einem fehlschlagenden Teil (Winkel mit FAIL): gewollt als erster Eindruck?

## Entscheidungen (Nutzer 2026-11-06)

1. Der Agent wird gleichrangig sichtbar, muss aber ausblendbar sein.
2. Eigener Stil, nicht die Optik von Inventor; die Abläufe bleiben Inventor-nah.
3. Die Live-Demo startet mit einem Teil, das die Prüfung besteht (Flansch zuerst in `mechvane/examples.py`).

Nachprüfung der Detektor-Befunde: Beide Überdeckungen sind Fehlalarme (Inhalt eines geschlossenen `<details>` behält in
Chromium seine Maße, wird aber nicht gezeichnet). Behoben: Kontrast Senden-Knopf (`#b8562f`, 4,8:1) und die doppelte
Beispielliste im File-Menü (Auswahlliste ausgeblendet).

