# Bearbeiten an Ort und Stelle in inventa (Gemini, 2026-10-20)

Bericht zur Umsetzung des In-Place Editing („Bearbeiten an Ort und Stelle“ nach Inventor-Art)
in `inventa/inplace.py` und der MCP-Schnittstelle in `inventa/server.py` auf dem Branch `gemini/an-ort-und-stelle`.

---

## 1. Ausgangslage und Zielsetzung

In Autodesk Inventor und anderen CAD-Systemen erlaubt „Bearbeiten an Ort und Stelle“ (Edit in Place),
ein in einer Baugruppe platziertes Bauteil direkt im Kontext seiner Einbaulage zu öffnen und zu modifizieren.

Bis zu dieser Umsetzung fehlte in `inventa` ein systematischer Mechanismus, um ausgehend von einer
Baugruppen-Occurrence das zugrundeliegende Bauteildokument zu ermitteln, im Workspace zu aktivieren
oder zu öffnen, Koordinaten zwischen Baugruppe und Bauteil umzurechnen und nach der Modifikation
die Verknüpfungen aller offenen Baugruppen konsistent zu aktualisieren.

**Anforderungen:**
1. Werkzeug `edit_in_place(assembly, occurrence, point=None)`:
   - Öffnet die Bauteildatei hinter einer Occurrence (auch in Unterbaugruppen wie `"Sub:1/Plate:1"`)
     als eigenes Dokument und gibt seinen Namen zurück.
   - Liefert die 4×4-Welt-Transformationsmatrix der Occurrence und die inverse Matrix, damit Agenten
     Punkte aus Baugruppenkoordinaten umrechnen können.
   - Ist das Bauteil bereits geöffnet, wird dieselbe Dokumentinstanz ohne Fehler zurückgegeben.
   - Optionaler Parameter `point` rechnet einen 3D-Baugruppenpunkt direkt in Bauteilkoordinaten um.
2. Werkzeug `finish_edit(part, update=True)`:
   - Speichert das Bauteil (`save`).
   - Führt bei `update=True` in allen offenen Baugruppen, die diese Datei verknüpfen (direkt oder
     über Unterbaugruppen), `update_links(repair=false)` aus.
   - Liefert die Berichte aller aktualisierten Baugruppen zurück, sodass Gelenkwarnungen
     (insbesondere verschobene Gelenke `status: "moved"` nach [#3330](https://github.com/tangency-labs/solidcraft/issues/3330))
     sofort transparent sichtbar sind.
3. Werkzeug `to_part_coords(assembly, occurrence, point)`:
   - Rechnet beliebige 3D-Weltkoordinaten aus dem Baugruppenraum in die lokalen Bauteilkoordinaten um.
4. Parallele Entwicklung / Konfliktfreiheit:
   - Parallel arbeitet ein anderer Agent auf `inventa-ebenen` an `inventa/links.py`.
   - `links.py` wurde daher überhaupt nicht verändert (vollständige Kapselung in `inventa/inplace.py`).
   - Neue Werkzeuge wurden am Dateiende von `inventa/server.py` angehängt.

---

## 2. Architektur und Umsetzung

### 2.1 Occurrence-Auflösung (`resolve_occurrence`)

In Baugruppen können Occurrences auf unterschiedliche Weise referenziert werden:
- Einfacher Name der Top-Level-Occurrence (z. B. `"Plate:1"` oder `"Plate"`).
- Pfad zu einer Komponente in einer Unterbaugruppe (z. B. `"Sub:1/Plate:1"` oder `"Sub/Plate"`).
- Interne Komponenten- oder Occurrence-Id.

`resolve_occurrence(doc, occurrence)` prüft hierarchisch:
1. **Pfadangaben mit `/`:** Sucht die Eltern-Komponente über die Baugruppen-Metadaten (`subassemblies`)
   bzw. `component.list`. Bei Unterbaugruppen werden die Metadaten `sinfo["parts"]` ausgewertet,
   wo `inventa` beim Einfügen der Unterbaugruppe die Zuordnung zur Originaldatei und zur
   Kind-Occurrence in der Oberbaugruppe festgehalten hat.
2. **Direkte Namen:** Gleicht gegen `_occurrences(doc.session)` ab.
3. **Dateipfad-Ermittlung:** Liest den Dateipfad über `_links(doc.session)` aus `component.links`
   oder aus den `subassemblies`-Metadaten.

### 2.2 Dokumentverwaltung & idempotentes Öffnen

Beim Aufruf von `edit_in_place`:
- Wird geprüft, ob eine geöffnete Datei in `ws.docs` denselben absoluten Dateipfad besitzt (`d.path.resolve() == target_path`).
- Falls ja, wird dieses Dokument zurückgegeben (keine Duplikatssitzung).
- Falls nein, wird das Dokument via `ws.open(target_path)` geöffnet. Kollidiert der Dateiname mit einem
  bereits vergebenen Dokumentnamen eines anderen Pfads, wird automatisch ein eindeutiger Alias (`stem_2`) gewählt.

### 2.3 Koordinatentransformation

SolidCraft verwendet 4×4-Matrizen in Zeilenvektorkonvention:
$$\mathbf{p}_{\text{world}} = [\mathbf{p}_{\text{local}}, 1] \cdot \mathbf{M}$$

Über `g.invert_rigid(transform)` aus `inventa/geometry.py` wird die exakte inverse Transformation
(Transponierte der Drehung + angepasste Translation) berechnet:
$$\mathbf{p}_{\text{local}} = [\mathbf{p}_{\text{world}}, 1] \cdot \mathbf{M}^{-1}$$

`edit_in_place` gibt sowohl `transform` als auch `inverse_transform` zurück und wandelt einen
optional übergebenen Punkt `point` direkt um. Zusätzlich steht das MCP-Werkzeug `to_part_coords`
für weitere Koordinatenumrechnungen bereit.

### 2.4 Warum `run_in_assembly_coords` weggelassen wurde

In der Aufgabenstellung war ein optionales Werkzeug `run_in_assembly_coords(part, assembly, occurrence, commands)`
vorgeschlagen („Nur wenn sauber machbar, sonst weglassen und begründen“).

Dieses Werkzeug wurde nach eingehender Analyse **bewusst weggelassen**. Die Gründe:
1. **2D-Skizzenebenen vs. 3D-Raum:**
   SolidCraft-Features basieren überwiegend auf 2D-Skizzen (`sketch.rectangle`, `sketch.circle`, etc.).
   Skizzenpunkte sind lokale zweidimensionale Koordinaten $(u, v)$ auf einer Skizzen- oder Arbeitsebene.
   Eine 4×4-Raumtransformationsmatrix kann 2D-Skizzenkoordinaten nicht transformieren, ohne die
   spezifische Ausrichtung der Arbeitsebene zu kennen.
2. **Fehlende Richtungsvektoren bei 3D-Primitiven:**
   Engine-Primitive wie `solid.cylinder` nehmen lediglich einen Basispunkt `base: [x, y, z]`, besitzen
   aber im Befehlssatz keinen Richtungs- oder Achsenvektor – sie extrudieren starr entlang der
   lokalen Bauteil-Z-Achse. Ist die Komponente in der Baugruppe gedreht (z. B. um 90° gekippt),
   würde die Transformation des Basispunkts den Zylinder zwar an den richtigen Punkt setzen,
   er würde aber in die falsche Richtung wachsen.
3. **Parametrische Arbeitsweise:**
   Konstruktionsänderungen im Kontext erfolgen in parametrischem CAD wie Inventor/SolidCraft über
   Parameter (`parameters.change`) oder geometrische Bezüge, nicht über absolute Rohkoordinaten.
4. **Fehleranfälligkeit bei Dutzenden Befehlen:**
   SolidCraft-Befehle nutzen Koordinaten in verschiedensten Schlüsseln (`base`, `corner`, `center`, `point`,
   `circle`, `p0`, `p1`, `edges`). Ein unvollständiges Mapping auf Befehlsebene würde zu subtilen Geometriefehlern
   führen.

**Die saubere Lösung:** Agenten nutzen `to_part_coords` bzw. den `point`-Parameter von `edit_in_place`,
um Referenzpunkte (z. B. aus semantischen Abfragen `find` oder Messungen `measure`) punktgenau umzurechnen,
und steuern die Bauteilgeometrie dann deterministisch in Bauteilkoordinaten.

### 2.5 Link-Aktualisierung (`finish_edit`)

`finish_edit(ws, part, update=True)`:
1. Speichert das Bauteil (`part_doc.save()`).
2. Durchsucht alle offenen Dokumente im `Workspace` nach Baugruppen (`doc.kind == ASSEMBLY`).
3. Prüft, ob die Baugruppe das Bauteil direkt (`component.links`) oder als Teil einer Unterbaugruppe
   (`metadata.subassemblies`) verknüpft.
4. Führt für jede gefundene Baugruppe `update_links(ws, asm_doc, repair_moved=False)` aus.
5. Sammelt die Ergebnisse und Warnungen und liefert sie zurück.

---

## 3. Verifikation und Testergebnisse

In `tests/inventa/check.py` wurden die geforderten Prüfungen implementiert (`edit_in_place_checks` sowie
MCP-Aufrufe in `mcp_server`):
1. **Baugruppe mit zwei Teilen und Gelenk:** Platte mit Bohrung (Parameter `hx = 10 mm`), zylindrischer Bolzen,
   starres Gelenk `PinInHole` koaxial zur Bohrung.
2. **Öffnen und Wiederverwenden:** `edit_in_place` öffnet geschlossenes Bauteil von Festplatte; erneuter Aufruf
   gibt dieselbe geöffnete Instanz zurück.
3. **Legitime Verschiebung:** Bohrungsverschiebung per `parameters.change` (`hx = 20 mm`). Nach `finish_edit`
   folgt das Gelenk auf $x = 20{,}0\text{ mm}$, `warnings` bleibt leer.
4. **Fall #3330:** Zusätzliche gleich große Bohrung `Hole0` an Position 1 im Bauteilverlauf eingefügt.
   `finish_edit` meldet sofort den Status `moved` in den Baugruppen-Warnungen.
5. **Unterbaugruppen:** `edit_in_place` mit Pfad `Sub:1/Plate:1` in verschachtelter Baugruppe löst die
   hierarchische Kette auf und transformiert Baugruppenpunkte unter Berücksichtigung aller Eltern-Transformationen.
6. **MCP-Server über stdio:** `edit_in_place`, `finish_edit` und `to_part_coords` erfolgreich über stdio RPC aufgerufen.

### Testergebnis

- `python3 tests/inventa/check.py`: **107 ok-Prüfungen, 0 failures** (~115 s).
- `python3 tests/reference/check.py`: **Alle Referenztests bestanden, 0 failures**.

---

## 4. Fazit

Mit `edit_in_place`, `finish_edit` und `to_part_coords` schließt inventa die verbliebene Lücke
beim dateiübergreifenden Modellieren in Baugruppen. Agenten können Baugruppenkomponenten direkt
adressieren, im Bauteilkontext ändern und die Auswirkungen auf Baugruppengelenke sofort überprüfen.
Die Trennung in `inventa/inplace.py` garantiert die vollständige Unabhängigkeit vom parallel laufenden
Zweig `inventa-ebenen`.
