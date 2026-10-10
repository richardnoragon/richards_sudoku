# Appendix E — Serialization schema and migration rules

## Alpha evidence

Apply [alpha.md](alpha.md) alongside the requirements in this appendix.
Demonstrate save/resume and failure recovery. Track DOC-03 session restoration
and DOC-06 unsaved transitions; schema compatibility alone is insufficient.

Parent: [constitution](speckit.constitution) §2.6. Related:
[Appendix A](speckit.constitution.appendix.a.md), [migration history](MIGRATIONS.md),
[release checklist](RELEASE_CHECKLIST.md), [lifecycle](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md).

## E1. Schema versioning

Save files use the integer key `version`; the current writer emits `2`.
The application version in `pyproject.toml` is independent of the save schema.
Breaking field semantics or incompatible structures require a schema version change.
Compatible optional fields may retain the version when loader defaults and tests
are documented in MIGRATIONS.md, as implemented for `hint_limit`.

## E2. Backward compatibility

The current loader accepts versions 1 and 2. It supplies missing SE fields and
hint-limit defaults, and maps the legacy variant name `extended` to `1to25`.
Future versions and missing/invalid version fields are rejected. Future schema
changes must document which prior versions remain readable and how to recover.

## E3. Fields

The writer emits `version`, `board`, `variant_meta`, `solution`, `timer`, `stats`,
`se_score`, `se_label`, `hint_limit`, and optional `original_puzzle`. Candidate marks
are stored inside board cells; `board.codebook_hypotheses` stores player mappings. Variant layouts and constraints are stored in `variant_meta`.
[MIGRATIONS.md](MIGRATIONS.md#current-format-version-2) defines required fields and defaults.

History and theme/font preferences are outside the current save format. Kakuro
clue positions are derived on load; they are not persisted.

## E4. Migration table

| Transition | Implemented behavior |
| --- | --- |
| 1 → 2 | Missing SE score/label default to 0.0 / Unknown; next save writes version 2 |
| Compatible version 2 additions | Default hint limit 3; original-clue fallback; empty hypotheses; legacy variant rename; variant constraints |

Record every future format change in MIGRATIONS.md with its transformations,
defaults, compatibility policy, validation, and recovery steps.

## E5. Validation requirements

Loaders must reject malformed payloads and invalid board/variant metadata safely.
Current checks live in model constructors, `_validate_variant_constraints`, and
`_validate_session`; they cover ranges, dimensions, coordinates, session counters,
hypotheses, and original-clue consistency. These checks are not a complete external
JSON Schema validator or a claim that every malformed payload is covered.
Add focused regression tests whenever a validation gap is fixed.

## E6. Safe persistence

Payloads are JSON data and must never execute code or trigger external resource
loads. Use temporary sibling files and atomic replacement for saves. Preserve a
previous-save backup and document recovery. See the [user guide](USER_GUIDE.md).
