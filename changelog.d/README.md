# Changelog Snippets

Branches add a snippet file here instead of editing `CHANGELOG.md` directly.
This prevents merge conflicts between parallel branches.

## Filename

Name your snippet file after your issue or feature branch:
`changelog.d/<issue>.md` (e.g. `changelog.d/75.md`).

## Format

The first line must be one of the Keep a Changelog categories:
`Added`, `Changed`, `Fixed`, or `Removed`.

Subsequent lines contain the entries as a Markdown bullet list, in English, written from a user's perspective.

### Example

`changelog.d/75.md`:

```markdown
Added
- Model browser inline rename (F2): select a feature or sketch in the model tree and press F2 to edit its name inline.
```

If your change spans multiple categories, you can use multiple category headings:

```markdown
Added
- Revolve tool shortcut R outside sketcher.

Fixed
- Sketch trim loose end handling.
```

## Release

At release time, `tools/changelog_build.py --release X.Y.Z` merges all snippets into `CHANGELOG.md` under the release version with the current date and deletes the snippet files.
