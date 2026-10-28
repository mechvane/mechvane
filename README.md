<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/mechvane/mechvane/main/docs/media/logo-wordmark-dark.png">
  <img alt="Mechvane" src="https://raw.githubusercontent.com/mechvane/mechvane/main/docs/media/logo-wordmark-light.png" width="320">
</picture>

# Mechvane

**You and your agent on the same model.**

Parametric 3D CAD for everyday mechanical engineering (individual engineers, makers,
small and medium-sized companies), following the workflow of classic mechanical CAD systems.
Model by hand, hand a step to an AI agent, or both: you work on the same parts and get the
same design checks either way. The core stays small; domain modules (sheet metal, standard
parts, frames, drawings …) load only when a document or the user needs them.

**[Try the web UI in your browser](https://mechvane.dev/)**: example models with the model
tree and design check findings, nothing to install.

![A joint jumps to the wrong bore after a part edit, update_links puts it back](https://raw.githubusercontent.com/mechvane/mechvane/main/docs/media/update_links.gif)

*Change a part, and `update_links` notices that a joint jumped to a different bore and
repairs it (regenerate with `python3 tools/demo_update_links.py`).*

## Guiding principles

- **One model, many hands.** Every action is a typed command. You in the GUI, your scripts,
  plugins and AI agents (MCP) share one interface, with undo, batch rollback and precise
  error messages, so you can pick up where your agent left off and the other way round.
- **Engineering knowledge for you and your agent.** An open, sourced knowledge catalog: standard
  values from freely accessible sources, best practice from public handbooks and design
  guides, our own measurement series on the printer. Every rule carries its source,
  rationale, exceptions and severity (error or hint), so `check_design` does not guess and
  an agent proposes what an experienced engineer would.
- **No dead weight.** What monolithic CAD suites carry around (piping, cable harness, BIM,
  rendering studio …) is a plugin here or left out.
- **Proven workflows where they work.** Design accelerators (bolted connections, shafts,
  gears), frame generator, standard parts, ISO drawings with parts list, rule-based
  configuration.
- **Text- and git-friendly file format.**

## Foundation

Mechvane builds on [SolidCraft](https://github.com/tangency-labs/solidcraft) (Rust,
Apache-2.0), an open CAD kernel and app where "everything is a command", with a built-in
MCP server. SolidCraft stays unchanged as a dependency; Mechvane adds its own layer on top
([ADR 0001](https://github.com/mechvane/mechvane/blob/main/docs/adr/0001-grundlage-solidcraft.md)).

## Quick start

Requirements: Python ≥ 3.11. Everything else comes with `mechvane setup`: it downloads the
pinned `solidcraft-cli` and SolidCraft web app (v0.25.1) from the
[SolidCraft release](https://github.com/tangency-labs/solidcraft/releases) for your platform
(Linux x86_64/aarch64, Windows x64/arm64, macOS) and checks their SHA256. No build needed;
rendering works headless too.

```sh
pip install mechvane
mechvane setup        # SolidCraft CLI and web app, about 90 MB, once
mechvane ui --demo    # example models in their own app window
mechvane ui my-project/   # your own .solidcraft files
mechvane shortcut     # optional: start menu entry for ~/Mechvane (Windows, Linux)
```

`mechvane ui` opens an app window when Chrome, Edge, Chromium or Brave is installed (no tabs, no
address bar; closing it stops Mechvane), otherwise a tab in your default browser. `--browser`
always uses a tab. Everything runs locally and offline after `mechvane setup`.

Alpha: tested on Linux and Windows 11 (x64); macOS is expected to work but not yet tested.
If `mechvane` is not found after a user install on Windows, use `python -m mechvane setup` (and
`ui`, `mcp`) instead.

An existing `solidcraft-cli` is used when you set `SOLIDCRAFT_CLI` or skip `mechvane setup`
and have it on your `PATH`.

As an MCP server for an agent (e.g. Claude Code), `.mcp.json` in your project:

```json
{
  "mcpServers": {
    "mechvane": {
      "command": "mechvane",
      "args": ["mcp", "--workspace", "./workspace"]
    }
  }
}
```

For development, clone the repo and run the checks:

```sh
git clone https://github.com/mechvane/mechvane && cd mechvane
pip install -e .
python3 tests/mechvane/check.py      # about 240 checks, a few minutes
python3 tests/reference/check.py     # reference parts with expected values
```

Then ask, for example: "Build an 80×40×8 plate with four M5 clearance holes, bolt it to a
bracket and check the design." The agent uses `new_part`, `run`, `bolted_connection`,
`add_joint` and `check_design`. When a part changes, `update_links` finds joints that
jumped to a different face and repairs them.
Windows: [docs/installation-windows.md](https://github.com/mechvane/mechvane/blob/main/docs/installation-windows.md) (German).

## Status

Phase 1: a Python prototype running as an MCP server on top of SolidCraft. Separate part
and assembly files, sketches owned by their feature, a model browser in the classic tree
style, joints across files with checking and repair, standard parts (screws, nuts,
washers, ball bearings), a bolted connection assistant with patterns, `check_design` with
design rules, ISO 286 fits and a knowledge catalog of sourced standard values. A read-only
web UI (`python3 -m mechvane.ui <file.solidcraft> [--port 8765]`) shows the 3D model,
the model browser tree and design/joint findings with interactive face highlighting.
Its "Model by hand" mode (`/model`) embeds the SolidCraft web app: edit the part or
assembly with the mouse, save, and Mechvane checks it again and updates the links. The web
app is downloaded once from the SolidCraft release and checked against a pinned SHA256.

![Mechvane read-only web UI showing model tree, 3D viewport and highlighted countersink finding](https://raw.githubusercontent.com/mechvane/mechvane/main/docs/media/web-ui-1.png)

*A countersink that notches the wall, highlighted on click (regenerate with
`python3 tools/demo_web_ui.py`).*

![Model by hand: the SolidCraft web app embedded in Mechvane, the countersink moved away from the wall and Mechvane's findings updated after saving](https://raw.githubusercontent.com/mechvane/mechvane/main/docs/media/model-mode.png)

*Model by hand: the same bracket in the embedded SolidCraft web app, the countersink moved away
from the wall and saved, Mechvane checked it again (regenerate with `python3 tools/demo_model_ui.py`).
Try it without installing: [live demo](https://mechvane.dev/model.html?demo=bracket).*

## Contents

- [ROADMAP.md](https://github.com/mechvane/mechvane/blob/main/ROADMAP.md): phases, decision points, risks
- [docs/adr/](https://github.com/mechvane/mechvane/tree/main/docs/adr): architecture decisions
- [MCP server](https://github.com/mechvane/mechvane/blob/main/docs/mechvane-mcp.md) (`mechvane/`): tools, data model, test reports
- [tests/](https://github.com/mechvane/mechvane/tree/main/tests): layer checks and reference parts
- [docs/research/](https://github.com/mechvane/mechvane/tree/main/docs/research): research notes and practice tests, dated. Notes
  marked as drafts (e.g. `-flash`, `-gemini`) are unverified unless a check note says
  otherwise.

Most project documentation is in German for now; code and comments are in English.

## License

MIT OR Apache-2.0, at your option (`LICENSE-MIT`, `LICENSE-APACHE`), like SolidCraft, so
code can move in both directions. Contributions are under the same terms. AGPL slicers
such as CuraEngine only run as separate processes and are not part of Mechvane
(`NOTICE`). See [CONTRIBUTING.md](https://github.com/mechvane/mechvane/blob/main/CONTRIBUTING.md).

Mechvane is an independent project and is not affiliated with Autodesk or any other CAD
vendor. Product names only describe workflows.
