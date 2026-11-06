🤖 Written by Claude Code on behalf of 👤

Two additions to the report above, same setup (0.30.1 against 0.40.0-rc.2):

- **A cut that misses the body still names it in `changed_bodies`.** Box 40 × 40 × 5, a Ø5 pin joined on top
  (`solid.cylinder {"diameter": 5, "height": 5, "base": [20, 20, 5], "operation": "join"}`), then a small sphere cut
  0.1 mm outside the pin: `solid.sphere {"center": [22.6, 20, 7.5], "radius": 0.04, "operation": "cut"}`.
  0.30.1 answers `changed_bodies: []`, rc.2 `["Body1"]`, with the same face count before and after. We used the
  empty list to tell a hole from a pin; scripts that do the same will now see every probe as a hit.
- **Hinge contact stop, in numbers:** 0.30.1 stops at 180.012° with 6.8 mm³ overlap, rc.2 at 179.761° with none,
  so a gap of about 0.17 mm at the lid's far edge (two 40 × 40 × 3 plates, revolute joint, contact set, driven to 270°).
