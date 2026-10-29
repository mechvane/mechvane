# Changelog

What changed in each Mechvane release. Mechvane is in alpha: file formats and tool names may still
change between releases, and each release names the SolidCraft version it is built and tested with.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **Material library for SolidCraft** (`katalog/werkstoffe.solidcraft-library.json`): the 16 catalog
  materials, each with density, a matching look and an engineering card (stiffness, strength, thermal
  values) that names the source of every value. Assign e.g. "EN AW-6082 T6" instead of a generic
  "Aluminum"; mass and the thread-depth check then use it. Rebuild with `tools/katalog_to_solidcraft.py`.
- **Example: the Mechvane logo as a real assembly** (`docs/examples/logo_showcase/`): welded steel M on a
  back plate, the V in brass and copper on spacers, fastened with countersunk screws. Comes with Blender
  scenes (angled and top view) and the same model as glTF with its materials.
- `export_gltf(document, path)`: writes a part or assembly as glTF 2.0 for Blender, three.js and other
  viewers, one mesh per body with sharp edges and the body's look (colour, metallic, roughness, IOR) taken
  from its SolidCraft appearance or material; faces with their own appearance keep it, and assemblies take
  the looks from their part files.
- Tools to take a model to Blender: `tools/logo_to_gltf.py` writes glTF 2.0 with clearcoat and anisotropy
  from a set of OpenPBR parameters, `tools/render_logo_blender.py` renders it with Cycles.

### Fixed

- `bolted_connection` drilled at a wrong height ("position … is not on a face") when there was a gap or a
  spacer between the plates and the lower part had a chamfer: the extended plane of the chamfer counted as
  a hit. The cause: a chamfer's face name contains "|", which also separates the two faces in an edge
  name, so the chamfer's edges were not found. Bolted connections and design rules now match edges to such
  faces correctly; hits also have to lie within their body.

## [0.1.0a7] - 2026-10-29

Built and tested with SolidCraft 0.25.1.

### Added

- **Parameters** on the Check page, under the model tree: change user parameters (and, folded away,
  feature dimensions) by typing a new value or expression and pressing Enter. Several changes are
  applied together; a bad expression changes nothing and says why. The file is saved and the view
  reloads.
- **Measure** in the 3D view of the Check page: click two points for the distance and ΔX/ΔY/ΔZ; on
  two flat faces it also gives the gap between parallel faces or the angle between them, on two holes or
  shafts the distance between their axes. One click shows the face's area, on a hole or shaft its
  diameter and axis. Works in the live demo as well.
- `check_design` takes a `material` (steel, cast_iron, alu, alu_wrought, brass, ...): the thread
  engagement depth then follows the same table as `bolted_connection` (e.g. 1.0 × d in steel,
  2.0 × d in soft aluminium) instead of a flat 1.5 × d. Values without a checked source say so.
  Without it, the material assigned to the part's bodies in SolidCraft is used.
- The Check page lets you choose the manufacturing profile and the material for the design rules
  (remembered per document in this browser).
- **Section** in the 3D view: cut the model along X, Y or Z with a slider, the cut surface shown in
  colour. Esc leaves either tool.
- The header says whether Mechvane keeps running: "Closing this window quits Mechvane" in its own
  app window. In a browser tab, where closing does not stop it, a **Quit** button ends Mechvane.
- Knowledge catalog: first 16 materials (structural and stainless steels, aluminium alloys, grey cast
  iron, brass, POM, PA6, PLA, PETG) with density, stiffness, strength, hardness and thermal values,
  every value with its source and quotation.
- A public roadmap at a glance: https://mechvane.dev/roadmap/

## [0.1.0a6] - 2026-10-29

### Fixed

- **Moving a project folder** (or copying it to another computer) no longer breaks assemblies:
  joints, subassemblies and bolted connections stored the full path of each part file, so after a
  move every joint reported `file_missing`. Part files are now stored relative to the assembly.
  Assemblies saved by earlier versions find their parts by name in their own folder.
- An empty project folder (the first start from the start menu entry) showed "Connection lost".
  The Check page now says how to make the first part and opens it as soon as it exists.
- The Check page showed an error for a new part that has no bodies yet; it now shows it empty.
- Clicking the start menu entry again started another Mechvane each time. A second `mechvane ui` for
  the same file or folder now opens a window on the one already running.
- Bolted connections on a face split with `solid.split_face` no longer report their anchor as lost
  (SolidCraft 0.25 names the pieces `F2:top#[…]`); the piece under the fastener is used.

## [0.1.0a5] - 2026-10-29

### Fixed

- **Windows with Intel graphics:** saving any part with a curved face (a hole, a cylinder, every
  standard part) crashed SolidCraft with `0xC0000005`, so `mechvane ui --demo` did not start. Saving
  renders through wgpu, and Intel's Vulkan driver crashes there. Mechvane now starts SolidCraft with
  DirectX 12 on Windows; set `WGPU_BACKEND` yourself to choose another backend
  ([SolidCraft #5589](https://github.com/tangency-labs/solidcraft/issues/5589)).
- Windows: the web UI put its scratch folder under `/tmp`, which doesn't exist there, so `mechvane ui`
  failed to start. It now uses the system's temp folder.
- `mechvane ui --demo` after a first start that broke off (for example the crash above): the
  example models are built again from scratch instead of failing on the files left behind.
- `mechvane ui` on a folder (and `--demo`): the Check page stayed empty because no document was open.
  It now lists the folder's documents and opens the one in `?doc=`, else the first assembly.
- Windows installation guide: PowerShell needs `&` before commands that start with `$HOME`.

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

[0.1.0a7]: https://github.com/mechvane/mechvane/compare/v0.1.0a6...v0.1.0a7
[0.1.0a6]: https://github.com/mechvane/mechvane/compare/v0.1.0a5...v0.1.0a6
[0.1.0a5]: https://github.com/mechvane/mechvane/compare/v0.1.0a4...v0.1.0a5
[0.1.0a4]: https://github.com/mechvane/mechvane/compare/v0.1.0a3...v0.1.0a4
[0.1.0a3]: https://github.com/mechvane/mechvane/compare/v0.1.0a2...v0.1.0a3
[0.1.0a2]: https://github.com/mechvane/mechvane/releases/tag/v0.1.0a2
[0.1.0a1]: https://pypi.org/project/mechvane/0.1.0a1/
