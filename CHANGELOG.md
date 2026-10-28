# Changelog

What changed in each Mechvane release. Mechvane is in alpha: file formats and tool names may still
change between releases, and each release names the SolidCraft version it is built and tested with.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0a4] - 2026-10-28

You and your agent on the same model: the web UI now has a chat with your own AI agent, and Mechvane
opens in a window of its own.

### Added

- **Agent chat in "Model by hand".** Talk to your own coding agent (Claude Code through the
  [Agent Client Protocol](https://agentclientprotocol.com) adapter `claude-agent-acp`) next to the model.
  Each message is one turn on your files: the app saves first, the agent works through the Mechvane
  tools only, and the app reloads with the camera where it was. **Stop** and errors put the files back
  as they were; **Undo** and **Redo** take back or restore a whole turn. Deleting, file commands and the
  agent's own shell and file tools are declined.
- **Selection for the agent.** What you select in the model goes with your message in Mechvane's names:
  the face and the feature that made it, where you clicked ("here") and the face's centre ("in the
  middle"). In an assembly the face is named in its part file.
- **Speech input (first version).** Hold the microphone button and speak (German, Chrome and Edge).
  Mechvane cleans up what was heard in code: "eins mal fünfundvierzig Grad" becomes "1 × 45°",
  "Em sechs" becomes "M6", and names in your model are recognised. You check the text before sending.
- **Own app window.** `mechvane ui` opens Mechvane in an app window (Chrome, Edge, Chromium or Brave),
  and closing the window stops Mechvane. `--browser` opens a tab instead.
- **Start menu entry.** `mechvane shortcut [folder]` adds "Mechvane" to the Windows start menu or the
  Linux application menu, with the Mechvane icon.
- **Request a feature.** A button in the web UI opens a prefilled GitHub issue for a feature, module,
  standard part, design rule or bug. Nothing is sent until you submit it on GitHub.
- Logo, favicon and a dark theme as the default look of the web UI.
- `GET /api/about` with the Mechvane and SolidCraft versions.

### Changed

- **SolidCraft 0.25.1** (was 0.21.0). Designs saved now use SolidCraft's file format 41 and don't open
  in SolidCraft 0.24 or older. Joints no longer move to a different hole of the same size when a part
  gains one earlier in its history (SolidCraft #3330, fixed upstream); `update_links` keeps checking.
- Mechvane starts its SolidCraft sessions with `--headless`, so they never join a SolidCraft app you
  have open.
- A part inserted into an assembly stays free unless you ask for it to be grounded, as before
  (SolidCraft 0.25 grounds the first part on its own).
- A document whose file changed on disk (saved by hand in the web UI, for example) is read again before
  the next tool call; with unsaved changes in the session you get an error instead of a silent overwrite.
- When the port is taken, `mechvane ui` uses a free one.

## [0.1.0a3] - 2026-10-28

### Fixed

- Design check: the edge distance from a hole to a cylindrical outer face is measured from the hole's
  centre; coaxial holes are checked one by one, each thread matched to its own hole.
- Standard parts: a part that fails to build no longer leaves a file behind (an existing file kept with
  `overwrite=True` stays); DIN 625 ball bearings get their edge chamfers.
- Bolted connections: countersunk screws sit at the right depth and point the right way; a hole
  pattern follows an anchor part that was rotated.
- Mechvane removes the empty scratch folders that `solidcraft-cli mcp` leaves behind (SolidCraft
  #7836) and its own browser profile for screenshots.

## [0.1.0a2] - 2026-10-27

### Added

- Standard parts: hexagon head bolts ISO 4017, M3 to M10.
- Design check: choose the build direction for printability (`build_direction`).

### Changed

- The web UI ships three.js with the package, so it works offline.

### Fixed

- Windows: the SolidCraft CLI pipe uses UTF-8, the UI server no longer shares its port with a second
  server, and `python -m mechvane setup|ui|mcp` works where the `mechvane` command is not on the PATH.

## [0.1.0a1] - 2026-10-27

First alpha on PyPI, built on SolidCraft 0.21.0.

### Added

- `pip install mechvane`, then `mechvane setup` downloads the pinned SolidCraft CLI and web app for
  your platform and checks their SHA256.
- MCP server for agents (`mechvane mcp`): separate part and assembly files, sketches owned by their
  feature, a model browser in the classic tree style, joints across files with checking and repair
  (`add_joint`, `update_links`), standard parts (screws, nuts, washers, ball bearings), a bolted
  connection assistant with patterns, `check_design` with design rules, ISO 286 fits and a catalogue of
  sourced standard values.
- Web UI (`mechvane ui`): 3D view, model browser and findings with face highlighting, and "Model by
  hand" with the SolidCraft web app embedded; Mechvane checks every save again.

[0.1.0a4]: https://github.com/mechvane/mechvane/compare/v0.1.0a3...v0.1.0a4
[0.1.0a3]: https://github.com/mechvane/mechvane/compare/v0.1.0a2...v0.1.0a3
[0.1.0a2]: https://github.com/mechvane/mechvane/releases/tag/v0.1.0a2
[0.1.0a1]: https://pypi.org/project/mechvane/0.1.0a1/
