# Mechvane roadmap

**You and your agent on the same model.**

What works today, what comes next and what is planned. The same list is on [mechvane.dev/roadmap](https://mechvane.dev/roadmap/).

## Next milestone: v0.2

Mechvane's engineering knowledge moves into SolidCraft's own app as plugins: design checks and bolted connections as entries in SolidCraft for you and as tools for your agent, on the same model.

## Foundation

Mechvane builds on SolidCraft, an open parametric CAD kernel and app where everything is a command. SolidCraft stays unchanged; Mechvane adds its own layer on top.

- **Built on SolidCraft** (Available): Parametric modelling, sketches, features and assemblies from SolidCraft, used as a dependency without changes.
- **Parts and assemblies as separate files** (Available): One file per part, assemblies link their parts like in classic mechanical CAD.
- **Joints that survive part changes** (Available): update_links notices when a joint moved to another face after a part edit and puts it back.
- **MCP server for your agent** (Available): Parts, assemblies, joints, standard parts and design checks as tools for Claude and other agents.
- **Works with the running SolidCraft app** (Available): Mechvane connects to the SolidCraft app you have open, so you and your agent work on the same design in SolidCraft's own window.
- **Design checks in the open SolidCraft window** (Available): Run Mechvane's design checks on the part you have open in SolidCraft and get every finding with its rule, value and source.
- **Bolted connection in one call** (Available): Create a bolted connection with one call and take it back with one call; Mechvane remembers the steps. A single undo step inside the SolidCraft window follows with the plugin.
- **Engineering plugins inside SolidCraft** (Planned): Design checks, bolted connections and standard parts as SolidCraft plugins: a ribbon entry and a form for you, the same entry as a tool for your agent.
- **Knowledge and checks beyond one CAD** (Later): The knowledge catalog, design checks and fastener calculations are kept independent of any one CAD system, so that further CAD systems can connect later. SolidCraft stays first.
- **Clear error messages for your agent** (Available): When SolidCraft rejects a step, Mechvane names the feature and the spot and says in one sentence what touches what, with a suggestion, so your agent can fix it on the next try.
- **A short report after every step** (Available): After each change your agent learns how size, centre of mass, volume and number of bodies moved, and gets a warning when a cut hit nothing or the part fell apart.
- **A picture to check against** (Available): One image with iso, front, top and a section, with axes and sizes, the last change highlighted: a quick visual check for agents that can see images.
- **Roll back to find a problem** (Available): Your agent can move the end of part before a failing feature, repair it there and step forward again, as you would in Inventor.
- **Install in one step** (Available): pip install mechvane and mechvane setup on Linux, Windows and macOS; SolidCraft comes as a checked release download.
- **Install in under 15 minutes** (Available): A short guide for Windows and Linux: someone new to Mechvane installs it and builds the example flange in under 15 minutes.
- **Webhooks** (Planned): Mechvane reports events such as a saved part, a failed check or a finished agent task to a URL of your choice.
- **Stable 0.1 release** (Available): A release you can rely on, checked by four tests: your agent builds a set task in the open SolidCraft app, design checks run in that window with their sources, a bolted connection comes and goes in one call, and a newcomer installs Mechvane and builds the flange in under 15 minutes.
- **Import STEP as a reference body** (Available): Bring in STEP files from suppliers or other tools as solid bodies, using SolidCraft's STEP reader: place bought parts in an assembly, measure them and run the checks on them. In the workspace (File → Import STEP…) or through your agent.
- **Moves to SolidCraft 0.41** (Available): Mechvane switches to SolidCraft 0.41 (with the new solid kernel since 0.40), so offset, shell and loft cases that fail today work in your parts.
- **Moves to SolidCraft 0.43** (Available): Mechvane follows SolidCraft to 0.43, with view tabs, new sketch and solid commands and file verification available to you and your agent.
- **Keeps pace with SolidCraft** (Available): A weekly check lists new SolidCraft releases, new commands and fixed upstream issues, and shows which of them Mechvane already offers.
- **Open files from other CAD systems** (Planned): Parts and assemblies from Inventor, SolidWorks, CATIA, NX, Creo, Solid Edge, Fusion and FreeCAD, rebuilt as SolidCraft features with their history, sketches and parameters, so your earlier work comes along fully editable, nothing left behind. Inventor comes first. Features that cannot be rebuilt directly stay as placeholders until your agent or a later version rebuilds them.

## After v0.1

Ideas for working with your agent inside the SolidCraft app and its plugins, once v0.1 is out.

- **Direct editing** (Later): Move, offset, rotate or delete faces and change a hole's diameter right on the body, with handles and typed values, as one step in the history, as in Inventor. Especially useful for imported bodies without a history. Builds on SolidCraft's face operations and arrives as a plugin.
- **Lock what you decided** (Later): Mark parameters, features or faces as fixed; your agent works around them and tells you when a request would need them changed.
- **Why a value is what it is** (Later): Values your agent or an assistant calculates keep their derivation and source, shown when you hover over them.
- **Versions, branches and variants** (Later): Named versions you can compare side by side, branches to try a variant (also by your agent, for you to pick), later merged back feature by feature. Your agent can sweep parameters and lay out the variants in a table to choose from.
- **Comments and tasks on the model** (Later): Pin notes and tasks to a face, edge or feature. Check findings and requests for your agent live in the same place, and finished tasks stay with the part.
- **Follow your agent** (Later): Watch live where your agent is working: camera, selection and the feature it is editing. When you point and speak, your agent sees your view.
- **Keep working while your agent works** (Later): Your agent prepares its changes on a copy while you go on modelling, and you take them over when they are ready.
- **Point and speak** (Later): Select a face in the SolidCraft app and say what should happen there, e.g. "chamfer 1 × 45°". Speech input worked in the browser workspace; it comes to the app after v0.1.

## Engineering knowledge

Rules and values with their sources, so the checks do not guess and your agent proposes what an experienced engineer would.

- **Design checks** (Available): Wall thickness, hole edge distance, thread depth and printability, for 3D printing and CNC milling.
- **Standard parts** (Available): Generated on demand: socket and countersunk screws, hex bolts, nuts, washers, ball bearings, heat-set inserts.
- **Bolted connection assistant** (Available): Through holes, tapped blind holes and heat-set inserts with matching screw, washer and nut.
- **Thread depth by material** (Available): Checks use the material assigned to the part, e.g. 1.0 × d in steel, 2.0 × d in soft aluminium.
- **Open knowledge catalog** (In progress): Every value with its source, quotation and status, checked automatically against the source. A page to browse the catalog on mechvane.dev is planned.
- **Private knowledge area** (In progress): Add your own works standards, test results and notes in a private folder. Checks can use them and cite them, and they are never published. A book can be named as a literature reference.
- **Every finding shows its source** (Available): Each finding of the design check shows the rule, the value, the source and the quoted passage from the knowledge catalog.
- **Material database** (In progress): 28 materials so far (steels, stainless steels, aluminium alloys and casting, cast iron, copper, brass, engineering plastics and 3D-printing materials), every value with its source, ready to assign in SolidCraft as a material library.
- **Rules from material properties** (Planned): Minimum thread depth, edge distance and contact pressure calculated from strength values instead of fixed tables.
- **More rules per manufacturing process** (Available): For 3D printing teardrop holes and heat-set inserts, for milling inner radii, drilling depth and tool access, each with its source.
- **Material and appearance editor** (Planned): Material and look per part, in an open format you can render 1:1 in Blender.

## Domain modules

Loaded only when a document needs them. Delivered as SolidCraft plugins or as contributions to SolidCraft itself, as the need comes up.

- **Frame generator** (Planned): Aluminium profile frames (20/30/40 slot) and steel sections with connectors.
- **Design accelerators** (Planned): Shafts, gears, springs and more as guided assistants.
- **Named connection points** (Planned): Parts offer named anchors such as a shaft axis or a mounting face, for joints and for parts built to fit. Joints snap to them directly, and coupled joints (gears, rack, screw, belt) drive each other.
- **Replicate parts** (Planned): Place a part with its joint on every matching spot at once, for example a screw in every hole of a hole pattern.
- **Shared variables** (Planned): One table of variables for several parts and their assembly, such as wall thickness or gap; a change updates every linked file.
- **Skeleton modelling** (Planned): Take sketches, faces or coordinate systems from a skeleton part into other parts, linked and kept up to date, while parts stay separate files.
- **Geometry projected across parts** (Planned): A part built to fit another one keeps the link and follows when the other part changes.
- **Fit check across joints** (Planned): Hole and shaft fits checked against each other and against the kind of joint.
- **Clearance and collision check** (Planned): Find parts that overlap, at rest and along the range of each joint.
- **Exploded view and parts list** (In progress): Exploded views from joint axes and bolted connections with an animated preview, and a parts list to export.
- **Sheet metal additions** (Planned): Rules and helpers on top of SolidCraft's sheet metal. The 3D part and its flat pattern side by side, both live while you edit. Turn a solid into sheet metal by picking bend and rip edges, on top of SolidCraft's conversion.
- **Slicer module** (Planned): Slice and send parts to your 3D printer from Mechvane.
- **Print check for your agent** (Planned): A quick slice in the background shows your agent where support, bridges or too thin walls would appear.
- **Rule-based configuration** (Planned): Parameter rules and configuration tables for families of parts. One small table per property (length, material, fastening) instead of one large variant table.
- **Your own features as code** (Planned): Write a feature such as a bolted connection once; it sits in the model browser as one feature, recomputes on change, and you and your agent use it the same way.
- **Welding** (Planned): Weld seams as features (fillet and butt welds), weldments and ISO 2553 weld symbols in drawings.
- **Strength check** (Planned): A quick linear stress check right on the model, loads and supports picked on faces; CalculiX for contact, plasticity and vibration.

## Manufacturing drawings

ISO drawings straight from the 3D model. Delivered as SolidCraft plugins or as contributions to SolidCraft itself, as the need comes up.

- **Views** (Planned): Base, projected, section and detail views with hidden lines.
- **Dimensions and tolerances** (Planned): Fits, thread representation, surface symbols, geometric tolerances to ISO.
- **Title block and parts list** (Planned): Title block, parts list and balloons. The parts list stays linked to the model in both directions.
- **Drawings by your agent** (Planned): Your agent derives a drawing ready for manufacturing and checks it for missing or duplicate dimensions.
- **Drawings that know the model** (Planned): Every edge in a view keeps the feature it comes from, with thread, depth, fit or weld, so dimensions follow the design intent.
- **PDF and DXF export** (Planned): 

## Later

Ideas for later. Delivered as SolidCraft plugins or as contributions to SolidCraft itself, as the need comes up.

- **Motion simulation** (Later): 
- **Rendering via Blender** (Later): 
- **CAM bridge** (Later): 
- **Simple release states** (Later): Revision letters and a released state for parts, kept as Git tags.
