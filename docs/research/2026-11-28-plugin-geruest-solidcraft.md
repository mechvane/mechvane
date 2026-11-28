# Recherche für U2: Aufbau eines SolidCraft-Plugins (WIT, Manifest, Installation, Beispiele, Grenzen) ab 0.45 bis 0.50

- **Datum:** 2026-11-28
- **Bezug:** Issue #237 (Zuarbeit für U2 / #220: Rust-WASM-Plugin für Prüfregeln als Ribbon-Eintrag und MCP-Werkzeug)
- **Arbeitsbasis:** SolidCraft `v0.50.0` (Plugin-Vertrag `craft:plugin@0.2.0`, geprüft ab `v0.45.0` über `v0.48.0` bis `v0.50.0`)
- **Abgerufen:** alle Quellen am 2026-11-28 geprüft

---

## Überblick für das U2-Plugin-Gerüst

Ein SolidCraft-Plugin ist ein Paketordner (für die Auslieferung als `.zip`), der mindestens ein JSON-Manifest (`plugin.json`) und eine aus Rust nach `wasm32-unknown-unknown` gebaute sowie mit `wasm-tools component new` umhüllte WebAssembly-Komponente enthält `[Q1]`. Für ein Prüfregel-Plugin (U2) passt ein reines Command-Plugin mit `"effect": "read"`, `"capabilities": ["commands@0.2"]`, einem Slot `{"kind": "ribbon", "name": "Inspect"}` (oder `"Model"`) und ausschließlich lesenden Engine-Befehlen wie `document.inspect`, `inspect.measure`, `inspect.classify_points`, `model.faces`, `model.edges` oder `model.mesh` `[Q2][Q3][Q4][Q5]`. Jedes installierte, aktivierte Entry erscheint automatisch sowohl im Ribbon/Plugins-Menü als auch als MCP-Werkzeug `<plugin>.<entry>` `[Q6][Q7]`.

---

## 1. Plugin-Vertrag (WIT-Datei, Welten, Importe/Exporte, v0.45.0 vs. v0.50.0)

### 1.1 Paket und Welten in `v0.50.0`

Die verbindliche Schnittstelle liegt in `crates/craft-plugin/wit/plugin.wit` unter dem Paket `craft:plugin@0.2.0` `[Q8]`. Daneben existieren:

- `crates/craft-plugin/wit-0.1/plugin.wit` (`craft:plugin@0.1.0`): eingefrorener Vorgängervertrag, den der Host weiterhin parallel bedient `[Q8][Q9]`.
- `crates/craft-plugin/wit-host/plugin.wit` (`craft:host@0.1.0`): separates, rein lesendes Zusatzpaket mit `world host-query { import capabilities; }`, über das ein Plugin per `granted()` abfragen kann, welche optionalen Capabilities der Host unterstützt `[Q10][Q11]`.

`crates/craft-plugin/wit/plugin.wit` (`v0.50.0`) definiert zwölf Welten `[Q8]`:

| Welt | Importe | Exporte | Einsatz / Capability |
|---|---|---|---|
| `command-plugin` | `forms`, `commands`, `user-storage`, `design-state`, `log`, `control`, `files`, `clock`, `storage` | `entry` (`execute`) | Standard-Command-Plugin (`commands@0.2` + optionale Capabilities) |
| `importer-plugin` | `log`, `control`, `clock`, `source`, `design`, `evaluate` | `importer` (`import-file`) | Dateiformat-Importer (`formats@0.2`, optional `evaluate@0.2`) |
| `importer-plugin-with-storage` | `importer-plugin` + `user-storage` | `importer` | Importer mit Nutzer-Einstellungen (`user-storage@0.1`) |
| `folder-reader` | `folders` | – | Teilwelt für `folders@0.1` |
| `command-with-folders` | `commands`, `log`, `control`, `files`, `clock`, `folders` | `entry` | Command-Plugin mit einmaligem Dialog-Ordnerzugriff (`folders@0.1`); ohne `forms`/`storage`/`user-storage`/`design-state` |
| `importer-with-folders` | `importer-plugin` + `folders` | `importer` | Importer mit `folders@0.1` |
| `exporter-plugin` | `commands` (nur `read`), `log`, `control`, `clock` | `formats-provider` (`export-file`) | Dateiformat-Exporter (`formats@0.2`) |
| `panel-plugin` | `command-plugin` + `ui` | `entry`, `ui-provider` (`describe`, `on-event`, `on-enter`, `on-exit`) | Command-Plugin mit angedocktem Panel (`ui@0.1`) |
| `panel-dialog-plugin` | `panel-plugin` | `entry`, `ui-provider`, `dialog-provider` | Panel-Plugin mit dynamischem Dialog-Hook (`dialog@0.1`) |
| `dialog-plugin` | `commands`, `log`, `control`, `files`, `clock` | `dialog-provider` (`update-fields`) | Isolierte Dialog-Hook-Welt |
| `command-dialog-plugin` | `command-plugin` | `entry`, `dialog-provider` | Command-Plugin mit Dialog-Hook (`dialog@0.1`) |
| `importer-dialog-plugin` | `importer-plugin` | `importer`, `dialog-provider` | Importer mit Dialog-Hook / dateibewusstem Formular (`dialog@0.1`) |

### 1.2 `commands.run`, Panels und Listener

- **`commands.run`:** Die Funktion `run(command: string, args: json) -> result<json, plugin-error>` ruft dieselben JSON-Befehle wie MCP-Clients (`solidcraft-cli commands`) auf einer Scratch-Session auf `[Q8][Q12]`. Jeder `commands.run`-Aufruf ist an die exakt in `runtime.commands` gelisteten IDs gebunden; ein `read`-Entry darf weder `edit`-Befehle noch schreibende Host-Importe (`write-file`, `user-storage.set`, `user-storage.remove`) nutzen `[Q1][Q13]`. Ein fehlgeschlagener Aufruf rollt die gesamte Transaktion zurück; ein erfolgreicher Edit-Aufruf erzeugt genau einen Undo-Schritt `[Q12]`.
- **Panels (`ui` / `ui-provider`):** Ein Panel wird sowohl statisch in `runtime.ui` als auch in `ui-provider.describe()` deklariert (beide müssen übereinstimmen) `[Q1][Q14]`. Das Layout ist eine flache Knotenliste (`layout { root, nodes }`) ohne Rekursion `[Q8][Q14]`. Zur Laufzeit aktualisiert der Gast Zellen über `ui.set-data(panel, list<datum>)` mit Slash-Pfaden (z. B. `/jobs/0/tool`, Werte als `value`-Variante in mm und Grad), leert sie mit `ui.clear-data` und öffnet/schließt das Panel mit `ui.show-panel` `[Q1][Q8][Q14]`. Nutzeraktionen in Panel-Buttons oder Tabellen senden einen `ui-event` sowohl an `ui-provider.on-event` als auch als JSON-`params` an das jeweilige `entry` in `entry.execute`, sodass dieselbe Aktion auch über MCP ausführbar bleibt `[Q14][Q15]`.
- **Listener (`design.changed` / `design.links_changed`):** Listener haben kein eigenes WIT-Export-Interface; sie werden über `runtime.listeners` im Manifest (z. B. `[{"entry": "refresh", "on": ["design.changed"]}]`) zusammen mit `"design@0.1"` deklariert und rufen einen normalen `read`-Entry über `entry.execute` auf `[Q16][Q17]`. Der Host liefert gedrosselte Gesamtdokument-Invalidierungen (ca. 10/s) nach abgeschlossenen Edits, Undo/Redo, Öffnen, Schließen und Tab-Wechseln auf einem Command-Worker mit engem Budget (max. `1_000_000` Fuel, `16 MiB` RAM, `512 KiB` Stack, `100 ms` Laufzeit) `[Q16][Q17]`. Zusätzlich liefert `design-state.get-token()` ein opakes `{document_id, revision}`-Token, mit dem `expected_design` veraltete Schreibzugriffe (`stale_revision`) abweist `[Q16][Q17]`. **Aktuelle Einschränkung in `v0.50.0`:** Ein `design.changed`-Handler läuft auf einer Scratch-Kopie und kann sein angedocktes Panel noch nicht direkt mit `ui.set-data` aktualisieren; als Übergangslösung dient ein Refresh-Button im Panel `[Q16]`.

### 1.3 Unterschiede `v0.45.0` gegen `v0.50.0`: nur Ergänzungen oder Brüche?

Der Vergleich von `crates/craft-plugin/wit/plugin.wit` über `v0.45.0`, `v0.48.0` und `v0.50.0` zeigt:

- **Keine Breaking Changes zwischen `v0.45.0` und `v0.50.0`:** Schon `v0.45.0` trug die Paketkennung `craft:plugin@0.2.0` (der Bruch von `0.1.0` zu `0.2.0` durch `plugin-error.unsupported` lag bereits vor `v0.45.0`; `0.1.0` wird über `wit-0.1` weiterhin parallel unterstützt) `[Q8][Q9][Q18]`.
- **Reine Ergänzungen (`v0.45.0` → `v0.48.0`):** Hinzu kamen `types.value` / `datum` / `color-role`, `forms` (`forms@0.1`), `design-state` (`design@0.1`), `storage` (`storage@0.1` zusätzlich zu den `storage.*`-Befehlen), `formats-provider` + `exporter-plugin`, `ui` + `ui-provider` + `panel-plugin` (`ui@0.1`) sowie `dialog-provider` + `dialog-plugin` / `command-dialog-plugin` (`dialog@0.1`) `[Q8][Q14][Q18][Q19]`.
- **Reine Ergänzungen (`v0.48.0` → `v0.50.0`):** Hinzu kamen `user-storage` (`user-storage@0.1`) samt `importer-plugin-with-storage`, `folders` (`folders@0.1`) samt `folder-reader`, `command-with-folders` und `importer-with-folders`, `panel-dialog-plugin`, `importer-dialog-plugin` sowie `panel-plugin` umgestellt auf `include command-plugin` `[Q8][Q19]`.
- **Rückwärtskompatibilität bestehender Komponenten:** Der Host erkennt die WIT-Version anhand der Importe/Exporte der Komponente, und neue Importe in `command-plugin` (`forms`, `user-storage`, `design-state`, `storage`) sind additiv – ältere Komponenten ohne diese Importe linken und laufen unverändert weiter `[Q8][Q16][Q20]`. Wichtig für `v0.45.0`-Ziele: Neue Top-Level-Manifestfelder ab `v0.45.0` (`min_host_version`, `optional_capabilities`, `extensions`) bzw. spätere Features (`ribbon_groups`, `updates`, `ui`, `user-storage`, `folders`) werden von Hosts vor deren Einführung als unbekannte Felder/Capabilities abgewiesen; für Abwärtskompatibilität muss `min_host_version` passend gewählt werden `[Q16]`.

#### Quellenbelege zu Abschnitt 1

* **[Q1] SolidCraft `docs/book/src/dev/plugins.md` – Aufbau, Build und Manifest**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/book/src/dev/plugins.md
  * **Zitat:** „A plugin is a folder (shipped as a `.zip`) holding a manifest, `plugin.json`, and one WebAssembly“
  * **Zitat:** „A plugin has no network access, ever. It reads and writes files only in folders the user approved,“

* **[Q2] SolidCraft `docs/plugins.md` – `inspect.classify_points` für Read-Entries**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/plugins.md
  * **Zitat:** „A plugin entry with `"effect": "read"` can call `inspect.classify_points` through“

* **[Q3] SolidCraft `docs/plugin-runtime.md` – `model.mesh` als Read-only-Eingabe**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/plugin-runtime.md
  * **Zitat:** „`model.mesh {body, tolerance?}` is a general read-only input boundary. Tolerance is a finite positive“

* **[Q4] SolidCraft `docs/plugins.md` – Ribbon-Tabs**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/plugins.md
  * **Zitat:** „The Design tab names are Model, Surface, Assemble, Insert, Inspect, Manage, View, Sketch,“

* **[Q5] SolidCraft `docs/book/plugin-examples/plate-maker/plugin.json`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/book/plugin-examples/plate-maker/plugin.json
  * **Zitat:** „Adds a square plate.“

* **[Q6] SolidCraft `crates/mcp/src/plugin_tools.rs` – MCP-Werkzeuge**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/mcp/src/plugin_tools.rs
  * **Zitat:** „//! Installed plugins as tools (RFC 0002 section 6c). Every installed, enabled plugin's entries are“

* **[Q7] SolidCraft PR #18741 – Plugins als MCP-Werkzeuge**
  * **URL:** https://github.com/tangency-labs/solidcraft/pull/18741
  * **Zitat:** „Installed plugins become tools that the in-app assistant and MCP clients can list and call by name,“

* **[Q8] SolidCraft `crates/craft-plugin/wit/plugin.wit`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/craft-plugin/wit/plugin.wit
  * **Zitat:** „App commands and their schemas are data; this world never names app types.“
  * **Zitat:** „The app's command surface: the same commands, inputs and results its MCP clients get.“
  * **Zitat:** „Additive forms@0.1 capability. Existing command components need not import this.“

* **[Q9] SolidCraft `crates/craft-plugin/wit-0.1/plugin.wit`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/craft-plugin/wit-0.1/plugin.wit
  * **Zitat:** „craft:plugin@0.1.0 as SolidCraft 0.44 shipped it, kept unchanged so plugins built against it“

* **[Q10] SolidCraft `crates/craft-plugin/wit-host/plugin.wit`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/craft-plugin/wit-host/plugin.wit
  * **Zitat:** „Read-only negotiation, independent of the command/importer API version. Existing worlds“

* **[Q11] SolidCraft `docs/plugins.md` – Capability-Abfrage `craft:host`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/plugins.md
  * **Zitat:** „The small read-only query is a separate additive WIT package, `craft:host@0.1.0`“

* **[Q12] SolidCraft `docs/plugins.md` – `PluginHost`, Transaktion und Undo**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/plugins.md
  * **Zitat:** „One successful plugin call is one undo step; a failed guest call rolls back the transaction.“

* **[Q13] SolidCraft `crates/craft-plugin/src/lib.rs` – Read-Entry-Schutz**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/craft-plugin/src/lib.rs
  * **Zitat:** „The host imports that change something outside the design. A `read` entry is refused every“

* **[Q14] SolidCraft `docs/plugins.md` – Docked Panels**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/plugins.md
  * **Zitat:** „The component's `ui-provider.describe` must return those declarations.“
  * **Zitat:** „The host owns the controls, theme, docking and plugin badge; plugins ship data and layouts.“

* **[Q15] SolidCraft PR #19516 – Angedockte Panels**
  * **URL:** https://github.com/tangency-labs/solidcraft/pull/19516
  * **Zitat:** „Row and button actions call the plugin's ordinary namespaced entries on the command worker, so the same action works over MCP.“

* **[Q16] SolidCraft `docs/plugins.md` – Listener, Versionen und Grenzen**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/plugins.md
  * **Zitat:** „A handler cannot refresh its plugin's docked panel yet. It runs on a scratch copy of the“
  * **Zitat:** „Existing manifests need no changes. Releases before 0.45.0 cannot understand these new top-level“

* **[Q17] SolidCraft PR #19894 – Revisionstoken und `design.changed`-Listener**
  * **URL:** https://github.com/tangency-labs/solidcraft/pull/19894
  * **Zitat:** „A plugin that declares them gets one notification after a finished change, after undo and redo, and when the active document“

* **[Q18] SolidCraft `crates/craft-plugin/wit/plugin.wit` (älterer Release-Tag)**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.45.0/crates/craft-plugin/wit/plugin.wit
  * **Zitat:** „// - `commands@0.2`: types, commands, log, control, files, clock and entry (world `command-plugin`);“

* **[Q19] SolidCraft `crates/craft-plugin/wit/plugin.wit` (Zwischenstand-Tag)**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.48.0/crates/craft-plugin/wit/plugin.wit
  * **Zitat:** „file-format slots (RFC 0015 §4). An import slot is world `importer-plugin`“

* **[Q20] SolidCraft `docs/plugins.md` – Rückwärtskompatibilität**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/plugins.md
  * **Zitat:** „Existing plugins need no new imports or capabilities.“

---

## 2. Manifest und Einträge (Ribbon, Formular, MCP-Werkzeug)

### 2.1 Aufbau von `plugin.json`

Ein ausführbares Manifest enthält folgende Top-Level-Felder (`plugin.json`-Größenlimit: in `docs/book/src/dev/plugins.md` und `crates/engine/src/plugin/check.rs` noch mit `16 KiB` dokumentiert, im Code `crates/craft-plugin/src/lib.rs` `MAX_MANIFEST_BYTES` und `docs/plugins.md` auf `64 KiB` angehoben `[Q1][Q13][Q21][Q22]`):

- `id`: 1–64 Kleinbuchstaben, Ziffern und Bindestriche (kein führender/schließender Bindestrich); der Paketordner trägt genau diese ID `[Q1][Q21]`.
- `name` (max. 80 Zeichen), `version` (max. 32 Zeichen), `description` (optional, max. 240 Zeichen) `[Q1][Q21]`.
- `capabilities` (Pflichtliste benötigter Interfaces, z. B. `["commands@0.2"]`), optional `min_host_version` (ab 0.45.0, strenges Semver), `optional_capabilities` (ab 0.45.0), `extensions` (ab 0.45.0, frei für Metadaten), `updates` (`{"github": "owner/repo"}`, ab 0.49.0), `$defs` (geteilte Felddefinitionen) `[Q1][Q16][Q21][Q23]`.
- `runtime`:
  - `module`: Kleinbuchstaben-Dateiname einer `.wasm`-Datei neben `plugin.json` (keine Unterordner) `[Q1][Q24]`.
  - `commands`: exakte ID-Liste aller aufrufbaren SolidCraft-Befehle (max. 128, keine Wildcards) `[Q24]`.
  - `entries`: 1–32 Einträge gleicher Art (`command`, `importer` oder `exporter`), jeweils mit `name`, `effect` (`"read"` oder `"edit"` bei Commands), `input_schema` (JSON Schema eines `object`) und optional `slots` `[Q1][Q21][Q24]`.
  - `limits`: `fuel`, `memory_mib`, `deadline_ms`, optional `stack_kib` (bei Weglassen: Defaults 10 Mio. Fuel, 64 MiB, 5000 ms) `[Q1][Q24]`.
  - `permissions`: optional `command_groups`, `files`, `clock`, `input_folder` (nur Importer); `net` wird abgelehnt `[Q1][Q24]`.
  - optional: `ribbon_groups`, `ui`, `listeners`, `data_format` `[Q1][Q21][Q23]`.

### 2.2 Platzierung im Ribbon und in Menüs

- Jeder installierte, aktivierte Eintrag erscheint automatisch in der **Plugins**-Gruppe des **Model**-Tabs sowie im **Plugins**-Menü `[Q21]`.
- Über `slots` auf dem Entry steuert das Manifest die zusätzliche Einordnung `[Q21]`:
  - `{"kind": "ribbon", "name": "Inspect"}` (Groß-/Kleinschreibung egal; gültige Design-Tabs: `Model`, `Surface`, `Assemble`, `Insert`, `Inspect`, `Manage`, `View`, `Sketch`, `Sheet Metal`, `Weldments`): erzeugt im jeweiligen Tab eine eigene Gruppe mit dem Plugin-Namen und Plugin-Badge `[Q4][Q21]`.
  - Jeder andere `ribbon`-Name landet im eigenen Tab **Plugins** (mit je einer Gruppe pro Plugin) `[Q21]`.
  - `{"kind": "menu", "name": "File"}` oder `"Help"` erzeugt Einträge im File- bzw. Help-Menü; andere Menünamen werden ignoriert (Eintrag bleibt im Plugins-Menü) `[Q21]`.
- Mehrere Entries lassen sich über `runtime.ribbon_groups` (max. 32 Gruppen mit `label`, optional `icon`-SVG und 1–32 lokalen Entry-Namen) im Model-Tab hinter einem gemeinsamen Dropdown-Button bündeln `[Q21]`.

### 2.3 Formular (Dialog aus `input_schema`)

Plugins liefern keinen eigenen UI-Code; SolidCraft zeichnet den Dialog automatisch aus dem `input_schema` jedes Entrys `[Q1]`. Öffnen des Dialogs führt keinen Plugin-Code aus `[Q21]`:

- **Standardfelder:** `number`, `integer`, `string`, `boolean`, `unit` (z. B. `"mm"`), `default`, `minimum`/`maximum`, `enum` oder `oneOf` (`{"const": ..., "title": ...}` für lesbare Dropdown-Labels) `[Q1][Q21]`.
- **Layout- & Hilfs-Annotationen:** `x-solidcraft-field-order: "declared"` (sonst Required-first, dann alphabetisch), `x-solidcraft-section`, `x-solidcraft-sections: "collapsible"`, `x-solidcraft-unit-from`, `x-solidcraft-help` (HTTPS-Link), `x-solidcraft-font: true` `[Q21]`.
- **Geometrie-Auswahl (`x-solidcraft-selection`):** `{"version": 1, "accept": ["body", "face", "edge", "profile", "sketch_point", "sketch_curve"]}` mit `minItems`/`maxItems`; der Host übernimmt beim Öffnen die aktuelle Viewport-Auswahl ins erste Auswahlfeld und übergibt strukturierte Auswahlobjekte als JSON-Array an das Plugin `[Q21]`.
- **Icons & Bilder:** `x-solidcraft-icon` (SVG im eingeschränkten SolidCraft-Icon-Subset, 64×64 ViewBox, Theme-Farbrollen, max. 64 KiB), `x-solidcraft-swatch` (PNG/JPEG bis 64 KiB / 256×256 px) und `x-solidcraft-image` (PNG/JPEG bis 512 KiB / 1024×1024 px) `[Q21]`.
- **Bedingte Felder & dynamische Hooks:** Deklarative Sichtbarkeit/Verfügbarkeit/Defaults über `x-solidcraft-visible-when`, `x-solidcraft-enabled-when`, `x-solidcraft-when`, `x-solidcraft-defaults` (laufen ohne WASM sowohl im Dialog als auch bei Agenten/CLI), optional ergänzt durch `dialog@0.1` (`dialog_hook: true` mit `dialog-provider.update-fields`, max. 10 Mio. Fuel, 16 MiB, 250 ms) `[Q21]`.
- **Live-Vorschau:** Bei `edit`-Entries (ohne `"job": true`) aktiv, läuft auf einer verworfenen Scratch-Session ohne Datei-/Command-Group-Rechte `[Q21]`.

### 2.4 Abbildung als MCP-Werkzeug (Namen, Schema, Prüfung)

Bei jedem `tools/list` fragt der MCP-Server `plugin.tools` beim Backend ab und hängt alle Entries aktivierter Plugins an die eingebauten Werkzeuge an `[Q6][Q25]`:

- **Werkzeugname:** `<plugin>.<entry>` (eingebaute MCP-Tools enthalten nie einen Punkt) `[Q6]`.
- **Parameterschema & Prüfung:**
  - Bei **Command-Entries** ist `input_schema` direkt das Argument-Schema des MCP-Tools `[Q6][Q26]`.
  - Bei **Importer-/Exporter-Entries** generiert `plugin.tools` ein Schema mit `path` und `options` (aus `input_schema`) und Titel `"Open .ext files with <Plugin name>"` bzw. `"Export .ext files with <Plugin name>"`; Aufrufe werden intern an `file.import` bzw. `file.export` delegiert `[Q6][Q26]`.
  - Vor jedem Plugin-Aufruf validiert `craft_plugin::check_input` streng gegen das deklarierte Schema (Typen, `required`, Bereiche, `additionalProperties: false` sofern nicht explizit erlaubt; ausgeblendete bedingte Felder werden vor dem Aufruf entfernt) `[Q6][Q7][Q21]`.
- **Beschreibung & Kennzeichnung:** Jede Tool-Definition trägt das Metadatenobjekt `plugin: {id, name, version, entry, kind, effect}`; die Plugin-eigene Beschreibung wird durch `<plugin-text>`-Marker (als reiner Text, nicht als Handlungsanweisung) gekapselt `[Q6]`.
- **Ausführung:** Ein MCP-Aufruf öffnet keine Dialoge, läuft mit den bei Installation erteilten Rechten als ein Undo-Schritt und liefert fehlende Rechte oder Read-Entry-Verstöße als Text und maschinenlesbar in `structuredContent.plugin_error` zurück `[Q6][Q21][Q26]`. Für revisionsgesicherte Edits (`expected_design`) kann über `execute` direkt `<plugin>.<entry>` mit `{approval, params, expected_design}` aufgerufen werden `[Q16][Q25]`.

#### Quellenbelege zu Abschnitt 2

* **[Q21] SolidCraft `docs/plugins.md` – Menü, Ribbon, Dialoge und MCP-Verhalten**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/plugins.md
  * **Zitat:** „The **Plugins** group on the Model tab lists every installed plugin entry, including entries without“
  * **Zitat:** „MCP tool arguments are checked against the entry's declared schema:“

* **[Q22] SolidCraft `crates/engine/src/plugin/check.rs` – Manifest-Größenhinweis**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/engine/src/plugin/check.rs
  * **Zitat:** „Keep plugin.json under 16 KiB: move long text into a README in the package.“

* **[Q23] SolidCraft `docs/plugins.md` – Updates, `$defs`, Manifest-Obergrenze**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/plugins.md
  * **Zitat:** „64 MiB. The manifest has a separate 64 KiB cap. Before publication, the host checks“

* **[Q24] SolidCraft `docs/plugin-runtime.md` – Runtime-Manifestfelder**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/plugin-runtime.md
  * **Zitat:** „Every command in the MCP catalog is reachable: the same ids, input schemas, results and read/edit“
  * **Zitat:** „A package lists the exact ids it calls; there are no wildcards or aliases.“

* **[Q25] SolidCraft `docs/mcp.md` – Plugin-Tools im MCP-Server**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/mcp.md
  * **Zitat:** „After the built-in tools, `tools/list` lists every installed, enabled plugin's“

* **[Q26] SolidCraft `crates/engine/src/plugin/tools.rs` – Schema-Aufbau und Ablehnungen**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/engine/src/plugin/tools.rs
  * **Zitat:** „Installed plugins as tools for agents (RFC 0002 section 6c): every enabled plugin's entries,“

---

## 3. Bauen (Toolchain, Versionen, Kommandos, Ergebnisgröße)

### 3.1 Toolchain und Versionen

- **Rust & Target:** SolidCraft `v0.50.0` nutzt laut `rust-toolchain.toml` Rust `1.99.1` mit Target `wasm32-unknown-unknown` `[Q27]`. Plugins **müssen** für `wasm32-unknown-unknown` (nicht `wasm32-wasip1` oder `wasip2`) gebaut werden, da SolidCraft kein WASI linkt und Komponenten mit `wasi:*`-Importen ablehnt `[Q1][Q22]`.
- **Crate-Konfiguration (`docs/book/plugin-examples/*/Cargo.toml`):**
  - `edition = "2024"`, eigener `[workspace]`-Block (vom SolidCraft-Workspace getrennt), `[lib] crate-type = ["cdylib"]`, Release-Profil `opt-level = "s"`, `lto = true`, `strip = true` `[Q28]`.
  - Abhängigkeiten in den Beispiel-Lockfiles (`v0.50.0`): `wit-bindgen = "0.63"` (`0.63.0` im Lockfile) und `serde_json = "1"` (`1.0.154` im Lockfile) `[Q28][Q29]`.
- **Komponenten-Wrapper (`wasm-tools` statt `cargo-component`):** SolidCraft dokumentiert und nutzt ausdrücklich `wasm-tools component new` (nicht `cargo-component`), um das von `cargo build` erzeugte Core-WASM-Modul anhand der eingebetteten `wit-bindgen`-Metadaten in eine WebAssembly-Komponente zu verpacken `[Q1][Q30]`. Eine konkrete Mindest- oder Zielversion der `wasm-tools`-CLI steht in den geprüften SolidCraft-Dateien **nicht** (**nicht gefunden** in `docs/book/src/dev/plugins.md`, `Cargo.toml` und `.github/workflows/ci.yml`).
- **Host-Wasmtime-Version in `v0.50.0`:** `wasmtime = "48.0.8"` (mit Winch als schnellem Baseline-Compiler beim ersten Lauf und Cranelift im Hintergrund samt Disk-Cache) `[Q16][Q31]`.

### 3.2 Build-Kommandos

```sh
rustup target add wasm32-unknown-unknown
cargo install wasm-tools

# Im Crate-Ordner (z. B. plate-maker-src/, mit wit/plugin.wit aus SolidCraft)
cargo build --release --target wasm32-unknown-unknown
wasm-tools component new \
  target/wasm32-unknown-unknown/release/plate_maker_src.wasm \
  -o ../plate-maker/plate-maker.wasm
```
(Vorbild: Schritt 5 des offiziellen Plugin-Leitfadens `[Q1]`; zusätzlich empfiehlt `crates/engine/src/plugin/check.rs` bei Größenproblemen `wasm-tools strip` `[Q22]`.)

### 3.3 Größe der Ergebnisdatei

- **Gemessene Größe der drei Beispiel-Plugins (`plate-maker.wasm`, `box-importer.wasm`, `job-list.wasm`):** **nicht gefunden** – die gebauten `.wasm`-Dateien sind in `docs/book/plugin-examples/` über `.gitignore` ausgeschlossen und werden in der Dokumentation nicht beziffert.
- **Gemessener Referenzwert & Host-Obergrenzen:** RFC 0002 nennt für einen realen CAD-Konverter eine Komponentengröße von `28 MB` (auf Größe optimiert) bis `42 MB` `[Q32]`. Der Host begrenzt die Komponente für Command-Plugins auf `16 MiB` (`MAX_COMPONENT_BYTES`), für Importer und Exporter auf `64 MiB` (`MAX_IMPORTER_COMPONENT_BYTES`) und das gesamte `.zip`-Archiv auf `80 MiB` (`MAX_ZIP_BYTES`, max. 256 Einträge, max. 1024 Dateien/Ordner entpackt) `[Q1][Q13][Q33]`.

#### Quellenbelege zu Abschnitt 3

* **[Q27] SolidCraft `rust-toolchain.toml`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/rust-toolchain.toml
  * **Zitat:** „# (dtolnay/rust-toolchain@1.99.1); change them together. Cargo.toml's rust-version stays the“

* **[Q28] SolidCraft `docs/book/plugin-examples/plate-maker-src/Cargo.toml`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/book/plugin-examples/plate-maker-src/Cargo.toml
  * **Zitat:** „# A crate of its own, not part of the SolidCraft workspace around it.“

* **[Q29] SolidCraft `docs/book/plugin-examples/plate-maker-src/Cargo.lock`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/book/plugin-examples/plate-maker-src/Cargo.lock
  * **Zitat:** „# It is not intended for manual editing.“

* **[Q30] SolidCraft `xtask/src/plugin_examples.rs` – `wasm-tools` / `wit_component`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/xtask/src/plugin_examples.rs
  * **Zitat:** „/// The module as a component: what `wasm-tools component new` does, from the type information“

* **[Q31] SolidCraft `crates/craft-plugin-wasm/Cargo.toml` – Wasmtime-Version**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/craft-plugin-wasm/Cargo.toml
  * **Zitat:** „description = "App-independent WebAssembly component runtime for Craft plugins"“

* **[Q32] SolidCraft `docs/rfcs/0002-plugins.md` – Größe eines realen Konverters**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/rfcs/0002-plugins.md
  * **Zitat:** „A real converter measured 28 MB (built for size) to 42 MB. Compiling happens in the app's process with no sandbox limit on the compiler,“

* **[Q33] SolidCraft `crates/engine/src/plugin/install.rs` – Archivgrenzen**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/engine/src/plugin/install.rs
  * **Zitat:** „/// The largest `.zip` read, and the most it may unpack to: room for an importer's component (up“

---

## 4. Installieren und Rechte (Ordner, CLI-Befehle, Rechte, MCP-Sperre)

### 4.1 Ordner auf dem System

| Zweck | Linux | macOS | Windows |
|---|---|---|---|
| Installierte Plugins | `$XDG_DATA_HOME/solidcraft/plugins` (Standard `~/.local/share/solidcraft/plugins`) | `~/Library/Application Support/SolidCraft/plugins` | `%LOCALAPPDATA%\SolidCraft\plugins` |
| Gespeicherte Freigaben (Grant Store) | `<plugins-dir>/.grants/<plugin-id>.json` | `<plugins-dir>/.grants/<plugin-id>.json` | `<plugins-dir>/.grants/<plugin-id>.json` |
| Nutzer-Einstellungen (`user-storage@0.1`) | `$XDG_DATA_HOME/solidcraft/plugin-user-data/<id>.json` | `~/Library/Application Support/SolidCraft/plugin-user-data/<id>.json` | `%APPDATA%/SolidCraft/data/plugin-user-data/<id>.json` |
| Wasmtime-Kompilierungs-Cache | `~/.cache/solidcraft/plugin-compile` | `~/Library/Caches/SolidCraft/plugin-compile` | `%LOCALAPPDATA%\SolidCraft\plugin-compile` |

- `SOLIDCRAFT_SETTINGS_DIR` lenkt den Einstellungsordner um; `--plugins-dir DIR` lenkt bei lokalen CLI- und `mcp --headless`-Aufrufen den Plugin-Ordner um; `--keep-plugin-approvals` speichert/liest die Freigaben dauerhaft in `.grants` gemeinsam mit der Desktop-App `[Q16][Q34]`.
- Manuell in den `plugins`-Ordner kopierte Plugins erhalten **keine** Freigaben; Installationen aus einer `.zip` entpacken atomar über einen versteckten `.install-...`-Ordner nach `plugins/<id>/`, ohne dass die Desktop-App neu gestartet werden muss `[Q16]`.

### 4.2 CLI- und Management-Befehle

Die eigene Unterbefehlsgruppe `solidcraft-cli plugin` bietet genau zwei Autoren-Kommandos `[Q35][Q36]`:

- `solidcraft-cli plugin check <folder|plugin.zip> [--json]`
- `solidcraft-cli plugin test <folder|plugin.zip> [--json] [--out DIR] [--require-cases]`

Für Installation, Auflistung, Freigaben und Entfernung in lokalen Läufen nutzt man die Engine-Kommandos über `solidcraft-cli exec` (bzw. in der Desktop-App unter **Preferences › Plugins**): `plugin.install` (`dry_run: true` für Vorabprüfung mit `approval`- und `archive`-Hashes, `approve` für Rechte/Limits, `replace: true` für Updates), `plugin.inspect`, `plugin.list`, `plugin.grants`, `plugin.revoke` (nimmt Freigaben zurück, behält Paket), `plugin.remove` (`remove_user_data?: bool`), `plugin.tools`, `plugin.run` `[Q16][Q34][Q37]`.

### 4.3 Rechte (Netz, Dateien, Command-Groups, Clock)

- **Netz (`net`):** Kategorisch verboten. `runtime.permissions.net` führt bereits bei `plugin check` und `plugin.install` zu einem Fehler, der Linker bindet weder Sockets noch HTTP/Fetch, und WASI-Netzwerkimporte werden abgelehnt `[Q1][Q22]`.
- **Dateien (`files` / `folders` / `input_folder`):**
  - `runtime.permissions.files`: benannte Ordner (`{"name": "exports", "read": true, "write": true}`), die der Nutzer bei Installation auswählt. Zugriff erfolgt im WIT über `files.read-file`/`write-file` oder in `file`/`doc`-Befehlen über `grant:<name>/<relpath>`. Schreibzugriffe werden gestaged und erst nach erfolgreichem Commit publiziert; ein `read`-Entry darf `write-file` nie aufrufen `[Q1][Q13][Q24]`.
  - `folders@0.1`: Einmaliges Leserecht für ein mit `"format": "directory"` und `"x-solidcraft-grant": "read"` markiertes Dialogfeld (nur in dieser einen interaktiven Ausführung gültig; wird nicht gespeichert) `[Q21]`.
  - `input_folder` (nur Importer): erlaubt `source.read`/`size`/`resolve` auf Geschwisterdateien im Ordner der geöffneten Datei (z. B. Baugruppen) `[Q1]`.
  - Symlinks, `..` und versteckte Dateien innerhalb gewährter Ordner werden abgelehnt `[Q16][Q38]`.
- **Command-Groups (`command_groups`):** Befehle, die über das geöffnete Design hinausreichen, erfordern die passende Gruppe (`file`, `doc`, `app`, `plugin`) sowohl in `runtime.permissions.command_groups` als auch als Nutzerfreigabe `[Q1][Q24]`.
- **Clock:** Ohne `"clock": true` liefert `clock.now()` eine feste Epoche (0) `[Q1]`.

### 4.4 Warum ein Agent aus MCP kein Plugin installieren (oder Freigaben verändern) darf

1. **Standard-`PathScope` des MCP-Servers schließt den Plugin-Ordner aus:** `solidcraft-cli mcp` setzt standardmäßig eine enge Pfad-Beschränkung (`PathScope`), die nur den Ordner des offenen Designs, den Recovery-Ordner, den temporären Scratch-Ordner und explizit per `--allow-path` übergebene Verzeichnisse freischaltet – **nicht** SolidCrafts Per-User-`plugins`-Ordner (sofern der Nutzer den Server nicht ausdrücklich mit `--allow-any-path` startet) `[Q25][Q39]`. In `crates/engine/src/cmd/plugin.rs` erzwingt `plugin.install` vor dem Schreiben ins Zielverzeichnis `solidcraft_io::vfs::check_new(&folder)`, und Tests in `crates/engine/src/plugin/tests.rs` belegen explizit, dass selbst bei angegebenem `approve`-Objekt ein `plugin.install` oder `plugin.remove` ohne passende Caller-`PathScope`-Freigabe auf den `plugins`-Ordner abgewiesen wird (`"folder approval retains caller scope"`) `[Q37][Q40]`.
2. **Kein Zugriff auf Plugin-Rechte über MCP-`preferences`:** Das MCP-Tool `preferences` akzeptiert ausschließlich harmlose Anzeige- und Einheiten-Einstellungen und verweigert jeden anderen Schlüssel, damit ein KI-Client weder Plugin-Rechte noch Dateilimits oder Dateipfade verändern kann `[Q25][Q41]`.
3. **Strikte Freigabepflicht im In-App-Assistenten (`agent_chat`):** Im internen Assistenten-Gate sind `app.*`, `prefs.*`, `ui.prefs` und `engine.script` grundsätzlich blockiert; jeder Aufruf von externem Plugin-Code (`plugin.run`, `<plugin>.<entry>` oder ein Importer) erfordert ungeachtet des Berechtigungsmodus und von „Always allow“ immer eine explizite Bestätigung durch den Menschen (**Allow**/**Deny**) `[Q42][Q43]`. Hinweis: Ein isoliertes Befehlsnamens-Verbot allein für `"plugin.install"` in `crates/mcp/src/tools.rs` oder `agent_chat/gate.rs` wurde **nicht gefunden** – die Sperre im Standard-MCP-Betrieb greift über den `PathScope` und die `preferences`-Whitelisting-Regel `[Q37][Q40][Q41]`.

#### Quellenbelege zu Abschnitt 4

* **[Q34] SolidCraft `apps/solidcraft-cli/src/main.rs` – CLI-Flags für Plugin-Ordner und Approvals**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/apps/solidcraft-cli/src/main.rs
  * **Zitat:** „--plugins-dir DIR, with local commands: the folder plugin.install installs to and importers are found in;“
  * **Zitat:** „--keep-plugin-approvals, with local commands: keep plugin approvals between runs, in the plugins folder's grant“

* **[Q35] SolidCraft `apps/solidcraft-cli/src/plugin.rs` – `plugin check` und `plugin test`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/apps/solidcraft-cli/src/plugin.rs
  * **Zitat:** „`check` runs the app's `plugin.check`: what Install and a call would refuse, each with its fix.“

* **[Q36] SolidCraft `apps/solidcraft-cli/tests/plugin_tools.rs` – CLI-Unterbefehle**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/apps/solidcraft-cli/tests/plugin_tools.rs
  * **Zitat:** „`plugin check` and `plugin test` on packages made from the repository's original plugin“

* **[Q37] SolidCraft `crates/engine/src/cmd/plugin.rs` – `PathScope`-Prüfung bei `plugin.install`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/engine/src/cmd/plugin.rs
  * **Zitat:** „// The plugins folder is the app's own, but a scoped caller must have been given it.“

* **[Q38] SolidCraft `crates/craft-plugin-wasm/src/native.rs` – Symlink-Verbot**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/craft-plugin-wasm/src/native.rs
  * **Zitat:** „/// Refuses `path` inside a granted folder when any part of it is a symbolic link (or, on Windows,“

* **[Q39] SolidCraft `crates/mcp/src/server.rs` – Standard-`PathScope` des MCP-Servers**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/mcp/src/server.rs
  * **Zitat:** „/// always sets one unless started with `--allow-any-path` (docs/mcp.md).“

* **[Q40] SolidCraft `crates/engine/src/plugin/tests.rs` – `PathScope`-Test für `plugin.install`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/engine/src/plugin/tests.rs
  * **Zitat:** „folder approval retains caller scope“

* **[Q41] SolidCraft `docs/mcp.md` – Sperre von Plugin-Zugriff über `preferences`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/mcp.md
  * **Zitat:** „`preferences` refuses every other key before changing any settings, so an AI client cannot change plugin access, graphics, file limits, signing or file paths, or use the interactive `open`, `button` and `stand_up` actions.“

* **[Q42] SolidCraft `crates/ui-egui/src/agent_chat/gate.rs` – Assistenten-Gate**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/ui-egui/src/agent_chat/gate.rs
  * **Zitat:** „// External executable code always needs a user decision; the digest is not consent by itself.“

* **[Q43] SolidCraft `docs/agent-chat.md` – Bestätigung bei Plugin-Tools**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/agent-chat.md
  * **Zitat:** „**Deny**, in every mode and after **Always allow**: running a plugin's code needs your go each“

---

## 5. Testen und CI-Prüfung

### 5.1 Headless prüfen mit `solidcraft-cli`

1. **Statische Prüfung (`plugin check`):**
   ```sh
   solidcraft-cli plugin check plate-maker          # oder plate-maker.zip
   solidcraft-cli plugin check plate-maker --json   # maschinenlesbare Ausgabe
   ```
   Prüft ohne Ausführung von WASM-Code Manifest, Feldlängen, Größenlimits, Berechtigungen (`net`), Limits gegen die Host-Obergrenzen, Icons/Swatches, bedingte Felder sowie WIT-Welt und -Version; gibt je Problem `severity`, `field`, `problem` und `fix` zurück und endet bei Fehlern mit Exit-Code ungleich 0 `[Q1][Q16][Q35]`. Im Paketordner werden `tests/` und versteckte Dateien wie beim `.zip`-Bau ignoriert `[Q1]`.

2. **Funktions- und Integrationsprüfung (`plugin test`):**
   ```sh
   solidcraft-cli plugin test plate-maker --require-cases
   solidcraft-cli plugin test plate-maker --json --out ./test-out --require-cases
   ```
   Prüft zunächst wie `plugin check`, installiert das Paket mit dem echten Installer in ein temporäres Scratch-Plugin-Verzeichnis, richtet pro Testfall ein eigenes temporäres User-Settings-Verzeichnis ein und führt jeden Fall aus `tests/*.json` gegen `plugin.run`, `file.import` oder `file.export` mit realen Host-Limits aus `[Q1][Q16][Q35]`.
   - **Testfall-Felder (`tests/<name>.json`):** `entry`, `params`, `design` (optionales `.sc`-Design in `tests/`), `file` (für Importer), `grants` (Standard: alle im Manifest angeforderten Rechte; mit `"grants": {}` lassen sich Ablehnungen testen), `expect` (`error`, `message`, `reply`, `model` per `inspect.measure`, `files`, `tolerance`, Standard `1e-6`) `[Q1][Q35]`.
   - `--require-cases`: lässt auch Einträge ohne abdeckenden Testfall fehlschlagen (statt `skipped`), sodass die CI ungetestete Entries erkennt `[Q1][Q35]`.

### 5.2 Beispiele und Tests im SolidCraft-Repository

- **Lauffähige Buch-Beispiele (`docs/book/plugin-examples/`):**
  - `plate-maker` + `plate-maker-src`: Command-Plugin (`commands@0.2`, erzeugt per `solid.box` eine Platte, Slot `Model`-Ribbon) `[Q5][Q44]`.
  - `box-importer` + `box-importer-src`: Importer (`formats@0.2`, liest `.box`-Textdateien und schreibt ein SolidCraft-JSON-Design) `[Q1]`.
  - `job-list` + `job-list-src`: Panel-Plugin (`commands@0.2`, `ui@0.1`, `storage@0.1`, `panel-plugin`, verwaltet Jobs im Design und zeigt sie in einer angedockten Tabelle) `[Q45]`.
- **CLI-Integrationstests:** `apps/solidcraft-cli/tests/plugin_tools.rs` testet `plugin check`, `plugin test --json --out`, fehlendes `wasm-tools component new`, verbotene WASI- und `net`-Imports sowie `--require-cases` `[Q36]`.
- **Engine- und MCP-Tests:** `crates/engine/src/plugin/tests.rs` (mit WAT-Fixtures wie `fixture.wat`) und `crates/mcp/src/tests.rs` prüfen Sandbox, Fuel-/Memory-/Stack-/Deadline-Grenzen, Rollback, `PathScope`, `storage`/`user-storage`, `design.changed`-Listener und MCP-Tool-Listing/-Ausführung `[Q40][Q46]`.

### 5.3 CI-Hinweise in SolidCraft

- In `.github/workflows/ci.yml` aktiviert jede Änderung an `docs/book/plugin-examples/*`, `docs/book/src/dev/plugins.md`, `crates/craft-plugin/wit/**` oder `xtask/src/plugin_examples.rs` den `wasm`-Job mit Target `wasm32-unknown-unknown` und führt `cargo xtask plugin-examples` aus `[Q47][Q48]`.
- `xtask/src/plugin_examples.rs` stellt sicher, dass alle im Plugin-Guide gezeigten Code-Blöcke exakt den echten Beispiel-Dateien entsprechen, kopiert das aktuelle `crates/craft-plugin/wit/plugin.wit` in jedes Beispiel, baut alle drei Crates mit `cargo build --release --locked --target wasm32-unknown-unknown` und unterstützt mit `--run` auch das Verpacken über `wit_component::ComponentEncoder` samt anschließendem `solidcraft-cli plugin test --require-cases` `[Q30]`.

#### Quellenbelege zu Abschnitt 5

* **[Q44] SolidCraft `docs/book/plugin-examples/plate-maker-src/src/lib.rs`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/book/plugin-examples/plate-maker-src/src/lib.rs
  * **Zitat:** „// The same command, parameters and reply as `solidcraft-cli exec solid.box`.“

* **[Q45] SolidCraft `docs/book/plugin-examples/job-list-src/src/lib.rs`**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/book/plugin-examples/job-list-src/src/lib.rs
  * **Zitat:** „// The jobs live in the design: one undo step, saved with it.“

* **[Q46] SolidCraft `crates/mcp/src/tests.rs` – MCP-Plugin-Tool-Tests**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/mcp/src/tests.rs
  * **Zitat:** „/// own text marked as plugin text, called with strict arguments, refused with the missing grant“

* **[Q47] SolidCraft `.github/workflows/ci.yml` – CI-Lauf für Plugin-Beispiele**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/.github/workflows/ci.yml
  * **Zitat:** „# The plugin guide and its example crates count too: the wasm job builds the examples.“

* **[Q48] SolidCraft `xtask/src/ci.rs` – `plugin-examples`-Gate**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/xtask/src/ci.rs
  * **Zitat:** „/// - `plugin-examples`: ci.yml's `wasm` job, for the plugin guide and its examples.“

---

## 6. Grenzen und offene Fragen (je mit Fundstelle)

| Thema | Aktuelle Grenze / Status in `v0.50.0` | Fundstelle |
|---|---|---|
| **Kein Netzwerk** | Kein HTTP/Socket/Fetch im Linker, kein WASI; `"net"` im Manifest wird abgelehnt. Netz-Rechte sind erst für Phase 6 (signierter Index, vom Host ausgeführt) vorgesehen. | `[Q1]`, `[Q32]` |
| **Nur Engine-Befehle, keine Kernel-API** | Kein direkter B-Rep-/Kernel-Zugriff; Plugins nutzen nur die MCP-Befehlsfläche (`commands.run`). `model.mesh` ist auf 8.192 Vertices, 16.384 Dreiecke und 1 MiB JSON begrenzt. | `[Q8]`, `[Q24]`, `[Q49]` |
| **Keine parametrischen Plugin-Features** | `FeatureKind::Plugin` existiert in `v0.50.0` nicht; Plugins erzeugen einmalige Edits oder native Features in einem Undo-Schritt. | `[Q24]` |
| **Kein Zustand zwischen Aufrufen** | Jeder Aufruf startet eine frische WASM-Instanz (`Background plugins` in RFC 0002 §6d ist nur Spezifikation). | `[Q24]`, `[Q32]` |
| **Laufzeit- & Ressourcenlimits** | Max. 256 Host-Aufrufe pro Run (1.048.576 bei `"job": true`), Parameter/Antwort je max. 1 MiB JSON, Deadline max. 30 s (`600 s` bei `"job": true` / Importern), Stack max. 1 MiB (Command) bzw. 64 MiB (Importer/Exporter), RAM max. 4.096 MiB (Default-Ceiling 128 MiB), Fuel-Obergrenze `10_000_000_000_000` (Default-Ceiling `100_000_000_000`), Komponente max. 16 MiB (Command) / 64 MiB (Importer/Exporter). | `[Q1]`, `[Q13]`, `[Q16]`, `[Q24]` |
| **Plattform** | Ausführung nur nativ auf x86-64 und AArch64 mit `plugins`-Feature; im Web-Build fehlt der native Host. | `[Q24]` |
| **Daten einbetten (`storage@0.1`)** | Pro Plugin und Design max. 16 MiB `data.json` und max. 256 MiB Blobs (und 256 MiB Plugin-Daten gesamt pro Design). Designs mit Plugin-Daten lassen sich nicht als `.json` speichern. | `[Q16]`, `[Q24]` |
| **Daten einbetten (`user-storage@0.1`)** | Max. 128 Keys, 64 KiB kompaktes JSON gesamt, 1 MiB je `set`-Aufruf; keine Schreibzugriffe aus `read`-Entries oder Dialog-Hooks. | `[Q8]`, `[Q16]` |
| **Exporter & `needs_plugin_data`** | Exporter erhalten in `v0.50.0` noch keine Plugin-Daten (Ausgabe erfolgt mit Warnung); zudem darf ein Manifest nur Entries einer Art (`command`, `importer` oder `exporter`) enthalten. | `[Q16]` |
| **Panels (`ui@0.1`)** | Max. 8 Panels pro Plugin, 512 Widgets pro Layout, 1 MiB Panel-Daten, 100.000 Zeilen. `item-tree` und `chart` zeigen nur einen Platzhalter; `design.changed`-Listener können offene Panels noch nicht per `ui.set-data` aktualisieren. | `[Q16]` |
| **Workspaces, 3D-Overlays & dynamische Layouts** | In RFC 0015 (`workspaces`, `viewport`, `repeat`/`update-layout`) spezifiziert, in `crates/craft-plugin/wit/plugin.wit` (`v0.50.0`) jedoch noch nicht enthalten. | `[Q8]`, `[Q50]` |
| **Offene Fragen aus RFC 0002 & RFC 0015** | RFC 0002 §9: Wasmtime-Binärgröße/Compiler-Speicher, Signatur & kuratierter Index, Web-Laufzeit über `jco`, lokales Netz für Druck-Plugins, Result-Annotations. RFC 0015: Switcher-Platzierung für Workspaces, 10-Minuten-Joblimit, Zeitpunkt für `craft:plugin@1.0.0`. | `[Q32]`, `[Q50]` |

#### Quellenbelege zu Abschnitt 6

* **[Q49] SolidCraft `crates/engine/src/cmd/plugin.rs` – `model.mesh`-Grenzen**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/crates/engine/src/cmd/plugin.rs
  * **Zitat:** „evaluated component-local mesh, corners at the same point shared, at most 8192 vertices and 16384 triangles; no files or model changes“

* **[Q50] SolidCraft `docs/rfcs/0015-plugin-ui-workspaces.md` – Offene Fragen und Phasen**
  * **URL:** https://raw.githubusercontent.com/tangency-labs/solidcraft/v0.50.0/docs/rfcs/0015-plugin-ui-workspaces.md
  * **Zitat:** „Should plugin workspaces sit beside Design and Render in the switcher, or under a "More" list until the user pins them? Open.“

---

## 7. Bauanleitung: Minimalgerüst für U2 (Prüfregeln als Ribbon-Eintrag und MCP-Werkzeug)

### Ordnerstruktur

```text
mechvane-checks/
  plugin.json
  mechvane-checks.wasm
  tests/
    smoke.json
mechvane-checks-src/
  Cargo.toml
  wit/
    plugin.wit              # Kopie aus SolidCraft v0.50.0: crates/craft-plugin/wit/plugin.wit
  src/
    lib.rs
```

### `mechvane-checks/plugin.json`

```json
{
  "id": "mechvane-checks",
  "name": "Mechvane Design Checks",
  "version": "0.1.0",
  "min_host_version": "0.50.0",
  "description": "Checks open SolidCraft designs against Mechvane engineering rules.",
  "capabilities": ["commands@0.2"],
  "runtime": {
    "module": "mechvane-checks.wasm",
    "commands": ["document.inspect", "inspect.measure", "model.faces", "model.edges"],
    "entries": [
      {
        "name": "check-design",
        "effect": "read",
        "input_schema": {
          "type": "object",
          "properties": {
            "process": {
              "type": "string",
              "title": "Process",
              "default": "cnc",
              "oneOf": [
                {"const": "cnc", "title": "CNC Milling"},
                {"const": "fdm", "title": "FDM 3D Printing"}
              ]
            }
          }
        },
        "slots": [
          {"kind": "ribbon", "name": "Inspect"}
        ]
      }
    ],
    "limits": {"fuel": 1000000000, "memory_mib": 32, "deadline_ms": 5000}
  }
}
```

### `mechvane-checks-src/Cargo.toml`

```toml
[package]
name = "mechvane-checks-src"
version = "0.1.0"
edition = "2024"

[workspace]

[dependencies]
serde_json = "1"
wit-bindgen = "0.63"

[lib]
crate-type = ["cdylib"]

[profile.release]
opt-level = "s"
lto = true
strip = true
```

### `mechvane-checks-src/src/lib.rs`

```rust
wit_bindgen::generate!({ path: "wit", world: "command-plugin" });

use craft::plugin::commands;
use craft::plugin::types::{FieldFailure, PluginError};
use exports::craft::plugin::entry::Guest;
use serde_json::{Value, json};

struct Plugin;

impl Guest for Plugin {
    fn execute(entry: String, params: String) -> Result<String, PluginError> {
        let params: Value = serde_json::from_str(&params).map_err(|e| invalid("params", e))?;
        match entry.as_str() {
            "check-design" => {
                let process = params["process"].as_str().unwrap_or("cnc");
                let measured: Value = serde_json::from_str(
                    &commands::run("inspect.measure", "{}")?,
                )
                .map_err(|e| invalid("measure", e))?;
                let body_count = measured["body_count"].as_u64().unwrap_or(0);
                Ok(json!({
                    "process": process,
                    "body_count": body_count,
                    "findings": []
                })
                .to_string())
            }
            _ => Err(invalid("entry", format!("no entry `{entry}`"))),
        }
    }
}

fn invalid(field: &str, reason: impl ToString) -> PluginError {
    PluginError::InvalidInput(FieldFailure {
        field: field.into(),
        reason: reason.to_string(),
    })
}

export!(Plugin);
```

### `mechvane-checks/tests/smoke.json`

```json
{
  "entry": "check-design",
  "params": {"process": "cnc"},
  "expect": {
    "reply": {"result": {"process": "cnc", "body_count": 0, "findings": []}}
  }
}
```

### Bauen, prüfen, testen und paketieren

```sh
cd mechvane-checks-src
cargo build --release --target wasm32-unknown-unknown
wasm-tools component new target/wasm32-unknown-unknown/release/mechvane_checks_src.wasm -o ../mechvane-checks/mechvane-checks.wasm
cd ..
solidcraft-cli plugin check mechvane-checks
solidcraft-cli plugin test mechvane-checks --require-cases
cd mechvane-checks && zip -r ../mechvane-checks.zip plugin.json mechvane-checks.wasm && cd ..
```

Damit steht das Entry automatisch als Button im **Inspect**-Tab (und in **Model › Plugins**) mit Formular für `process` sowie über MCP als Read-only-Tool `mechvane-checks.check-design` bereit. Für eine optionale Ergebnis-Tabelle im angedockten Panel ergänzt man `"ui@0.1"` und `"storage@0.1"` analog zu `docs/book/plugin-examples/job-list` (`world: "panel-plugin"`).
