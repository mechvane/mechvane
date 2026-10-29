# AGENTS.md

Guidance for coding agents (Claude Code, Codex, Gemini, Cursor, …) working **on** Mechvane. Agents that
**use** Mechvane to design parts get their instructions from the MCP server itself (`mechvane mcp`).
Humans: see [CONTRIBUTING.md](CONTRIBUTING.md); everything there applies to agents too.

## What this is

Parametric CAD for everyday mechanical engineering, built on
[SolidCraft](https://github.com/tangency-labs/solidcraft). **SolidCraft stays unchanged** (ADR 0001):
Mechvane is its own layer on top – Python package `mechvane/`, an MCP server, a web UI and a sourced
knowledge catalog. Tagline: "You and your agent on the same model."

## Setup and checks

```sh
pip install -e .
mechvane setup                         # pinned SolidCraft CLI and web app (SHA256-checked)
python3 tests/mechvane/check.py        # all checks, a few minutes; must end with "0 failure(s)"
python3 tests/reference/check.py       # reference parts with expected values
```

Every change comes with a check in `tests/mechvane/check.py`. Never weaken or skip a check to get to green.
Headless UI checks: `tools/ui_smoke.py` (needs playwright).

## Where things are

- `mechvane/` – MCP server (`server.py`), documents and workspace, joints and links (`links.py`), standard
  parts, bolted connections, design rules, glTF export; `mechvane/ui/` – web UI (Check page, "Model by hand",
  agent chat), static files in `mechvane/ui/static/`
- `katalog/` – knowledge catalog (schema `katalog/schema.json`, entries `katalog/eintraege/`), material
  library for SolidCraft (`tools/katalog_to_solidcraft.py`)
- `docs/adr/` – architecture decisions; `docs/mechvane-mcp.md` – tools and data model (German)
- `roadmap.json` – public roadmap at mechvane.dev/roadmap (statuses: done, next, progress, planned, later)
- `website/` – the website at mechvane.dev; `tools/build_demo_site.py` builds the Pages site

## Rules

- **Code and comments in English**, docs mostly German (English is welcome). Match the surrounding code.
- **Values need a source.** Numbers in the catalog or in design rules come from a freely accessible source
  with a verbatim quote; `python3 tools/check_sources.py <note.md>` must find them. No values from paid
  standards documents, no copied standard texts.
- **No GPL/LGPL/AGPL code**, not even as a reference to read, and no automating commercial CAD to produce
  contributions (SolidCraft's governance).
- In assemblies use Mechvane's tools (`insert_part`, `add_joint`, `edit_joint`, `update_links`,
  `bolted_connection`), not raw SolidCraft joint commands, so joints stay checkable.
- A sketch used by one feature sits directly before it (`sketch_rule`).
- Changing behaviour users see: add a line to `CHANGELOG.md` under "Unreleased" and update `roadmap.json`
  (`next` for done but unreleased).
- Public texts: encouraging and factual, no hype, always credit SolidCraft.
