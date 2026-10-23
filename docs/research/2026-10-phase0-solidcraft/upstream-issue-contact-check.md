### What happened

`contact.check` reports no collision when two plates cross each other through their faces, while `inspect.interference` finds the overlap. It only reports a collision when a corner of one body lies inside the other.

Hinge: a grounded base plate and a lid plate (both 40 × 40 × 3 mm), joined by a revolute joint along their shared edge. The lid is driven past 180° without a contact set, then a contact set with both occurrences is created and checked:

| Lid angle | `contact.check` | `inspect.interference` |
|---|---|---|
| 195° | 1 collision, depth 0.72 mm | 1390.9 mm³ |
| 210° | **none** | 720.0 mm³ |
| 240° | **none** | 415.7 mm³ |
| 270° | **none** | 360.0 mm³ |

From 210° on the lid passes through the whole base plate, so no vertex of either body lies inside the other. It looks as if the quick check only tests vertices or corners and misses edge-through-face or face-through-face crossings. Earlier, in the same setup, `motion.interference` also reported nothing for a study across these angles. I did not re-run that for this report.

Expected: `contact.check` reports Base:1 / Lid:1 at 210°, 240° and 270°, as `inspect.interference` does.

### Steps to reproduce

`solidcraft-cli run repro.json --results` with:

```json
{"commands": [
 {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 3, "corner": [-20, -40, 0], "operation": "new", "body_name": "BasePlate"}},
 {"command": "solid.box", "params": {"length": 40, "width": 40, "height": 3, "corner": [-20, 0, 0], "operation": "new", "body_name": "LidPlate"}},
 {"command": "component.create", "params": {"name": "Base", "parent": "root", "activate": false}},
 {"command": "component.move_bodies", "params": {"bodies": ["BasePlate"], "component": "Base"}},
 {"command": "component.create", "params": {"name": "Lid", "parent": "root", "activate": false}},
 {"command": "component.move_bodies", "params": {"bodies": ["LidPlate"], "component": "Lid"}},
 {"command": "occurrence.ground", "params": {"occurrence": "Base:1", "grounded": true}},
 {"command": "joint.create", "params": {"type": "revolute", "name": "Hinge", "flip": true, "limits": [[0, 270]],
   "a": {"occurrence": "Base", "point": [0, 0, 3], "z": [1, 0, 0]}, "b": {"occurrence": "Lid", "point": [0, 0, 3], "z": [1, 0, 0]}}},
 {"command": "joint.drive", "params": {"joint": "Hinge", "value": 210, "quiet": true}},
 {"command": "contact.create", "params": {"occurrences": ["Base:1", "Lid:1"], "name": "Plates"}},
 {"command": "contact.check", "params": {}},
 {"command": "inspect.interference", "params": {}}
]}
```

The last two results are `{"collisions": []}` and an interference of 720 mm³ between BasePlate and LidPlate. With `"value": 195` the check reports the collision.

With the contact set enabled before driving, the drive correctly stops at contact (about 180.01°). So this matters for checks of a pose that was reached some other way, such as a set joint value or a moved occurrence.

### SolidCraft version and OS

solidcraft-cli 0.16.2 (release tar.gz, linux x86_64), headless, Debian container. Not checked on `main`. Related, but different: #3249 (mesh bodies skipped by `inspect.interference`).
