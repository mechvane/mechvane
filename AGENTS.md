# AGENTS.md

Guidance for coding agents (Claude Code, Codex, Gemini, Cursor, …) working **on** Mechvane. Agents that
**use** Mechvane to design parts get their instructions from the MCP server itself (`mechvane mcp`).
Humans: see [CONTRIBUTING.md](CONTRIBUTING.md); everything there applies to agents too.

## What this is

Parametric CAD for everyday mechanical engineering, built on
[SolidCraft](https://github.com/tangency-labs/solidcraft). **SolidCraft stays unchanged** (ADR 0001):
Mechvane is its own layer on top – Python package `mechvane/`, an MCP server, a web UI (frozen, see below) and a sourced
knowledge catalog. Tagline: "You and your agent on the same model."

Direction (see the README): Mechvane's engineering knowledge – design checks with their sources, bolted connections, standard
parts, ISO fits – is moving into SolidCraft's own app, first by connecting to the app you have open, later as SolidCraft
plugins. The browser workspace stays available as a local preview as it is; the public live demo is offline since 2026-11-23. For contributions this means: put new engineering
work into the design checks, the catalog and the MCP tools; please do not start new web-UI features without asking in an issue
first.

## Setup and checks

```sh
pip install -e .
mechvane setup                         # pinned SolidCraft CLI and web app (SHA256-checked)
python3 tests/mechvane/check.py        # all checks, a few minutes; must end with "0 failure(s)"
python3 tests/reference/check.py       # reference parts with expected values
```

Every code change comes with a check in `tests/mechvane/check.py` (research notes and catalog entries need none; `check.py` validates every entry). Never weaken or skip a check to get to green.
Headless checks of the frozen web UI: `tools/ui_smoke.py` (needs playwright; only needed when a change touches `mechvane/ui/`). Heavy runs (`ui_smoke.py`, `demo_smoke.py`) take a
lock (`tools/heavy_lock.py`) and wait for each other: run them one at a time.
Nightly and on pushes to `main` in the public repository, `.github/workflows/platforms.yml` runs a clean installation and smoke test (`tools/ci_smoke.py`) across Windows, macOS, and Linux.

## Where things are

- `mechvane/` – MCP server (`server.py`), documents and workspace, joints and links (`links.py`), standard
  parts, bolted connections, design rules, glTF export; `mechvane/ui/` – web UI (Check page, "Model by hand",
  agent chat; frozen, kept as it is), static files in `mechvane/ui/static/`
- `katalog/` – knowledge catalog (schema `katalog/schema.json`, entries `katalog/eintraege/`), material
  library for SolidCraft (`tools/katalog_to_solidcraft.py`)
- `docs/adr/` – architecture decisions; `docs/mechvane-mcp.md` – tools and data model (German)
- `roadmap.json` – public roadmap at mechvane.dev/roadmap (statuses: done, next, progress, planned, later)
- `website/` – the website at mechvane.dev; `tools/build_demo_site.py` builds the Pages site (the live demo only with `--with-demo`)

## Rules

- **Code and comments in English**, docs mostly German (English is welcome). Match the surrounding code.
- **Values need a source.** Numbers in the catalog or in design rules come from a freely accessible source
  with a verbatim quote; `python3 tools/check_sources.py <note.md>` (or a catalog entry,
  `katalog/eintraege/<area>/<id>.json`) must find them. No values from paid standards documents, no copied
  standard texts. A new catalog entry has `pruefstatus` `offen`, a file name equal to its `id`, and every source with `url`,
  `stelle`, a verbatim `zitat` and `abgerufen`. Changing an existing entry can move a design-check threshold or the source shown
  with a finding (`mechvane/design_rules.py`): do it in its own change, with a test.
- **No GPL/LGPL/AGPL code in Mechvane.** Mechvane stays MIT OR Apache-2.0, so nothing copied, ported or
  linked from (L/A)GPL sources goes into this repository.
- **GPL programs may run as separate programs** (input file in, result file out, e.g. CuraEngine, later
  CalculiX or Gmsh): check their licence first and say in the docs and installer what gets added.
- **Clean room for upstream work:** for anything meant for SolidCraft or cadmpeg (kernel features, file
  format analysis) do not read GPL/LGPL/AGPL source code, and do not automate commercial CAD to produce
  contributions (SolidCraft's governance, cadmpeg's provenance statement).
- In assemblies use Mechvane's tools (`insert_part`, `add_joint`, `edit_joint`, `update_links`,
  `bolted_connection`), not raw SolidCraft joint commands, so joints stay checkable.
- A sketch used by one feature sits directly before it (`sketch_rule`).
- Changing behaviour users see (research notes and catalog entries need no snippet): add a changelog snippet in `changelog.d/<issue>.md` (first line
  one of `Added`/`Changed`/`Fixed`/`Removed`, then bullet list in English; do not edit `CHANGELOG.md`
  directly) and update `roadmap.json` (`next` for done but unreleased).
- Public texts: encouraging and factual, no hype, always credit SolidCraft.
