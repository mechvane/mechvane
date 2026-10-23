# Wissenskatalog: Plan (2026-10-20)

Ziel des Nutzers: Die Agenten sollen so viel praktisches Konstruktionswissen
wie möglich direkt zur Hand haben, nicht nur Normmaße, sondern auch das, was
in keiner Norm steht. Alles Zugängliche wird systematisch abgegrast und in
einem Wissensgraphen zusammengefasst. Normen werden nicht gekauft und nicht
abgeschrieben, nur einzelne Werte und Regeln mit Quelle übernommen.

## Quellen, nach Verlässlichkeit

1. **Normwerte aus Sekundärquellen:** Herstellerkataloge (Bossard, Würth,
   Böllhoff, EJOT, Kerb-Konus), Tabellen in Hochschulskripten. Erste
   Recherchen: `2026-10-20-normtabellen-flash.md`,
   `-einschraubtiefen-flash.md`, `-senkungen-gewindefreistich-flash.md`.
2. **Öffentliche Handbücher von Raumfahrt und Militär:** NASA Fastener
   Design Manual (RP-1228) und NASA-Standards, ESA ECSS-Handbücher
   (z.B. ECSS-E-HB-32-23A Schraubverbindungen), MIL-Handbooks. Enthalten
   das Warum (Sicherung, Kerbwirkung, Montage). Lizenz je Dokument prüfen.
3. **Design-Guides von Herstellern und Fertigern:** SKF, Schaeffler, igus,
   Misumi, Protolabs, Xometry, Prusa, Ruthex, CNC Kitchen. Erste Recherche:
   `2026-10-20-fertigungsregeln-fdm-cnc-flash.md`.
4. **Hochschulskripte** zu Maschinenelementen und Konstruktionslehre
   (Gestaltungsregeln: Kraftfluss, Kerben, fertigungs- und montagegerecht).
5. **Offene Datensätze:** cq_warehouse (Apache-2.0, Empfehlung von Flash),
   BOLTS, FreeCAD Fasteners, BOSL2, NopSCADlib. Lizenz selbst prüfen.
   Recherche: `2026-10-20-offene-normteil-datensaetze-flash.md`.
6. **Auswertung guter offener Konstruktionen:** Voron, Prusa und andere
   Open Hardware als STEP laden und mit `find`/`measure` auswerten, welche
   Wandstärken, Radien, Schrauben und Passungen tatsächlich verwendet werden.
7. **Eigene Versuche:** Prüfkörper auf dem Ultimaker 2+ (Skill `3d-druck`)
   für Passungsspiel, Gewindeeinsätze, Überhang, Lochmaße, Brücken;
   messen und als eigene Messwerte eintragen.
8. **Erfahrung des Nutzers:** kurze Befragungsrunden; jede Korrektur im
   Betrieb wird eine Regel mit Begründung.
9. **Wissen der Modelle:** nur als Hypothese, bis eine Quelle oder ein
   Versuch es bestätigt.

## Eintrag im Katalog

Jede Regel oder jeder Wert ist ein Datensatz, nicht Code:

- Aussage bzw. Wert mit Einheit, Geltungsbereich (Werkstoff, Verfahren,
  Größe, Festigkeitsklasse)
- Herkunft: Norm (über Sekundärquelle) / Hersteller / Lehrbuch / Handbuch /
  Versuch / Erfahrung / Hypothese
- Quellen mit URL, Seite, wörtlichem Zitat; „belegt“ erst ab zwei
  unabhängigen Quellen oder einem eigenen Versuch
- Begründung (warum) und Ausnahmen
- Härte: Fehler (harte Grenze) oder Hinweis (Best Practice), so meldet
  `check_design` nur bei harten Regeln „fail“
- Prüfstatus: automatisch (Zahl im Quell-PDF gefunden), von Hand geprüft,
  offen

## Graph

Knoten: Regel, Wert, Quelle, Werkstoff, Verfahren (FDM, CNC, Guss …),
Feature (Bohrung, Gewinde, Wand, Rippe …), Normteil, Versuch.
Kanten: gilt_für, belegt_durch, widerspricht, leitet_ab, ersetzt,
geprüft_durch. Widersprüche zwischen Quellen bleiben sichtbar statt
überschrieben. Die Agenten fragen den Graphen über ein inventa-Werkzeug
ab („Regeln für Sackloch M6 in Aluguss, FDM-Druck“). Technik offen:
graphify (schon im Repo), eigene JSON-Dateien plus Index, oder das
assistant-graph-Muster; Entscheidung als ADR.

## Ablauf

1. Abgrasen: Flash-Recherchen pro Themengebiet (Gemini-Kontingent),
   Rohfassungen unter `docs/research/`.
2. Automatisch prüfen: Links erreichbar, Zahl im Quelltext gefunden
   (Skript, kein Claude-Kontingent). So fiel am 2026-10-20 der
   Abschreibfehler bei Hanke auf.
   Mit Browser-User-Agent abrufen; was trotzdem gesperrt ist, kommt in
   `2026-10-20-quellen-nicht-erreichbar.md` (Code, Art, Recherche). Bei
   wertvollem Inhalt holt der Nutzer die Datei von Hand; Volltexte bleiben
   privat, nicht im öffentlichen Repo.
3. Übernehmen: geprüfte Einträge in den Katalog, Rest bleibt „offen“.
4. Versuche planen für Werte ohne belastbare Quelle.
5. Öffentlich: „Belege Wert X mit zwei Quellen“ als Einstieg zum Mitmachen.

## Themenliste zum Abgrasen

Schraubverbindungen (Sicherung, Vorspannung, Einschraubtiefe, Senkungen),
Gewinde (Freistiche, Einsätze, Kunststoff), Passungen und Toleranzen
(ISO 286 über Sekundärquellen, Lagersitze), Wälz- und Gleitlager (Einbau,
Schultern, Radien), Wellen (Nuten, Sicherungsringe, Kerben), Blech
(Biegeradien, Ausklinkungen), Guss, Schweißen, Kunststoffspritzguss
(Entformung, Wand, Rippen, Dome), FDM-Druck, CNC-Fräsen und -Drehen,
Kleben, Federn, Dichtungen (O-Ring-Nuten), Gestaltungsregeln allgemein
(Kraftfluss, Montage, Wartung).
