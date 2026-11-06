🤖 Written by Claude Code on behalf of 👤

Test report from [Mechvane](https://github.com/mechvane/mechvane), an Inventor-style layer on SolidCraft (MCP, headless). Release-to-release: **v0.30.1** (truck) against **v0.40.0-rc.2** (solidcore), both from the release tarballs, Linux x86_64, `solidcraft-cli mcp --headless`.

**Shell and offset on a body with one freeform face** (our case from #745): loft from a 40 × 40 square at z = 0 to a circle r = 12 at z = 30, then one command per fresh session.

| Case | 0.30.1 | 0.40.0-rc.2 |
|---|---|---|
| `solid.shell`, bottom face removed, t = 2 | refused (`only bodies with planes, cylinders…`) | ✓ 2.3 s, 29127 → 7510 mm³ |
| `solid.shell`, closed hollow (`faces: []`), t = 1 | `select 1…1000 faces` | ✓ 2.9 s, 29127 → 5348 mm³ |
| `solid.offset_face`, bottom face +3 | refused | ✓ 2.1 s, 29127 → 34152 mm³ |
| `solid.offset_face`, top (circle) face +3 | refused | ✓ 4.3 s, 29127 → 30370 mm³ |
| `solid.shell`, top (circle) face removed, t = 2 | refused | `SMLib shell: operation: SMLib failed (status 1001)` |
| `solid.offset_face`, the lofted side face +1 (#10884) | refused | `SMLib made no change: the offset faces reported success but moved no face onto its new surface` |

So the far-away freeform face no longer blocks planar faces, which was the whole of #745 for us. Thank you! Shelling with the circular end open and offsetting the lofted face itself still fail.

<details><summary>Commands (one session per case)</summary>

```json
[
  {"command": "sketch.create", "params": {"plane": "XY"}},
  {"command": "sketch.rectangle.two_point", "params": {"p0": [-20, -20], "p1": [20, 20]}},
  {"command": "sketch.finish", "params": {}},
  {"command": "sketch.create", "params": {"plane": {"origin": [0, 0, 30], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}}},
  {"command": "sketch.circle.center", "params": {"center": [0, 0], "radius": 12}},
  {"command": "sketch.finish", "params": {}},
  {"command": "solid.loft", "params": {"sections": [{"sketch": "Sketch1"}, {"sketch": "Sketch2"}]}},
  {"command": "solid.shell", "params": {"faces": [[0, 0, 30]], "thickness": 2}}
]
```
Other cases: `solid.shell {"faces": [[0,0,0]], "thickness": 2}`, `solid.shell {"faces": [], "thickness": 1}`, `solid.offset_face {"faces": [[0,0,0]], "distance": 3}`, `{"faces": [[0,0,30]], "distance": 3}`, `{"faces": [[16,0,15]], "distance": 1}`.
</details>

**Our regression suites on rc.2**

- Reference parts (volumes and bounding boxes over parameter changes, 58 checks): all match 0.30.1 except the
  contact stop of a hinge. Two 40 × 40 × 3 plates on a revolute joint with a contact set, driven to 270°:

  | | stops at | overlap at the stop |
  |---|---|---|
  | 0.30.1 | 180.012° | 6.8 mm³ |
  | 0.40.0-rc.2 | 179.761° | 0 |

  So solidcore stops 0.24° early, a gap of about 0.17 mm at the lid's far edge. Not wrong as such, just a data
  point on the contact tolerance; we widened our check.
- **A cut that misses the body still names it in `changed_bodies`.** Box 40 × 40 × 5, a Ø5 pin joined on top,
  then a sphere r 0.04 cut 0.1 mm outside the pin (`solid.sphere {"center": [22.6, 20, 7.5], "radius": 0.04,
  "operation": "cut"}`): 0.30.1 answers `changed_bodies: []`, rc.2 `["Body1"]`, with the same face count before and
  after. We used the empty list to tell a hole from a pin (probe cut just outside the cylinder); we now count faces
  instead, but other scripts may rely on it.
- A change tool authors will notice: a cylindrical face is now **one face** (`F3:bore:side:0`), where truck gave two
  halves (`side:0`, `side:1`) plus split pieces (`side:0#[F1:+z]`). Our hole depth from the face area and one test
  relied on the halves; fixed on our side. One face per cylinder is the better model.

We'll run our suites again on the final 0.40.0 and report anything that differs.
