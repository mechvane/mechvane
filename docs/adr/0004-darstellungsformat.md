# ADR 0004: Darstellung von Werkstoffen – glTF-PBR mit OpenPBR-Namen, Kennwerte in der SolidCraft-Karte

- Status: **angenommen** (2026-10-29, Nutzer; vorgeschlagen und geprüft am selben Tag von Claude)
- Entscheidet: in welchem offenen Format Mechvane das Aussehen von Werkstoffen speichert, damit es sich
  1:1 in Blender rendern und in der Web-UI (three.js) zeigen lässt, und wie Aussehen und physikalischer
  Werkstoff zusammenhängen
- Bezug: ROADMAP „Material- und Darstellungseditor“ und „Werkstoffdatenbank“, ADR 0001 (SolidCraft-Kern
  unverändert), ADR 0002 (Katalogformat), Recherche
  [Darstellungsformat](../research/2026-10-29-darstellungsformat-flash.md) (Issue #15)

## Kontext

Der Nutzer wünscht einen Material- und Darstellungseditor, dessen Format sich ohne Umweg zum Rendern in
Blender nutzen lässt. Zwei Dinge sind zu trennen, wie in klassischem Maschinenbau-CAD:

- **Physikalischer Werkstoff:** Dichte, E-Modul, Festigkeiten, Wärmewerte. Grundlage für Masse und
  Prüfregeln. SolidCraft 0.25 speichert das bereits je Werkstoff als **Kennwertkarte** (`physical_card`,
  Schema 1, SI, Quelle je Wert) und in Bibliotheken `solidcraft-library/2`. Mechvane erzeugt daraus seit
  2026-10-29 eine Bibliothek aus dem Katalog (`tools/katalog_to_solidcraft.py`).
- **Aussehen:** Farbe, Rauheit, Metall, Klarlack, Anisotropie (gebürstet), Transmission, Texturen.
  SolidCraft speichert davon nur `color`, `opacity` und `pbr: {metallic, roughness, dielectric_ior}`.

Geprüfte Kandidaten (Recherche #15, 16 von 16 Zitaten bestätigt; Nachprüfung 2026-10-29):

| Format | Blender | three.js (Web-UI) | Bewertung |
|---|---|---|---|
| MaterialX mit OpenPBR | kein direkter `.mtlx`-Import; Export nur über USD („MaterialX Network“), seit 4.5 als OpenPBR. In den Pipeline-Notes zu 5.0, 5.1 und 5.2 kein MaterialX-Import | `MaterialXLoader` nur mit WebGPU-Renderer | am ausdrucksstärksten, heute nicht 1:1 nutzbar |
| USD / UsdPreviewSurface | Import vorhanden, laut Handbuch verlustbehaftet | nur rudimentär (USDZ) | zu schwach für Klarlack/Anisotropie, schwere Bibliotheken |
| glTF 2.0 PBR + KHR_materials_* | Import/Export im Lieferumfang, bildet auf Principled BSDF ab | `GLTFLoader` → `MeshPhysicalMaterial` | in beiden Zielen nativ, schlankes JSON |

## Probe (2026-10-29)

Logo-Testmodell (`tools/build_logo_showcase.py`) mit sieben Oberflächen: Pulverbeschichtung navy und
hellgrau (mit Klarlack), Schweißnaht, Messing gebürstet (anisotrop), Kupfer poliert, Edelstahl gebürstet,
brünierte Schrauben. Gleiche Szene in Blender 5.2.2 (Cycles), zwei Wege:

- **A, direkt:** OpenPBR-Werte aus `tools/logo_looks.json` per Skript auf den Principled BSDF.
- **B, glTF:** `tools/logo_to_gltf.py` schreibt glTF 2.0 mit `pbrMetallicRoughness`,
  `KHR_materials_clearcoat` und `KHR_materials_anisotropy`; Blenders eigener Importer liest es.

Ergebnis (`ROUTE=direct|gltf` in `tools/render_logo_blender.py`, Werte nach dem Laden ausgelesen):

- Alle sieben Werkstoffe kommen über glTF mit **identischen Principled-Werten** an (Grundfarbe, Metall,
  Rauheit, IOR, Anisotropie, Klarlack-Stärke und -Rauheit).
- Bild: mittlere Abweichung 0,1 von 255 je Kanal, mit bloßem Auge kein Unterschied
  ([nebeneinander](../media/adr0004-probe.png)). Abweichungen nur an zwei Stellen, beide im eigenen
  Exporter begründet: die **Schliffrichtung** des Messings (glTF ohne `TANGENT`, der direkte Weg setzt sie
  per Tangentenknoten) und die **Schattierung an den Nahtkanten** (glTF ohne `NORMAL`).

Zweiter Lauf mit Normalen je B-Rep-Fläche, `TANGENT` und UVs entlang der Schliffrichtung: Die
Nahtkanten sind jetzt sauber getrennt (genauer als die pauschale Winkelglättung des direkten Wegs, daher
mittlere Abweichung 0,35 statt 0,1). Die **Schliffrichtung** überträgt Blenders Importer (5.2) aber auch so
nicht: Die Anisotropie-Stärke kommt an, die Richtung bleibt Blenders Standard.

Dritter Lauf: `brushed_finish` in `tools/render_logo_blender.py` setzt nach dem glTF-Import Tangente und
Schleifspuren für alle Werkstoffe mit Anisotropie. Danach keine Abweichung mehr im Messing; im ganzen Bild
mittel 0,25, höchstens 50 von 255, nur noch an den Kanten (Normalen je Fläche statt Winkelglättung).

Folgerung: Für diesen Parametersatz trägt glTF nach Blender, mit einer Lücke: die Richtung gebürsteter
Oberflächen. Dafür reicht ein kleines Nachbearbeitungsskript nach dem Import (Tangentenknoten setzen), ein
eigener Blender-Weg für alle Werkstoffe ist nicht nötig.

## Entscheidung (Vorschlag, nach der Probe)

1. **Datenmodell** für das Aussehen ist ein **OpenPBR-Parametersatz** (Werte, kein Shader-Graph), wie in
   `tools/logo_looks.json`. Ein späterer MaterialX-Export ist damit nur eine Abbildung.
2. **Austausch und Web-UI über glTF 2.0** (`pbrMetallicRoughness` plus `KHR_materials_clearcoat`,
   `_anisotropy`, `_transmission`, `_volume`, `_ior`, `_specular`, `_sheen`, `_emissive_strength`). Der
   Exporter schreibt Normalen je B-Rep-Fläche, Tangenten und UVs. Blender liest das mit dem mitgelieferten
   Importer (Probe: Werte identisch); für die Schliffrichtung setzt ein kleines Skript nach dem Import den
   Tangentenknoten. three.js liest es mit `GLTFLoader`.
3. **Physikalischer Werkstoff** bleibt die SolidCraft-Kennwertkarte, gespeist aus dem Katalog (ADR 0002).
   Ein Werkstoff hat ein Standard-Aussehen und beliebig viele **Oberflächen** (gebürstet, poliert,
   eloxiert), die nur das Aussehen ändern.
4. **In SolidCraft** landet die darstellbare Teilmenge (`color`, `opacity`, `pbr`); der Rest liegt in
   Mechvanes Metadaten des Dokuments und geht beim Export mit.

## Folgen

- Kein neues Format zu pflegen, keine schwere Abhängigkeit (kein USD, kein MaterialX zur Laufzeit).
- Texturen und prozedurale Muster (Rändel, Bürstrichtung als Textur) sind nur über Bilddateien möglich;
  Anisotropie-Richtung reicht für gebürstete Oberflächen ohne Textur.
- Neu prüfen, sobald Blender `.mtlx` importiert oder three.js MaterialX im WebGL-Renderer zeigt.

## Offen

- Prüfen, ob three.js (`GLTFLoader`) die Anisotropie-Richtung aus `TANGENT` übernimmt.
- `brushed_finish` aus dem Logo-Skript in ein allgemeines Mechvane-Werkzeug für den Blender-Export überführen.
