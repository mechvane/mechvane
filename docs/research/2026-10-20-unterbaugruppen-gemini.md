# Unterbaugruppen in inventa (Gemini 4 Argon, 2026-10-20)

Bericht zur Untersuchung von SolidCraft (`/root/repos/_ext/solidcraft` sowie
installiertes `solidcraft-cli` v0.16.2) und zur Umsetzung von Unterbaugruppen in
`inventa/` auf dem Branch `gemini/unterbaugruppen`.

---

## 1. Was SolidCraft kann – und was nicht (mit Belegen)

### 1.1 `component.insert_design` klopft Baugruppendateien flach

Wird eine `.solidcraft`-Baugruppendatei per `component.insert_design` in eine
Oberbaugruppe eingefügt, entsteht **keine** verschachtelte Komponenten-Hierarchie:

- [`component_insert_design`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/component.rs#L653-L711)
  lädt die Quelldatei über
  [`load_linked_part`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/component.rs#L611-L651).
- `load_linked_part` ruft
  [`world_solids_from_part`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/component.rs#L574-L609)
  auf. Dort werden alle sichtbaren Körper des Quelldokuments über
  `doc.occurrence_world_transform(occ.id)` in Weltkoordinaten gebacken, als ein
  einziger STEP-Blob serialisiert (`solidcraft_exchange::write_step_ named`) und in
  der Zielbaugruppe als **ein** `FeatureKind::Import`-Feature in **einer**
  Komponente abgelegt.
- Die `components`, `occurrences`, `links` und `joints` der Unterbaugruppe werden
  dabei vollständig verworfen.
- [`component_update_links`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/component.rs#L747-L845)
  iteriert ausschließlich über `session.doc.links` des aktuellen Dokuments und
  ruft erneut `load_linked_part` auf, ohne rekursiv `links` in der geladenen
  Datei auszuwerten. Ändert sich eine Bauteildatei `part.solidcraft`, merkt eine
  Oberbaugruppe, die nur `sub.solidcraft` per `component.insert_design`
  eingebunden hat, davon nichts, solange `sub.solidcraft` nicht selbst geöffnet,
  aktualisiert und gespeichert wird.

### 1.2 Verschachtelte Komponenten im selben Dokument funktionieren

SolidCrafts Datenmodell unterstützt beliebig geschachtelte Komponenten im
selben Dokument:

- [`Component`](file:///root/repos/_ext/solidcraft/crates/doc/src/assembly.rs#L17-L38)
  besitzt `parent: Option<ComponentId>`, und
  [`Occurrence`](file:///root/repos/_ext/solidcraft/crates/doc/src/assembly.rs#L45-L62)
  besitzt `parent: ComponentId` sowie `transform: [f64; 16]` relativ zur
  Eltern-Komponente.
- `component.create` und `component.insert_design` akzeptieren `parent` (Name
  oder Id der Eltern-Komponente).
- [`Document::occurrence_world_transform`](file:///root/repos/_ext/solidcraft/crates/doc/src/assembly.rs#L483-L526)
  multipliziert die lokalen `transform`-Matrizen über die `parent`-Kette bis zur
  Wurzel (`parent == 0`), wobei es je Eltern-Komponente deren erste Occurrence
  (`occurrences_of(cur_comp).first()`) heranzieht.
- [`component.list`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/component.rs#L176-L246)
  liefert zu jeder Komponente `parent`, `occurrences` (die eigenen Instanzen)
  und `children` (die direkten Kind-Occurrences mit `o.parent == c.id`). In
  beiden Listen ist `transform` die **lokale** 4×4-Matrix relativ zu `o.parent`,
  nicht die Weltmatrix.

### 1.3 Gelenke und Solver bei verschachtelten Occurrences

Praktische Versuche mit `inventa.documents.Workspace` und Code-Prüfung ergaben
vier wichtige Eigenschaften von SolidCrafts Gelenksystem:

1. **Weltkoordinaten in `joint.create` und `joint.list`:**
   [`pick_joint_origin`](file:///root/repos/_ext/solidcraft/crates/engine/src/cmd/joints.rs#L387-L445)
   transformiert die Körper einer Occurrence vor dem Picking mit
   `doc.occurrence_world_transform(occ_id)` in Weltkoordinaten und speichert den
   gefundenen `JointFrame` anschließend über `inv_transform_frame(&world, ...)`
   lokal auf der Occurrence. Umgekehrt gibt `joint.list` (`frame_a`, `frame_b`)
   die Rahmen wieder über `occurrence_world_transform` in Weltkoordinaten aus.
2. **Fixierung (`grounded`) wirkt im Solver nur auf Blatt-Occurrences:**
   [`joints::solve`](file:///root/repos/_ext/solidcraft/crates/doc/src/joints.rs#L1756)
   sammelt fixierte Occurrences über
   `doc.occurrences.iter().filter(|o| o.grounded)`. Ob die Eltern-Occurrence
   `Sub:1` `grounded = true` hat, prüft der Solver **nicht** für deren Kinder.
   Damit eine frei eingefügte Unterbaugruppe (`grounded=False`) als Einheit
   beweglich bleibt, dürfen ihre Kind-Occurrences nach dem Anlegen nicht
   dauerhaft auf `grounded=True` stehen; während die inneren Gelenke der
   Unterbaugruppe beim Einfügen nachgebildet werden, müssen die Kinder dagegen
   kurzzeitig fixiert sein, damit Zwischenschritte des Solvers unverbundene Teile
   nicht verschieben. Ist die Unterbaugruppe mit `grounded=True` eingefügt,
   bleiben ihre in der Unterbaugruppe fixierten Teile auch in der Oberbaugruppe
   fixiert.
3. **Eindeutige Komponentennamen nötig:**
   [`Document::add_occurrence`](file:///root/repos/_ext/solidcraft/crates/doc/src/assembly.rs#L391-L393)
   vergibt den Occurrence-Namen `"{cname}:{k}"` pro `ComponentId`. Heißen zwei
   verschiedene Komponenten gleich (z. B. `Bolt` in der Oberbaugruppe und `Bolt`
   in der Unterbaugruppe), erzeugen beide eine Occurrence `Bolt:1`, wodurch die
   Namensauflösung in `joint.create` mehrdeutig wird.
4. **Versionsunterschied bei `occurrence.move`:**
   Im neueren Quellstand (`/root/repos/_ext/solidcraft`) unterstützt
   `occurrence.move` einen `matrix`-Parameter (`component_matrix.rs`); das
   installierte Binary `/root/.local/bin/solidcraft-cli` (v0.16.2) ignoriert
   `matrix` noch stillschweigend, unterstützt aber `translate`, `axis`, `angle`,
   `space: "local"` und `base_transform`. Durch Zerlegung einer starren
   4×4-Matrix in `(translate, axis, angle)` mit `base_transform: IDENTITY`
   ([`geometry.move_params`](file:///root/repos/inventa-gemini/inventa/geometry.py#L63-L80))
   lässt sich jede lokale Pose auf Maschinenpräzision (`~1e-16`) setzen.

---

## 2. Was in `inventa` gebaut wurde

### 2.1 Entscheidung: `insert_part` erweitern statt eigenes `insert_assembly`

`insert_part` wurde für Baugruppendateien erweitert (statt ein zusätzliches
Werkzeug `insert_assembly` einzuführen):

- Sowohl Bauteile als auch Baugruppen sind `.solidcraft`-Dateien im selben
  Arbeitsordner und teilen sich dieselben Platzierungsparameter (`assembly`,
  `part_path`, `name`, `translate`, `grounded`).
- Auch in Autodesk Inventor werden Einzelteile und Unterbaugruppen über denselben
  Befehl (*Komponente platzieren*) eingefügt.
- Ein gemeinsames Werkzeug hält die MCP-Werkzeugliste klein und erspart dem
  Aufrufer, vor dem Einfügen prüfen zu müssen, ob eine `.solidcraft`-Datei ein
  Bauteil oder eine Baugruppe ist.

### 2.2 Einfügen und Gelenk-Nachbildung (`links.insert` / `_insert_subassembly`)

1. **Erkennung:** [`_is_assembly`](file:///root/repos/inventa-gemini/inventa/links.py#L207-L219)
   liest `document.json` aus dem `.solidcraft`-Zip-Archiv (mit Fallback über
   `ws.reader`) und prüft `metadata["io.github.nilsgollub.inventa"]["kind"] == "assembly"`
   bzw. das Vorhandensein von `links`.
2. **Eltern-Komponente & Bauteile:** In der Oberbaugruppe wird per
   `component.create` eine Eltern-Komponente `Sub` (`Sub:1`) angelegt, bei Bedarf
   verschoben (`translate`) und fixiert (`grounded`). Darunter wird jedes
   verknüpfte Bauteil der Unterbaugruppe einzeln per `component.insert_design`
   mit `parent=sub_comp` verknüpft (bei Namenskollision als `<Sub>_<Part>`) und
   mit `occurrence.move` (`geometry.move_params`) auf seine lokale
   Unterbaugruppen-Transformation gesetzt.
3. **Gelenke nachbilden:** Alle Gelenke der Unterbaugruppe werden in der
   Oberbaugruppe über [`_recreate_sub_joint`](file:///root/repos/inventa-gemini/inventa/links.py#L246-L310)
   echt nachgebildet (`type`, `flip`, `offset`, `angle`, `values`, `limits`,
   `suppressed`), indem ihre Rahmen mit der Weltmatrix von `Sub:1` transformiert
   und in `joints` der Oberbaugruppe samt Bauteilflächen-Verankerung aus der
   Unterbaugruppe gespeichert werden. Dadurch bleiben sowohl starre als auch
   bewegliche Freiheitsgrade (z. B. `revolute`) der Unterbaugruppe erhalten.
4. **Metadaten:** Unter `metadata["io.github.nilsgollub.inventa"]["subassemblies"][sub_name]`
   wird festgehalten, welche Komponente (`component`, `occurrence`) aus welcher
   Unterbaugruppendatei (`file`, `path`) stammt und welche Kind-Occurrences
   (`parts`) und Gelenke (`joints` mit Parameter-Stand) daraus angelegt wurden.

### 2.3 Weltkoordinaten, äußere Gelenke und `#3330` (`links.py`)

- [`_occurrences`](file:///root/repos/inventa-gemini/inventa/links.py#L31-L51)
  berechnet `transform` als Weltmatrix über die gesamte `parent`-Kette
  (`geometry.mat_mul(cur["transform"], m)`) und bewahrt die lokale Matrix in
  `local_transform`.
- [`resolve_occurrences`](file:///root/repos/inventa-gemini/inventa/links.py#L187-L204)
  erlaubt in `add_joint` und `edit_joint` neben dem direkten Occurrence-Namen
  (`Plate:1`) auch Pfadangaben wie `Sub:1/Plate:1` (einschließlich automatischer
  Auflösung auf `<Sub>_Plate:1` bei Namenskollision).
- `record`, `check` und `repair` arbeiten über die Weltmatrix mit der echten
  Bauteildatei des jeweiligen Unterbaugruppen-Teils. Damit funktionieren
  Bohrungsverschiebungen und die `#3330`-Erkennung samt Reparatur auch für
  Gelenke zwischen der Oberbaugruppe und einem Bauteil in einer Unterbaugruppe.

### 2.4 `update_links` für Unterbaugruppen (`_sync_subassemblies`)

[`_sync_subassemblies`](file:///root/repos/inventa-gemini/inventa/links.py#L441-L601)
läuft am Anfang von `update_links` vor `component.update_links`:

- Bestimmt zunächst den aktuellen starren Rahmen (`t_frame`) der Unterbaugruppe
  innerhalb von `Sub:1`, falls ein äußeres Gelenk die Teile der Unterbaugruppe
  in der Oberbaugruppe verschoben hat.
- Löscht entfernte oder geänderte Gelenke der Unterbaugruppe zuerst, damit
  `session.refresh()` während `component.insert_design` verschobene Teile nicht
  auf alte Gelenkpositionen zurückzieht.
- Löscht in der Unterbaugruppendatei entfernte Bauteile (`component.delete`),
  fügt neu hinzugekommene Bauteile unter `Sub` ein (`component.insert_design`),
  aktualisiert geänderte Bauteil-Transformationen (`occurrence.move`) und legt
  neue oder geänderte Unterbaugruppen-Gelenke neu an.
- Gibt in `update_links` unter `"subassemblies"` für jede Unterbaugruppe
  `status` (`"unchanged"`, `"updated"`, `"file_missing"`), `added`, `removed`
  und `moved` zurück.

### 2.5 Browser (`tree.py`)

- [`tree.assembly_tree`](file:///root/repos/inventa-gemini/inventa/tree.py#L121-L185)
  und [`tree.render`](file:///root/repos/inventa-gemini/inventa/tree.py#L220-L236)
  stellen Unterbaugruppen-Occurrences mit ihrer Quelldatei (`Sub:1 (sub_unit.solidcraft)`)
  und rekursiv eingerückten Kind-Occurrences dar.
- In der Ordneransicht (`groups=True`) erhalten Gelenke, deren beide Seiten in
  derselben Unterbaugruppe liegen, in `groups["relations"]` das Feld
  `"owner": "Sub:1"` (im Text `→ Sub:1`).

---

## 3. Offene Punkte

1. **Solver bewegt Blatt-Occurrences statt der Eltern-Occurrence:**
   SolidCrafts Gelenklöser verschiebt bei einem äußeren Gelenk auf `Sub:1/Plate:1`
   die Blatt-Occurrences (`Plate:1`, `Bolt:1`) innerhalb von `Sub:1`, während
   `Sub:1` selbst auf seinem Einfüge-Offset stehenbleibt. `_sync_subassemblies`
   rechnet diese Verschiebung über `t_frame` heraus; schöner wäre upstream in
   SolidCraft, wenn starre/bewegliche Unterbaugruppen-Container ihre
   Eltern-Occurrence mitführen könnten.
2. **Mehrfach-Instanzen derselben Komponente per `occurrence.copy`:**
   Wird eine Unterbaugruppen-Komponente im selben Dokument über `occurrence.copy`
   mehrfach instanziiert, teilt SolidCrafts `occurrence_world_transform` die
   Eltern-Transformation der ersten Occurrence. Wer dieselbe Unterbaugruppe
   mehrfach unabhängig platzieren will, sollte `insert_part` mehrfach aufrufen
   (legt jeweils eine eigene Eltern-Komponente `Sub`, `Sub_2` mit eigenen
   Kind-Occurrences an).
3. **Ebenen-Reparatur bei `#3330`:**
   Wie bei einstufigen Baugruppen werden auf Ebenen verankerte Gelenke bei
   `#3330` als `moved` gemeldet, aber derzeit nur Zylinder-Verankerungen
   automatisch repariert.
