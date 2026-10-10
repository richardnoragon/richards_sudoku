# Save schema migration history

## Alpha alignment

[Alpha](alpha.md) requires understood data risks and tested recovery. Schema v2
and atomic backups support that goal. DOC-03 restoration and DOC-06 unsaved
transitions now have regression evidence. This pass adds compatible optional fields.

Reviewed against `model/schema.py`, `model/types.py`, and
`persistence/persistence.py` on 2026-09-29. This records implemented compatibility;
Updated 2026-10-01 for the compatible additions below. Policy: [Appendix E](speckit.constitution.appendix.e.md).

## Current format: version 2

The top-level version key is `version`. Writers emit integer `2`; loaders accept
versions 1 and 2. Missing, invalid, and future versions are rejected.

| Field | Contents / missing-field behavior |
| --- | --- |
| `version` | Required schema version |
| `board` | Required `Board.to_dict()` result, including cells and their candidates |
| `variant_meta` | Required `VariantMetadata.to_dict()` result, including layout and constraints |
| `solution` | Solved grid; defaults to null |
| `timer` | Required serialized elapsed-time state |
| `stats` | Required moves, hints-used, and elapsed-time state |
| `se_score` | Defaults to 0.0 |
| `se_label` | Defaults to `"Unknown"` |
| `hint_limit` | Integer allowance or null for unlimited; defaults to 3 |
| `original_puzzle` | Optional original clue grid; legacy fallback uses saved fixed cells |
| `board.codebook_hypotheses` | Optional player mappings, default empty; independent of solution codebook |

## Version 1 → 2

Version 2 adds `se_score` and `se_label`. Loading a version 1 file supplies
`0.0` and `"Unknown"` when those fields are absent. Saving the loaded state writes
version 2. Existing files are not rewritten by loading them. The original migration
date and reviewer are not recorded; this entry was reconstructed from the code.

## Compatible additions within version 2

On 2026-10-01, `original_puzzle` and `board.codebook_hypotheses` were added with
legacy defaults. Older applications may ignore these fields and lose the new
state on re-save; keep a backup before moving a session between app revisions.

- `hint_limit` was added with a default of 3 and no version bump.
- Legacy variant string `"extended"` is mapped to `"1to25"` by both
  `Board.from_dict()` and `VariantMetadata.from_dict()`.
- Variant fields live in `variant_meta.constraints`: Str8ts masks/givens,
  Killer cages, Codewords mappings, KenKen arithmetic cages, and Kakuro runs.
- Jigsaw's `region_layout` remains a field of `variant_meta`.
- Kakuro `clue_positions` is omitted from serialized constraints and rebuilt from
  `clues` during loading. Run dictionaries use `cells`, `sum`, and `dir`.
- KenKen serialized operators are `+`, `-`, `*`, `/`; single-cell cages use `+`.

## Session restoration limits

Undo/redo history and theme/font preferences are not saved. The controller resumes
the timer only for unfinished games and clears history. Saved candidates are
preserved exactly; remaining hints are `max(0, hint_limit - stats.hints_used)`, or
unlimited when the limit is null. Value edits recompute candidates. Failed saves
preserve timer state and do not change the active save path or clean-state marker.

## Validation and recovery

`tests/test_persistence.py` and the variant suites cover round-trips, defaults,
legacy names, and malformed metadata. These checks are not a complete external
JSON Schema validator. Further input-hardening requirements remain subject to review.

An overwrite copies the previous file to `<filename>.bak` before atomic replacement.
Recovery uses a copy of that file or `restore_backup(path)`. There is no reverse
migration utility; retain old files before upgrading. For future migrations record
added/removed fields, defaults, transformations, compatibility, tests, and recovery.
