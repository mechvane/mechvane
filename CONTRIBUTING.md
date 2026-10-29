# Contributing

Coding agents: see [AGENTS.md](AGENTS.md).

Mechvane is an early-stage project. Bug reports, practice tests on real parts and sourced
standard values help most.

## Reporting bugs

- A short script that shows the bug (Python via `mechvane`, or a command list for
  `solidcraft-cli`), with expected and actual result.
- If the bug is in SolidCraft itself, please report it there
  ([tangency-labs/solidcraft](https://github.com/tangency-labs/solidcraft/issues)) and link
  it here.

## Code

- Python ≥ 3.11, no dependencies beyond `mcp`. Code and comments in English; docs are
  mostly German, English contributions are just as welcome.
- Every change comes with a check in `tests/mechvane/check.py`, and all checks pass
  (`python3 tests/mechvane/check.py`, `python3 tests/reference/check.py`). Do not weaken
  checks to get to green.
- Larger decisions as an ADR under `docs/adr/`.

## Standard values and design rules

Entries in the knowledge catalog (`katalog/eintraege/`, schema `katalog/schema.json`) need
a freely accessible source with a verbatim quote. `python3 tools/check_sources.py
<note.md>` checks that quotes and numbers really appear in the source. Do not copy values
from paid standards documents.

## License

Contributions are licensed under MIT OR Apache-2.0 like the project. No GPL/AGPL code and
no code or models from proprietary CAD systems.
