A question on UI, since `docs/plugins.md` currently rules out per-plugin egui ("No per-plugin egui in milestone 2", display limited to label, tooltip and an icon from the app's registry):

Is there a plan for plugins that bring **their own panel or workspace**, later on? The case I have in mind is a slicer for FDM printing as a workspace next to Design. The user switches to a Print tab, the current bodies go straight in, the engine (a separate process, so AGPL engines like CuraEngine stay out of the app) slices them, and the plugin shows a layer preview with sliders and print settings. A parameter change in Design triggers a new slice. Commands alone can't do that: it needs a panel with its own controls and a way to draw toolpaths into the viewport. It is close to the 3D printing research in #1626 and to what Manufacture needs.

Possible shapes, from least to most UI freedom:

1. **Declarative panels:** the plugin returns a schema (sliders, dropdowns, tables, buttons bound to its own exported functions), and the host draws it with the app's widgets. This extends the `parameter_schema()` idea from milestone 2 to whole panels. It stays sandboxed and keeps one look.
2. **Viewport overlays:** the host accepts line/point/mesh buffers from a plugin (with colours per segment, e.g. by line type) and draws them in the 3D view, toggled from the plugin's panel. A layer preview needs this.
3. **Workspace registration:** a plugin adds a workspace tab (Design / Render / … / Print) that holds its panels and overlays.

Would something like 1 + 2 fit the direction, or should tools like this live in-tree instead? I'm happy to write it up as a separate issue if that is easier to track.
