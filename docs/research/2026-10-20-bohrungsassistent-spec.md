# Spezifikation: Bohrungsassistent mit Verschraubung für inventa

> **Prüfnotiz (Claude, 2026-10-20):** Entwurf von Gemini 3.8 Flash, nicht
> vollständig verifiziert. ISO 273 (M3, M5, M8) stichprobenartig bestätigt.
> **Nachtrag:** Senktiefen ohne Scheibe inzwischen geprüft, 5,4 (M5) und 8,6 mm (M8) sind richtig ([Normwerte online](2026-10-20-normwerte-online.md)). Ursprünglich: **DIN 974-1 Senktiefen zweifelhaft:** M5 vermutlich 5,7 statt 5,4 mm, M8
> vermutlich 9,0 statt 8,6 mm, vor der Umsetzung gegen die Norm prüfen. Die
> Spalte „Senkung mit Scheibe (angepasst)“ ist hergeleitet, keine Normtabelle.


Stand: 2026-10-20  
Status: Entwurf / Spezifikation (Phase 1 nach [ROADMAP.md](../../ROADMAP.md))  
Grundlage: [ADR 0001 (SolidCraft-Kern unverändert, inventa als eigene Schicht)](../adr/0001-grundlage-solidcraft.md), [inventa-MCP-Server](../inventa-mcp.md), Normteile-Generator (`inventa/standard_parts.py`)

---

## 1. Einleitung und Motivation

In mechanischen Konstruktionen machen lösbare Schraubverbindungen (Schraube, Scheiben, Mutter oder Gewinde/Gewindeeinsatz, passende Durchgangs- und Kernlochbohrungen mit Senkungen) einen erheblichen Teil der Modellierungsarbeit aus.

Das klassische Vorgehen erfordert viele Einzelschritte:
1. Bohrung(en) mit Senkung im ersten Bauteil anbringen.
2. Fluchtende Bohrung(en) in den Zwischen- und Anschlussbauteilen anbringen.
3. Paketdicke (Klemmlänge) ausmessen.
4. Passende Schraubenlänge aus der Normreihe ermitteln.
5. Normteile (Schraube, Scheiben, Mutter) einzeln modellieren oder laden.
6. Alle Komponenten in der Baugruppe platzieren und über mehrere Gelenke (konzentrisch, planar, Abstände) miteinander und mit den Bohrungen verknüpfen.

Der **Bohrungsassistent mit Verschraubung** fasst diesen Prozess in einen einzigen atomaren, regelbasierten Vorgang zusammen. Er bildet das bewährte Vorbild des **Autodesk Inventor Verschraubungs-Generators** (*Bolted Connection Generator*) auf die inventa-Architektur ab – konsequent angepasst an getrennte Bauteildateien, agentengestützte Bedienung über MCP und additive Fertigung (3D-Druck).

---

## 2. Vorbild: Autodesk Inventor „Verschraubung“ (Bolted Connection Generator)

In Autodesk Inventor ist der Verschraubungs-Generator Teil des *Design Accelerator* (Konstruktionsassistenten). Er dient der automatisierten Erzeugung vollständiger Schraubenverbindungen inklusive Bohrungsgeometrie in allen betroffenen Bauteilen.

### 2.1 Benutzerauswahl und Parameter im Inventor-Dialog

Der Anwender konfiguriert die Verbindung anhand folgender Parameter:

1. **Platzierungstyp (*Type / Placement*):**
   - **Linear (*Linear*):** Auswahl einer Startfläche sowie zweier linearer Kantenreferenzen mit Abstandswerten ($d_1, d_2$).
   - **Konzentrisch (*Concentric*):** Auswahl einer Startfläche und einer kreisförmigen Kante bzw. zylindrischen Fläche (Bohrung fluchtet zentrisch zur gewählten Achse).
   - **Nach Skizzenpunkt (*On Point / By Hole*):** Auswahl vorhandener Skizzenpunkte (oder Bohrungsmittelpunkte) als Platzierungsreferenz.
   - **Nach Muster (*By Pattern*):** Verknüpfung mit einem bestehenden Komponenten- oder Feature-Muster (Änderungen der Instanzenzahl im Muster replizieren die Verschraubung automatisch).
2. **Referenzflächen für das Plattenpaket:**
   - **Startfläche (*Start Plane*):** Fläche, auf der die Schraube (bzw. die Unterkopfscheibe oder die Senkung) ansetzt.
   - **Abschlussfläche (*Termination / Bottom Plane*):** Fläche, an der die Schraube austritt (bei Durchgangsverbindung) bzw. bis zu der die Gewindebohrung maximal reicht (bei Sacklöchern).
3. **Verbindungstyp (*Connection Type*):**
   - **Durchgangsbohrung (*Through Hole*):** Alle Platten werden durchbohrt; Sicherung über Mutter auf der Austrittsseite.
   - **Sackloch / Gewindebohrung (*Blind / Tapped Hole*):** Die letzte Platte erhält eine Kernlochbohrung mit Innengewinde; die Schraube greift direkt in das Material.
4. **Zusammensetzung des Verbindungspakets (*Fastener Stack*):**
   - Schraubentyp (z. B. Zylinderschraube mit Innensechskant ISO 4762 / DIN 912, Sechskantschraube ISO 4014/4017).
   - Kopfsenkung (ja/nein, Zylindersenkung oder Kegelsenkung).
   - Scheibe(n) unter dem Schraubenkopf (z. B. ISO 7089 / DIN 125).
   - Scheibe(n) unter der Mutter.
   - Mutterntyp (z. B. Sechskantmutter ISO 4032 / DIN 934).
5. **Automatische Längenermittlung und Einschraubtiefe:**
   - Inventor misst den Abstand zwischen Start- und Abschlussfläche (Klemmlänge $t_{\text{klemm}}$).
   - Bei Sacklöchern berechnet Inventor die notwendige Einschraubtiefe anhand des gewählten Werkstoffs der Gewindekomponente (z. B. Stahl $1{,}0 \cdot d$, Aluminium $1{,}5 \cdot d$).
   - Die Schraubenlänge wird automatisch auf die nächstgrößere kommerzielle Vorzugslänge der Norm aufgerundet, sodass bei Durchgangsverschraubungen ein Gewindeüberstand von $1 \dots 2 \cdot P$ über die Mutter gewährleistet ist.

### 2.2 Was entsteht im CAD-Modell?

- **Baugruppengesteuerte Bohrungs-Features:** In **jedem einzelnen** durchdrungenen Bauteil (`.ipt`) wird das passende Bohrungs-Feature eingefügt (z. B. Senkung + Durchgangsloch in Platte 1, Durchgangsloch in Platte 2, Gewindesackloch in Platte 3).
- **Normteil-Instanzen:** Die gewählten Verbindungselemente werden aus dem Inhaltscenter (*Content Center*) instanziiert und in die Baugruppe (`.iam`) eingefügt.
- **Baugruppen-Abhängigkeiten (*Constraints / Joints*):**
  - Koaxiale Ausrichtung aller Normteile zur Bohrungsachse.
  - Flächenpaarungen: Scheibe auf Bauteil/Senkgrund, Schraubenkopf auf Scheibe/Senkgrund, Scheibe auf Austrittsfläche, Mutter auf Scheibe.
- **Zusammenfassung im Modell-Browser:** Alle Komponenten und Bohrungen werden unter einem gemeinsamen Browser-Knoten (*Bolted Connection*) geführt und bleiben als Gesamtheit editierbar.

---

## 3. Abbildung auf inventa

### 3.1 Architekturprinzipien (nach ADR 0001 und inventa-mcp)

1. **Bauteile und Baugruppen sind getrennte Dateien:**
   - Bauteile liegen als eigenständige `.solidcraft`-Dateien im Workspace (`kind: "part"`).
   - Die Baugruppe verweist auf diese Bauteile über verknüpfte Komponenten (`component.insert_design`, `kind: "assembly"`).
   - Bohrungen dürfen **nicht** als reine temporäre Baugruppenschnitte erzeugt werden, sondern müssen als echte, parametrische Features in den jeweiligen Bauteildateien stehen.
2. **Prozedurale Normteile statt Datenbank:**
   - Normteile werden über `inventa/standard_parts.py` als vollwertige parametrische Einzelteile im Workspace generiert (z. B. `ISO_4762_M5x25.solidcraft`).
3. **Agenten-Bedienung über MCP:**
   - Das Werkzeug muss von KI-Agenten und Skripten mit einer präzisen Signatur aufrufbar sein, ohne GUI-Klickpfade vorauszusetzen.
4. **Additive Fertigung (3D-Druck) als First-Class-Option:**
   - Neben klassischen geschnittenen Gewinden in Metall/Guss muss direkt die 3D-Druck-Variante mit Einschmelz-Gewindeeinsätzen (Ruthex / CNC Kitchen) unterstützt werden.

---

### 3.2 Vorgeschlagene MCP-Werkzeug-Signaturen

Für den inventa-MCP-Server (`inventa/server.py`) werden zwei Werkzeuge spezifiziert:

#### A. `bolted_connection` (Ausführung)

```python
@mcp.tool()
def bolted_connection(
    assembly: str,
    placement: dict,
    size: str,
    fasteners: dict | None = None,
    fit: str = "normal",
    counterbore: bool = True,
    connection_type: str = "through",
    blind_material: str | None = None,
    use_insert: bool = False,
    name: str | None = None,
) -> dict:
    """Erzeugt eine vollständige Verschraubung über Dateigrenzen hinweg: schneidet
    Bohrungen in alle betroffenen Bauteildateien, generiert Normteile und fügt sie mit
    Gelenken in die Baugruppe ein.

    assembly: Dokumentname der Baugruppe (z. B. "vorrichtung.solidcraft").
    placement: Platzierungsangabe:
      - konzentrisch: {"type": "concentric", "occurrence": "Flansch:1", "axis": [x, y, z] | "face": face_name}
      - skizzenpunkt: {"type": "points", "occurrence": "Platte:1", "sketch": "Skizze1", "points": ["p1", "p2"]}
      - linear/koordinaten: {"type": "point", "position": [x, y, z], "direction": [dx, dy, dz]}
    size: Metrische Gewindegröße, z. B. "M3", "M4", "M5", "M6", "M8", "M10", "M12".
    fasteners: Definition des Verbindungspakets (Defaults: ISO 4762, ISO 7089, ISO 4032):
      {
        "screw_norm": "ISO 4762",      # Zylinderschraube mit Innensechskant
        "washer_head": True,           # Scheibe unter Schraubenkopf
        "washer_nut": True,            # Scheibe unter Mutter (nur bei through)
        "nut_norm": "ISO 4032",        # Sechskantmutter (nur bei through)
        "length_override": float|None  # Explizite Schraubenlänge übersteuern
      }
    fit: Durchgangsloch-Passung nach ISO 273: "fine" | "normal" | "loose".
    counterbore: Kopfsenkung nach DIN 974-1 an Startplatte erzeugen (Standard: True).
    connection_type: "through" (Durchgangsverbindung mit Mutter) oder
                     "blind" (Sackloch mit Innengewinde im letzten Bauteil).
    blind_material: Werkstoff des Sackloch-Bauteils zur automatischen Bestimmung der
                    Einschraubtiefe: "steel" | "cast_iron" | "alu_wrought" | "alu_cast" | "plastic".
    use_insert: True wählt die 3D-Druck-Variante mit Ruthex-Einschmelzgewinde im letzten Bauteil
                (ignoriert blind_material und erzeugt Aufnahmebohrung nach Ruthex-Norm).
    name: Optionaler Bezeichner der Verschraubung (z. B. "Verschraubung_Deckel").
    """
```

#### B. `preview_bolted_connection` (Trockenlauf / Prüfung vor Ausführung)

```python
@mcp.tool()
def preview_bolted_connection(
    assembly: str,
    placement: dict,
    size: str,
    fasteners: dict | None = None,
    fit: str = "normal",
    counterbore: bool = True,
    connection_type: str = "through",
    blind_material: str | None = None,
    use_insert: bool = False,
) -> dict:
    """Berechnet die Schnittgeometrie, Klemmlängen, gewählte Normteile und Bohrungsparameter
    ohne Dateien zu verändern."""
```

---

### 3.3 Ablauf über Dateigrenzen hinweg

Der Aufruf von `bolted_connection` läuft intern in sechs synchronisierten Phasen ab:

```
[Baugruppe: Geometrie-Raycast & Klemmlänge]
                   │
                   ▼
[1. Bauteildateien öffnen & transformieren]
                   │
                   ▼
[2. solid.hole in jede Bauteildatei schreiben & speichern]
                   │
                   ▼
[3. standard_parts erzeugen (Schraube, Scheiben, Mutter/Insert)]
                   │
                   ▼
[4. Bauteile & Normteile in Baugruppe per insert_part laden]
                   │
                   ▼
[5. Gelenke add_joint setzen & update_links mit #3330-Reparatur]
                   │
                   ▼
[6. Metadaten bolted_connections in Baugruppe protokollieren]
```

#### Phase 1: Geometrische Durchdringungsanalyse (Raycast in der Baugruppe)
1. Ausgehend von `placement` wird in der Baugruppe ein Richtungsstrahl (Achse $A = P_0 + \lambda \cdot \vec{d}$) in Weltkoordinaten definiert.
2. Ermittlung aller Occurrences im Baugruppenbaum, deren Körper vom Strahl geschnitten werden:
   - Sortierung der Schnittpunkte entlang $\vec{d}$.
   - Bestimmung von Eintritts- und Austrittsflächen je Bauteil.
   - Berechnung der Teildicken $t_i = s_{\text{austritt}, i} - s_{\text{eintritt}, i}$.
3. Bestimmung der Rollen:
   - Erste Occurrence: Kopfseite (erhält Durchgangsbohrung bzw. Senkung).
   - Mittlere Occurrences: Durchgangsbohrungen.
   - Letzte Occurrence:
     - Bei `connection_type == "through"`: Durchgangsbohrung.
     - Bei `connection_type == "blind"`: Sackloch mit Innengewinde.
     - Bei `use_insert == True`: Aufnahmebohrung für Ruthex-Einsatz.

#### Phase 2: Bearbeitung der Bauteildateien (Cross-File Operations)
Für jedes betroffene Bauteil:
1. Lokale Koordinatentransformation:
   $$\vec{P}_{\text{local}} = T_{\text{occ}}^{-1} \cdot \vec{P}_{\text{world}}, \quad \vec{D}_{\text{local}} = R_{\text{occ}}^{-1} \cdot \vec{D}_{\text{world}}$$
2. Bauteildatei über den Workspace öffnen: `doc = ws.open(part_path)`.
3. Ausführen des passenden `solid.hole`-Befehls über `run(doc, [cmds])`:
   - **Kopfbauteil mit Senkung:**
     ```json
     {
       "command": "solid.hole",
       "params": {
         "position": [x_loc, y_loc, z_loc],
         "direction": [dx_loc, dy_loc, dz_loc],
         "clearance": "M5",
         "fit": "normal",
         "type": "counterbore",
         "cb_diameter": 10.0,
         "cb_depth": 5.4,
         "depth": plate_thickness,
         "name": "Bohrung_Verschraubung_Kopf"
       }
     }
     ```
   - **Zwischenbauteil(e):**
     ```json
     {
       "command": "solid.hole",
       "params": {
         "position": [x_loc, y_loc, z_loc],
         "direction": [dx_loc, dy_loc, dz_loc],
         "clearance": "M5",
         "fit": "normal",
         "depth": plate_thickness,
         "name": "Bohrung_Verschraubung_Durchgang"
       }
     }
     ```
   - **Abschlussbauteil (Sackloch mit Gewinde):**
     ```json
     {
       "command": "solid.hole",
       "params": {
         "position": [x_loc, y_loc, z_loc],
         "direction": [dx_loc, dy_loc, dz_loc],
         "thread": "M5",
         "type": "drilled",
         "tip_angle": "118 deg",
         "depth": drill_depth,
         "name": "Bohrung_Verschraubung_Gewinde"
       }
     }
     ```
   - **Abschlussbauteil (3D-Druck / Ruthex):**
     ```json
     {
       "command": "solid.hole",
       "params": {
         "position": [x_loc, y_loc, z_loc],
         "direction": [dx_loc, dy_loc, dz_loc],
         "diameter": 6.4,
         "depth": 10.5,
         "type": "drilled",
         "tip_angle": "118 deg",
         "name": "Bohrung_Ruthex_M5"
       }
     }
     ```
4. Bauteildatei speichern: `save_document(doc)`.
5. Die Skizzenregel von inventa wird in jedem Bauteil automatisch gewahrt.

#### Phase 3: Längenberechnung und Normteile-Generierung
1. **Effektive Klemmlänge:**
   $$t_{\text{klemm}} = \sum_{i} t_i - (\text{cb\_depth if counterbore else } 0) + (h_{\text{washer, head}} \text{ if washer\_head else } 0)$$
2. **Erforderliche Schraubenlänge:**
   - Durchgangsverbindung:
     $$l_{\text{req}} = t_{\text{klemm}} + (h_{\text{washer, nut}} \text{ if washer\_nut else } 0) + m_{\text{nut}} + (1{,}5 \cdot P)$$
   - Sacklochverbindung:
     $$l_{\text{req}} = t_{\text{klemm}} + s_{\text{einschraub}}$$
   - 3D-Druck (Ruthex):
     $$l_{\text{req}} = t_{\text{klemm}} + L_{\text{insert}} - 1{,}0\text{ mm}$$
3. **Auswahl der Vorzugslänge:**
   - Abgleich von $l_{\text{req}}$ gegen `ISO_4762[size]["preferred_lengths"]`.
   - Wähle das kleinste $l_{\text{norm}} \in \text{preferred\_lengths}$ mit $l_{\text{norm}} \ge l_{\text{req}}$.
4. **Erzeugung der Normteile im Workspace:**
   - Aufruf von `standard_parts.create(ws, norm="ISO 4762", size=size, length=l_norm)`.
   - Falls Scheiben: `standard_parts.create(ws, norm="ISO 7089", size=size)`.
   - Falls Mutter: `standard_parts.create(ws, norm="ISO 4032", size=size)`.
   - Falls Ruthex: `standard_parts.create(ws, norm="Ruthex", size=size)`.

#### Phase 4: Einfügen und Verknüpfen in der Baugruppe
1. Einfügen der Normteile in die Baugruppe per `insert_part(assembly, part_path, name=...)`.
2. Verknüpfungen herstellen (`add_joint`):
   - **Schraube:** Starres Gelenk (`type: "rigid"`):
     - Seite A: Unterkante des Schraubenkopfes ($z = 0$ der Schraube).
     - Seite B: Senkungsgrundfläche der Kopfplatte bzw. Oberseite der Kopfscheibe.
   - **Kopfscheibe (falls vorhanden):** Starres Gelenk zwischen Scheibenunterseite und Bauteilauflagefläche.
   - **Mutterscheibe (falls vorhanden):** Starres Gelenk an der Austrittsfläche des letzten Bauteils.
   - **Mutter (falls vorhanden):** Starres Gelenk auf Mutterscheibe bzw. Bauteilaustrittsfläche.
   - **Ruthex-Einsatz (falls vorhanden):** Starres Gelenk bündig zur Bauteiloberkante ($z = 0$).

#### Phase 5: Links aktualisieren und auf #3330 prüfen
1. Da die Bauteildateien auf der Festplatte geändert wurden, muss die Baugruppe die neuen STEP-Körper einlesen:
   `update_links(assembly, repair=True)`.
2. `inventa/links.py` prüft alle verankerten Gelenke gegen die stabilen Flächennamen der Bauteile.
3. Etwaig verschobene Gelenke werden automatisch repariert.

#### Phase 6: Metadaten protokollieren
In den Metadaten der Baugruppendatei (`doc.metadata()`) wird unter `bolted_connections` ein Eintrag hinterlegt:
```json
{
  "id": "bolted_conn_1",
  "size": "M5",
  "type": "through",
  "screw": "ISO_4762_M5x25:1",
  "washers": ["ISO_7089_M5:1", "ISO_7089_M5:2"],
  "nut": "ISO_4032_M5:1",
  "parts": [
    {"occurrence": "Deckel:1", "hole_feature": "Bohrung_Verschraubung_Kopf"},
    {"occurrence": "Gehaeuse:1", "hole_feature": "Bohrung_Verschraubung_Durchgang"}
  ]
}
```
Damit kann die Verbindung später als Ganzes geändert, umbemaßt oder sauber entfernt werden.

---

### 3.4 Normtabellen und Berechnungsgrundlagen

#### A. Durchgangslöcher nach DIN EN ISO 273 (Ausgabe 1991 / ISO 273:1979)
Durchgangsbohrungen für Schrauben werden in drei Reihen unterteilt:
- **Fein (Reihe 1 / `fine`):** Für Passschrauben oder Senkkopfschrauben mit präziser Zentrierung.
- **Mittel (Reihe 2 / `normal`):** Standardfall im Maschinenbau.
- **Grob (Reihe 3 / `loose`):** Für Schweißkonstruktionen, grobe Blechteile oder weite Lochabstände.

Lochdurchmesser $d_h$ in mm:
| Gewindegröße $d$ | Fein (`fine` / `close`) | Mittel (`normal` / `medium`) | Grob (`loose` / `coarse`) | Quelle |
|---|---:|---:|---:|---|
| **M2,5** | 2,7 | 2,9 | 3,1 | DIN EN ISO 273:1991, Tab. 1 |
| **M3** | 3,2 | 3,4 | 3,6 | DIN EN ISO 273:1991, Tab. 1 |
| **M4** | 4,3 | 4,5 | 4,8 | DIN EN ISO 273:1991, Tab. 1 |
| **M5** | 5,3 | 5,5 | 5,8 | DIN EN ISO 273:1991, Tab. 1 |
| **M6** | 6,4 | 6,6 | 7,0 | DIN EN ISO 273:1991, Tab. 1 |
| **M8** | 8,4 | 9,0 | 10,0 | DIN EN ISO 273:1991, Tab. 1 |
| **M10** | 10,5 | 11,0 | 12,0 | DIN EN ISO 273:1991, Tab. 1 |
| **M12** | 13,0 | 13,5 | 14,5 | DIN EN ISO 273:1991, Tab. 1 |

*(Hinweis: Diese Tabelle stimmt 1:1 mit der in SolidCraft unter `crates/engine/src/cmd/features.rs:1631-1653` hinterlegten Tabelle überein.)*

---

#### B. Flachsenkungen für Zylinderschrauben ISO 4762 nach DIN 974-1

Quelle: **DIN 974-1:1999-04** (*Senkungen für Zylinderschrauben – Teil 1: Schrauben mit Innensechskant*).

Bei der Senkung ist zwingend zu unterscheiden, ob unter dem Schraubenkopf eine Scheibe nach ISO 7089 liegt:
- **Ohne Scheibe (DIN 974-1 Form N / Reihe 1 mittel):** Senkdurchmesser $d_3$ ist auf den Kopfdurchmesser $d_k$ der Schraube abgestimmt.
- **Mit Scheibe (DIN 974-1 Form H bzw. angepasst):** Da der Scheiben-Außendurchmesser $d_2$ (ISO 7089) deutlich größer als der Schraubenkopf $d_k$ ist, muss der Senkdurchmesser vergrößert werden ($d_3 \ge d_2 + 0{,}5 \dots 1{,}0\text{ mm}$), und die Senktiefe muss die Scheibendicke $h$ aufnehmen.

Maße in mm:
| Größe | Schraube $d_k$ | Kopfhöhe $k$ | Scheibe ISO 7089 $d_2 \times h$ | **Senkung ohne Scheibe** (DIN 974-1 Form N)<br>Senkdurchm. $d_3$ $\times$ Tiefe $t_1$ | **Senkung mit Scheibe** (angepasst)<br>Senkdurchm. $d_3$ $\times$ Tiefe $t_1$ | Quelle |
|---|---:|---:|---|---|---|---|
| **M2,5** | 4,5 | 2,5 | $6,0 \times 0,5$ | $\varnothing\,6{,}0 \times 2{,}9$ | $\varnothing\,7{,}0 \times 3{,}4$ | DIN 974-1 Tab. 1 & ISO 7089 |
| **M3** | 5,5 | 3,0 | $7,0 \times 0,5$ | $\varnothing\,6{,}5 \times 3{,}4$ | $\varnothing\,8{,}0 \times 4{,}0$ | DIN 974-1 Tab. 1 & ISO 7089 |
| **M4** | 7,0 | 4,0 | $9,0 \times 0,8$ | $\varnothing\,8{,}0 \times 4{,}4$ | $\varnothing\,10{,}0 \times 5{,}4$ | DIN 974-1 Tab. 1 & ISO 7089 |
| **M5** | 8,5 | 5,0 | $10,0 \times 1,0$ | $\varnothing\,10{,}0 \times 5{,}4$ | $\varnothing\,11{,}5 \times 6{,}6$ | DIN 974-1 Tab. 1 & ISO 7089 |
| **M6** | 10,0 | 6,0 | $12,0 \times 1,6$ | $\varnothing\,11{,}0 \times 6{,}4$ | $\varnothing\,13{,}5 \times 8{,}2$ | DIN 974-1 Tab. 1 & ISO 7089 |
| **M8** | 13,0 | 8,0 | $16,0 \times 1,6$ | $\varnothing\,15{,}0 \times 8{,}6$ | $\varnothing\,17{,}5 \times 10{,}4$ | DIN 974-1 Tab. 1 & ISO 7089 |
| **M10** | 16,0 | 10,0 | $20,0 \times 2,0$ | $\varnothing\,18{,}0 \times 10{,}6$ | $\varnothing\,21{,}5 \times 12{,}8$ | DIN 974-1 Tab. 1 & ISO 7089 |
| **M12** | 18,0 | 12,0 | $24,0 \times 2,5$ | $\varnothing\,20{,}0 \times 12{,}6$ | $\varnothing\,25{,}5 \times 15{,}3$ | DIN 974-1 Tab. 1 & ISO 7089 |

*Hinweis zu Toleranzen:* Die Tiefenmaße $t_1$ enthalten nach DIN 974-1 ein Freimaß (ca. 0,4 bis 0,8 mm), damit der Zylinderkopf bzw. die Scheibe stets vollständig unter der Oberfläche verschwindet.

---

#### C. Kernlochbohrungen nach DIN 336 / ISO 261 (Regelgewinde)

Für das Gewindeschneiden berechnet sich der Kernlochdurchmesser theoretisch zu $d_{\text{kern}} \approx d - P$.

| Gewindegröße | Steigung $P$ (mm) | Kernlochdurchmesser $d_{\text{kern}}$ (mm) | Quelle |
|---|---:|---:|---|
| **M2,5** | 0,45 | 2,05 | DIN 336-1:1969-07 / DIN ISO 261 |
| **M3** | 0,50 | 2,50 | DIN 336-1:1969-07 / DIN ISO 261 |
| **M4** | 0,70 | 3,30 | DIN 336-1:1969-07 / DIN ISO 261 |
| **M5** | 0,80 | 4,20 | DIN 336-1:1969-07 / DIN ISO 261 |
| **M6** | 1,00 | 5,00 | DIN 336-1:1969-07 / DIN ISO 261 |
| **M8** | 1,25 | 6,80 | DIN 336-1:1969-07 / DIN ISO 261 |
| **M10** | 1,50 | 8,50 | DIN 336-1:1969-07 / DIN ISO 261 |
| **M12** | 1,75 | 10,20 | DIN 336-1:1969-07 / DIN ISO 261 |

**Bohrtiefe bei Sacklöchern:**
Um das Gewindewerkzeug nicht auf Grund laufen zu lassen, muss die Kernbohrung tiefer sein als das nutzbare Gewinde $s_{\text{einschraub}}$:
$$l_{\text{bohr}} = s_{\text{einschraub}} + a$$
mit Gewindeauslauf $a \approx 3 \dots 5 \cdot P$ (Faustwert Maschinenbau: $a \approx 0{,}5 \cdot d$).  
Spitzenwinkel des Bohrers: $118^\circ$ (DIN 1414 / SolidCraft Standard `tip_angle: "118 deg"`).

---

#### D. Mindesteinschraubtiefen nach Werkstoff (VDI 2230 / Roloff-Matek)

Um ein Abstreifen des Innengewindes vor dem Bruch der Schraube (Festigkeitsklasse 8.8) zu verhindern, gelten nach VDI 2230 Blatt 1 und Fachliteratur folgende Mindesteinschraubtiefen:

| Werkstoffgruppe | Typische Werkstoffe | Richtwert Einschraubtiefe $s_{\text{einschraub}}$ | Berechnung für M5 ($d=5\text{ mm}$) | Quelle |
|---|---|---:|---:|---|
| **Stahl / Stahlguss** | S235, C45, 42CrMo4 ($R_m \ge 400\text{ N/mm}^2$) | $1{,}0 \cdot d$ | 5,0 mm | VDI 2230 / Roloff-Matek Tab. 8.4 |
| **Grauguss** | EN-GJL-250 (GG-25) | $1{,}25 \dots 1{,}4 \cdot d$ | 7,0 mm | VDI 2230 / Roloff-Matek Tab. 8.4 |
| **Knet-Aluminiumlegierungen** | AlMgSi0.5, AlZnMgCu1.5 | $1{,}4 \cdot d$ | 7,0 mm | VDI 2230 / Roloff-Matek Tab. 8.4 |
| **Guss-Aluminiumlegierungen** | AlSi10Mg | $1{,}6 \dots 2{,}0 \cdot d$ | 9,0 mm | VDI 2230 / Roloff-Matek Tab. 8.4 |
| **Kupferlegierungen / Messing** | CuZn39Pb3 | $1{,}2 \cdot d$ | 6,0 mm | Roloff-Matek Maschinenelemente |
| **Thermoplaste (Direktverschraubung)** | POM, PA, PLA, PETG | $2{,}0 \dots 2{,}5 \cdot d$ | 11,0 mm | VDI 2230 *(im 3D-Druck unzuverlässig)* |

*(Empfehlung für den Assistenten: Bei 3D-Druckteilen Warnung ausgeben, wenn direktes Gewinde gewählt wird, und Ruthex vorschlagen).*

---

#### E. 3D-Druck-Alternative: Ruthex-Gewindeeinsätze zum Einschmelzen

Für thermoplastische Druckteile (PLA, PETG, ABS, ASA) sind direkt geschnittene Gewinde bei dynamischer Last und mehrmaligem Lösen ungeeignet. Die 3D-Druck-Variante erzeugt stattdessen die Passbohrung für messingene Rändel-Einschmelzgewinde:

Quelle: **Ruthex Datenblätter** (RX-Mxx Reihe, baugleich CNC Kitchen Standard).

| Größe | Einsatzbezeichnung | Außendurchm. $D$ | Länge $L$ | **Aufnahmebohrung $\varnothing\,d_{\text{hole}}$** | **Mindesttiefe $t_{\min}$** ($L + 1{,}0$) | Empfohlene Mindestwandstärke |
|---|---|---:|---:|---:|---:|---:|
| **M2,5** | RX-M2.5x5.7 | 4,6 mm | 5,7 mm | **4,0 mm** | **6,7 mm** | 1,5 mm |
| **M3** | RX-M3x5.7 | 4,6 mm | 5,7 mm | **4,0 mm** | **6,7 mm** | 1,5 mm |
| **M4** | RX-M4x8.1 | 6,3 mm | 8,1 mm | **5,6 mm** | **9,1 mm** | 2,0 mm |
| **M5** | RX-M5x9.5 | 7,1 mm | 9,5 mm | **6,4 mm** | **10,5 mm** | 2,5 mm |

*(Alle Maße sind bereits im Modul `inventa.standard_parts` unter `RUTHEX_INSERTS` validiert).*

---

## 4. SolidCraft-Bestand: Vorhandene Befehle und Lücken

Zur Umsetzung stützt sich inventa auf die Befehle der SolidCraft-Engine.

### 4.1 Was SolidCraft bereits bietet

| Befehl / Feature | Fundstelle im SolidCraft-Quellcode | Vorhandene Funktion |
|---|---|---|
| `solid.hole` | `crates/engine/src/cmd/features.rs:55-59` und `1630-1813` | - ISO 273 Durchgangslöcher integriert: `clearance: "M6"`, `fit: "normal"\|"fine"\|"loose"` (Z. 1630–1663)<br>- Kernlöcher automatisch berechnet: `thread: "M6"` bohrt $d - P$ (Z. 1756–1759)<br>- Zylindrische Senkung: `type: "counterbore"`, `cb_diameter`, `cb_depth` (Z. 1777)<br>- Kegelsenkung: `type: "countersink"`, `cs_diameter`, `cs_angle` (Z. 1778)<br>- Bohrspitze: `type: "drilled"`, `tip_angle` (Z. 1776)<br>- Bohrung bis Fläche: `to: [x,y,z]` (Z. 1785)<br>- Kosmetisches Gewinde direkt am Bohrungs-Feature: `thread: "M6"` (Z. 1698–1703)<br>- Bohrung folgt Skizzenpunkten: `sketch` + `points` oder alle Skizzenpunkte (Z. 1668–1697) |
| `solid.thread` | `crates/engine/src/cmd/features.rs:80-83` und `2070-2091` | Kosmetisches oder ausmodelliertes Gewinde auf Zylinderflächen |
| `solid.pattern.rectangular` | `crates/engine/src/cmd/features.rs:42-45` | Rechteckiges Muster von Features (1 oder 2 Richtungen) |
| `solid.pattern.circular` | `crates/engine/src/cmd/features.rs:46-49` | Kreismuster um Achse X/Y/Z mit Teilungswinkel |
| `solid.pattern.path` | `crates/engine/src/cmd/features.rs:50-53` | Muster entlang eines Skizzenpfades |
| `solid.mirror` | `crates/engine/src/cmd/features.rs:54` | Spiegelung von Bohrungen an Ebenen |
| `parts.insert` | `crates/engine/src/cmd/parts.rs:27-32` und `385-440` | Platziert Normteile an ein vorhandenes Loch (`at: [x,y,z]`) mit Starrem Gelenk |
| `joint.create` / `joint.edit` | `crates/engine/src/cmd/joints.rs` | Erzeugt und modifiziert Baugruppen-Gelenke (`rigid`, `revolute`, etc.) |

---

### 4.2 Was in SolidCraft fehlt (und inventa lösen muss)

1. **Kein Baugruppen-übergreifender Verschraubungsassistent:**
   - SolidCraft besitzt keinen Generator, der eine Verbindung definiert und synchron Bohrungen in mehrere Bauteile einbringt.
   - `parts.insert` bohrt **keine** Löcher, sondern verlangt ein bereits bestehendes Loch.
2. **`parts.insert` verletzt ADR 0001:**
   - SolidCrafts interner `parts.insert`-Befehl erzeugt Unterkomponenten (`component.create`) **innerhalb derselben Design-Datei** mit fest einkodierten Zahlenwerten ohne `parameters.add`. In inventa ist jedes Bauteil eine eigene Datei mit eigener Historie.
3. **Keine automatische Senkungsbemaßung nach DIN 974:**
   - `solid.hole` verlangt `cb_diameter` und `cb_depth` als manuelle Zahlenwerte; es kennt die Maße der DIN 974-1 (insb. die Differenzierung mit/ohne Scheibe) nicht.
4. **Keine automatische Einschraubtiefen- und Längenberechnung:**
   - SolidCraft berechnet weder werkstoffabhängige Gewindetiefen noch paketabhängige Schraubenvorzugslängen.
5. **Keine Ruthex- / 3D-Druck-Integration:**
   - SolidCraft kennt keine Einschmelzgewinde und keine gestuften Aufnahmebohrungen für den 3D-Druck.
6. **Topologieverlust über Dateigrenzen (#3330):**
   - Beim Aktualisieren verknüpfter STEP-Komponenten gehen die Flächennamen der Bauteile verloren.

---

## 5. Risiken, Prüfungen und Umsetzungsreihenfolge

### 5.1 Risiken und Gegenmaßnahmen

1. **Topologieverlust über Dateigrenzen (#3330):**
   - *Problem:* Schneidet man nachträglich eine Bohrung in eine Bauteildatei, verändert sich die Reihenfolge oder Identität der Flächen im B-Rep. Bei `component.update_links` in der Baugruppe können bestehende Gelenke stillschweigend auf falsche Flächen springen.
   - *Gegenmaßnahme:* 
     - Bohrungen werden nach Möglichkeit am Ende des Verlaufs eingefügt.
     - Jeder Verschraubungsvorgang ruft zwingend `inventa/links.py` (`update_links(assembly, repair=True)`) auf, welches alle Gelenkanker validiert und verschobene Gelenke repariert.
2. **Koordinaten- und Rundungsfehler beim Durchdringen:**
   - *Problem:* Bei schräg im Raum liegenden Komponenten können Rundungsfehler in den Transformationsmatrizen ($T_{\text{occ}}$) dazu führen, dass Bohrungsachsen zwischen zwei Platten leicht verspringen.
   - *Gegenmaßnahme:* Einheitliche Berechnung der Bohrungsachse im Weltkoordinatensystem der Baugruppe und präzise Invertierung mit `geometry.invert_rigid()`. Validierung, dass alle erzeugten Zylinderachsen nach dem Schnitt kollinear innerhalb $10^{-4}\text{ rad}$ und $10^{-4}\text{ mm}$ liegen.
3. **Performance bei Mehrfachverschraubungen (Muster):**
   - *Problem:* Wenn bei 16 Flanschschrauben jede Schraube einzeln gespeichert, geladen und aktualisiert wird, führt das zu 16 Datei-Schreibvorgängen und 16 Baugruppen-Neu-Evaluierungen.
   - *Gegenmaßnahme:* Batch-Verarbeitung: Alle 16 Bohrungen werden in einem einzigen `run()`-Aufruf je Bauteil platziert. Die Baugruppe aktualisiert die Links nur einmal nach Abschluss aller Bauteiländerungen.

---

### 5.2 Konkrete Testfälle für die Umsetzung

Die Implementierung wird durch folgende automatisierte Tests in `tests/inventa/check_bolted.py` verifiziert:

#### Testfall 1: Durchgangsverschraubung mit Senkung und Scheiben (Standard Maschinenbau)
- **Aufbau:** Zwei Aluminiumplatten (je $40 \times 40 \times 10\text{ mm}$), aufeinanderliegend.
- **Verschraubung:** M5, ISO 4762 mit Zylindersenkung nach DIN 974-1 (mit Scheibe ISO 7089), Scheibe unter Mutter, Mutter ISO 4032.
- **Sollwerte:**
  - Platte 1: Bohrung $\varnothing\,5{,}5\text{ mm}$, Senkung $\varnothing\,11{,}5\text{ mm}$, Tiefe $6{,}6\text{ mm}$.
  - Platte 2: Bohrung $\varnothing\,5{,}5\text{ mm}$ durchgehend.
  - Klemmlänge: $10 + 10 - 6{,}6 + 1{,}0 = 14{,}4\text{ mm}$.
  - Erforderliche Länge: $14{,}4 + 1{,}0 (\text{Scheibe}) + 4{,}7 (\text{Mutter}) + 1{,}2 (\text{Überstand}) = 21{,}3\text{ mm}$.
  - Gewählte Schraube: `ISO 4762 M5x25` (Vorzugslänge).
  - Gelenke: Alle 4 Komponenten (Schraube, 2 Scheiben, Mutter) sind mit Status `ok` verankert.

#### Testfall 2: Sacklochverbindung in Gusskörper (Werkstoffabhängig)
- **Aufbau:** Stahlplatte ($8\text{ mm}$) auf Grauguss-Sockel ($30\text{ mm}$).
- **Verschraubung:** M6, ISO 4762 ohne Senkung, Scheibe ISO 7089 unter Kopf. Werkstoff Sockel: `cast_iron` ($1{,}4 \cdot d = 8{,}4\text{ mm}$ Mindesteinschraubung).
- **Sollwerte:**
  - Stahlplatte: Durchgangsbohrung $\varnothing\,6{,}6\text{ mm}$.
  - Guss-Sockel: Kernloch $\varnothing\,5{,}0\text{ mm}$, Gewindetiefe $\ge 8{,}4\text{ mm}$, Bohrtiefe $\ge 8{,}4 + 3{,}0 = 11{,}4\text{ mm}$, Spitzenwinkel $118^\circ$.
  - Gewählte Schraube: `ISO 4762 M6x20` ($8 + 1{,}6 + 8{,}4 = 18{,}0 \to 20\text{ mm}$).

#### Testfall 3: 3D-Druck-Verbindung mit Ruthex-Gewindeeinsatz
- **Aufbau:** Deckel ($3\text{ mm}$ PLA) auf Gehäusekorpus ($20\text{ mm}$ PLA).
- **Verschraubung:** M3 mit Ruthex-Einsatz (`RX-M3x5.7`), `use_insert=True`, Senkung für Zylinderkopf M3 im Deckel.
- **Sollwerte:**
  - Deckel: Durchgang $\varnothing\,3{,}4\text{ mm}$, Senkung $\varnothing\,6{,}5 \times 3{,}4\text{ mm}$.
  - Gehäuse: Zylindrische Bohrung $\varnothing\,4{,}0\text{ mm}$, Mindesttiefe $6{,}7\text{ mm}$.
  - Normteil `Ruthex RX-M3x5.7` wird bündig an der Gehäuseoberfläche platziert.
  - Gewählte Schraube: `ISO 4762 M3x8`.

#### Testfall 4: Bohrungsmuster (4 Schrauben auf Teilkreis)
- **Aufbau:** Runder Flansch mit 4 Bohrungen über `solid.pattern.circular`.
- **Sollwerte:**
  - In beiden Flanschteilen entstehen jeweils 4 synchrone Bohrungen.
  - 4 Schrauben, 4 Scheiben und 4 Muttern werden instanziiert und korrekt gepaart.
  - `check_joints` meldet 16 Gelenke mit Status `ok`.

#### Testfall 5: Stabilität bestehender Gelenke (#3330 Regression)
- **Aufbau:** Scharniermodell mit vorhandenem Drehgelenk.
- **Aktion:** Verschraubung an einer anderen Stelle durch beide Scharnierlaschen einbringen.
- **Sollwert:** Nach `update_links` bleibt das ursprüngliche Drehgelenk auf Status `ok` und springt nicht auf die neuen Bohrungen über.

---

### 5.3 Reihenfolge der Umsetzung in kleinen Schritten

1. **Schritt 1: Regel- und Tabellenmodul (`inventa/bolted_table.py`)**
   - Datenstrukturen für ISO 273, DIN 974-1 (Form N und mit Scheibe), DIN 336, Werkstoff-Einschraubtiefen und Schraubenlängen-Auswahl.
   - Reine Python-Logik ohne CAD-Aufrufe, unit-getestet.
2. **Schritt 2: Berechnungs- und Vorschau-Werkzeug (`preview_bolted_connection`)**
   - Auswertung von Bauteildicken in der Baugruppe über Raycast / `measure`.
   - Rückgabe der ermittelten Dicken, Bohrungsmaße und Schraubenlängen zur Freigabe durch den Agenten.
3. **Schritt 3: Bauteil-Bohrungen schneiden (Cross-File Hole Writer)**
   - Transformation der Koordinaten in Bauteilsysteme.
   - Ausführen von `solid.hole` in den Bauteildateien, Einhaltung der Skizzenregel, Speichern.
4. **Schritt 4: Normteile erzeugen und in Baugruppe verknüpfen**
   - Aufruf von `standard_parts.create()`.
   - Platzierung über `insert_part()` und `add_joint()`.
5. **Schritt 5: Link-Aktualisierung und #3330-Sicherung**
   - Integration von `update_links(assembly, repair=True)`.
   - Ablage der Baugruppen-Metadaten unter `bolted_connections`.
6. **Schritt 6: 3D-Druck-Variante (Ruthex-Einsätze)**
   - Einbindung der Ruthex-Aufnahmebohrungen und Gelenkverankerung für Einschmelzgewinde.
7. **Schritt 7: Musterunterstützung & Gesamttests**
   - Unterstützung für Punktlisten und Kreismuster.
   - Gesamte Testsuite in `tests/inventa/check.py` integrieren.
