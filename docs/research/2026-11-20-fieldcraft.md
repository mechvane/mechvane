# FieldCraft (Tangency Labs), erste Notiz

Stand 2026-11-20. Quelle: 3Druck.com, „FieldCraft: Open-Source-Tool zur Simulation von CAD-Bauteilen als freie
Abaqus-Alternative“, 19.11.2026 (https://3druck.com/programme/fieldcraft-open-source-tool-zur-simulation-von-cad-bauteilen-als-freie-abaqus-alternative-07166034/).
Nur Sekundärquelle, Repo und Doku noch nicht gelesen; Herstellerangaben unbestätigt.

- Quelloffene CAE-Anwendung von Tangency Labs, „selbe Familie wie SolidCraft“. Version 0.8.1, Windows, macOS, Linux, Browser.
  Lizenz MIT oder Apache-2.0.
- Öffnet parametrische SolidCraft-Teile „mit festen Namen für Flächen, Kanten und Körper“; Lager und Lasten hängen an
  diesen Namen und bleiben beim Neuvernetzen erhalten. Liest außerdem 3MF-Netze mit markierten Flächen.
- Netze: Schwerpunkt Hexaeder (Teil in SolidCraft in Zellen teilen, Beispiel L-Winkel in 30 Zellen, 0,1 % Abweichung
  zur feinen Vergleichsrechnung), zusätzlich automatischer Vernetzer, Tetraeder, Balken, Schalen, Federn.
- Löser selbst in Rust: linear, große Verformungen, Plastizität, Gummi, Eigenschwingungen, Wärme, Thermospannungen,
  explizite Dynamik (Sturz, Stoß), Luftströmung. Export für Abaqus, Nastran, LS-DYNA.
- Prüfung: 170 von 176 Werten aus 50 Fällen, sechs Abweichungen dokumentiert.
- Bedienung: Fenster, Kommandozeile, KI-Agenten (Vorführung mit Claude: Kragträger 1 kN, 0,176 mm gegen 0,177 mm Lehrbuch).
- Fehlt noch: Knicken, Kontakt zwischen Bauteilen (als Nächstes geplant). „Frühe Version“.

## Bezug zu Mechvane

ROADMAP Phase 2, Punkt FEM (eigener Schnellcheck mit scikit-fem, dann CalculiX). FieldCraft deckt beides bis auf Kontakt ab
und kennt die Flächennamen von SolidCraft. Vor dem Start (nach v0.1) prüfen: Repo, Schnittstelle (MCP/CLI), Dateiformat für
Lasten und Lager, eigene Probe gegen ein Lehrbuchbeispiel. Repo-Recherche bei Bedarf an Gemini. Bis zum Audit 30.11. nichts anfangen.
