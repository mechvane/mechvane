<!-- Filed as tangency-labs/solidcraft#3330 on 2026-10-20 (scripts inlined as code blocks). -->
<!-- Title: Update Links can silently move a joint to another face of a linked component -->

### What happened

A joint on a face of a linked component (Insert Design) moves to a different face after the part design changes and Update Links runs. There is no warning from `component.update_links` and no error from `joint.list`.

Part design: a plate 60 × 40 × 5 with one Ø 6 hole at x = `hx`. Assembly: the plate inserted with `component.insert_design` and grounded, a pin as its own component, and a rigid joint from the pin to the hole's top edge (`circle: [13, 0, 5]`, so the hole at x = 10).

Then the part design is changed and saved, and the assembly runs `component.update_links`:

| Change in the part design | Joint frame after Update Links | Expected |
|---|---|---|
| Hole moved to x = 20 | x = 20 | x = 20 ✓ |
| A second Ø 6 hole added at x = −10, **before** the first in the timeline. The first hole is now at x = 20 | x = **−10** | x = 20, or a warning |
| First hole moved to x = 5, a new Ø 6 hole at x = 15 | x = **15** | x = 5, or a warning |

The same change inside one design keeps the joint on the right hole: plate, hole and joint in one file, a new hole inserted before the first with the marker rolled back, then the first hole redefined to x = 20. The joint stays at x = 20, because the face names (`F3:side…`) carry the reference.

So the difference is the link. The Import feature holds the linked bodies as STEP text, the part's history-based face names are lost, and references are matched again from geometry. Where that is ambiguous (two holes of the same size), the joint silently takes the wrong one.

### Expected

References into a linked component survive an update the same way they do inside one design. A possible way: the Import feature of a linked design keeps the face (and edge) names the part design gave its bodies, next to the STEP text, and references resolve through them first. Where a name is gone, the joint reports it, as references inside a design already do.

### Steps to reproduce

Scripts (solidcraft-cli 0.16.2):

1. `solidcraft-cli run part_a.json --save plate.solidcraft`
2. `solidcraft-cli run asm.json --save asm.solidcraft` (the joint frame is at x = 10)
3. `solidcraft-cli run part_c.json --save plate.solidcraft`
4. `solidcraft-cli run upd.json --in asm.solidcraft --results`: `frame_a.origin` is [−10, 0, 5]

(attach `part_a.json`, `part_c.json`, `asm.json`, `upd.json`)

### SolidCraft version and OS

solidcraft-cli 0.16.2 (release tar.gz, linux x86_64), headless. Not checked on `main`.
