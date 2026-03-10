"""Versioned JSON persistence for Richards Sudoku.

Save format (schema version 2)
-------------------------------
{
  "version": 2,
  "board": { ... Board.to_dict() ... },
  "variant_meta": { ... VariantMetadata.to_dict() ... },
  "solution": [[int|null, ...], ...],   // null-free row-major Grid or null
  "timer": { "elapsed_seconds": float, "is_running": bool },
  "stats": { "moves": int, "hints_used": int, "elapsed_seconds": float },
  "se_score": float,                    // SE difficulty score (0.0 = unrated)
  "se_label": str                       // SE difficulty label ("Unknown" = unrated)
}

Schema version 1 files (no se_score/se_label) are loaded with defaults
(0.0, "Unknown") and will be re-saved as version 2 on next save.

Atomic write strategy: write to a sibling *.tmp file then rename, so a
crash cannot corrupt an existing save.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from richards_sudoku.model.schema import CURRENT_SCHEMA_VERSION, add_version, check_version
from richards_sudoku.model.types import Board, Variant, VariantMetadata
from richards_sudoku.services.stats import GameStats
from richards_sudoku.services.timer import GameTimer
from richards_sudoku.solver.solver import Grid


# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------

class PersistenceError(ValueError):
    """Raised when a save file is structurally valid JSON but contains
    semantically invalid game state (bad region layout, cage overlap, etc.)."""


# ---------------------------------------------------------------------------
# Public data container
# ---------------------------------------------------------------------------

class SaveState:
    """All game state needed to fully restore a session.

    Attributes:
        board:        Current board (user edits + fixed clues).
        variant_meta: Variant rules / layout.
        solution:     Full solved grid, used for hints (may be None for
                      externally imported puzzles without a known solution).
        timer:        Elapsed-time state (always loaded in paused form).
        stats:        Move/hint counters.
        hint_limit:   Maximum hints allowed (None = unlimited, default 3).
    """

    __slots__ = ("board", "variant_meta", "solution", "timer", "stats", "se_score", "se_label", "hint_limit")

    def __init__(
        self,
        board: Board,
        variant_meta: VariantMetadata,
        solution: Grid | None,
        timer: GameTimer,
        stats: GameStats,
        se_score: float = 0.0,
        se_label: str = "Unknown",
        hint_limit: int | None = 3,
    ) -> None:
        self.board = board
        self.variant_meta = variant_meta
        self.solution = solution
        self.timer = timer
        self.stats = stats
        self.se_score = se_score
        self.se_label = se_label
        self.hint_limit = hint_limit


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _serialize(state: SaveState) -> dict[str, Any]:
    return add_version(
        {
            "board": state.board.to_dict(),
            "variant_meta": state.variant_meta.to_dict(),
            "solution": state.solution,
            "timer": state.timer.to_dict(),
            "stats": state.stats.to_dict(),
            "se_score": state.se_score,
            "se_label": state.se_label,
            "hint_limit": state.hint_limit,
        }
    )


def _validate_variant_constraints(meta: VariantMetadata) -> None:  # noqa: C901
    """Raise ValueError if variant-specific constraints in *meta* are invalid."""
    variant = meta.name
    size = meta.size
    constraints = meta.constraints or {}

    if variant == Variant.JIGSAW:
        layout = meta.region_layout
        counts: dict[int, int] = {}
        for row in layout:
            for region_id in row:
                counts[region_id] = counts.get(region_id, 0) + 1
        if len(counts) != size:
            raise ValueError(
                f"Jigsaw region_layout has {len(counts)} distinct regions; expected {size}."
            )
        for region_id, count in counts.items():
            if count != size:
                raise ValueError(
                    f"Jigsaw region {region_id} has {count} cells; expected {size}."
                )

    elif variant == Variant.STR8TS:
        black_cells = constraints.get("black_cells", [])
        seen_bc: set[tuple[int, int]] = set()
        for entry in black_cells:
            if (
                not isinstance(entry, (list, tuple))
                or len(entry) != 2
                or not all(isinstance(v, int) for v in entry)
            ):
                raise ValueError(f"black_cells entry {entry!r} is not a valid [row, col] pair.")
            key = (int(entry[0]), int(entry[1]))
            if key in seen_bc:
                raise ValueError(f"Duplicate black_cell at {list(key)}.")
            seen_bc.add(key)
        black_givens = constraints.get("black_givens", [])
        seen_bg: set[tuple[int, int]] = set()
        for entry in black_givens:
            if (
                not isinstance(entry, (list, tuple))
                or len(entry) != 3
                or not all(isinstance(v, int) for v in entry)
            ):
                raise ValueError(
                    f"black_givens entry {entry!r} is not a valid [row, col, value] triple."
                )
            key = (int(entry[0]), int(entry[1]))
            if key in seen_bg:
                raise ValueError(f"Duplicate black_given at {list(key)}.")
            seen_bg.add(key)

    elif variant == Variant.KILLER:
        cages = constraints.get("cages", [])
        if not cages:
            raise ValueError("Killer variant requires a non-empty 'cages' list.")
        covered: set[tuple[int, int]] = set()
        for i, cage in enumerate(cages):
            if not isinstance(cage, dict) or "cells" not in cage or "sum" not in cage:
                raise ValueError(f"Cage {i} is missing 'cells' or 'sum' key.")
            for entry in cage["cells"]:
                if (
                    not isinstance(entry, (list, tuple))
                    or len(entry) != 2
                    or not all(isinstance(v, int) for v in entry)
                ):
                    raise ValueError(f"Cage {i} cell {entry!r} is not a valid [row, col] pair.")
                key = (int(entry[0]), int(entry[1]))
                if key in covered:
                    raise ValueError(
                        f"Killer cage overlap: cell {list(key)} appears in multiple cages."
                    )
                covered.add(key)
        expected = size * size
        if len(covered) != expected:
            raise ValueError(
                f"Killer cages cover {len(covered)} cells; expected {expected}."
            )

    elif variant == Variant.CODEWORDS:
        codebook = constraints.get("codebook", {})
        if not codebook:
            raise ValueError("Codewords variant requires a non-empty 'codebook' mapping.")
        valid_letters = set("ABCDEFGHI")
        valid_digits = set(range(1, 10))
        if set(codebook.keys()) != valid_letters:
            raise ValueError(
                f"Codewords codebook must map exactly letters A–I; got keys {sorted(codebook.keys())!r}."
            )
        if set(codebook.values()) != valid_digits:
            raise ValueError(
                f"Codewords codebook must map bijectively to digits 1–9; got values {sorted(codebook.values())!r}."
            )
        given_mappings = constraints.get("given_mappings", {})
        for letter, digit in given_mappings.items():
            if letter not in valid_letters:
                raise ValueError(f"given_mappings contains invalid letter {letter!r}.")
            if codebook.get(letter) != digit:
                raise ValueError(
                    f"given_mappings entry {letter}={digit} contradicts codebook ({letter}={codebook.get(letter)})."
                )

    elif variant == Variant.KENKEN:
        cages = constraints.get("cages", [])
        if not cages:
            raise ValueError("KenKen variant requires a non-empty 'cages' list.")
        valid_ops = {"+", "-", "*", "/"}
        kk_covered: set[tuple[int, int]] = set()
        for i, cage in enumerate(cages):
            if (
                not isinstance(cage, dict)
                or "cells" not in cage
                or "op" not in cage
                or "target" not in cage
            ):
                raise ValueError(
                    f"KenKen cage {i} is missing 'cells', 'op', or 'target' key."
                )
            op = cage.get("op")
            if op not in valid_ops:
                raise ValueError(
                    f"KenKen cage {i} op must be one of {sorted(valid_ops)!r}; got {op!r}."
                )
            for entry in cage["cells"]:
                if (
                    not isinstance(entry, (list, tuple))
                    or len(entry) != 2
                    or not all(isinstance(v, int) for v in entry)
                ):
                    raise ValueError(
                        f"KenKen cage {i} cell {entry!r} is not a valid [row, col] pair."
                    )
                key = (int(entry[0]), int(entry[1]))
                if key in kk_covered:
                    raise ValueError(
                        f"KenKen cage overlap: cell {list(key)} appears in multiple cages."
                    )
                kk_covered.add(key)
        expected = size * size
        if len(kk_covered) != expected:
            raise ValueError(
                f"KenKen cages cover {len(kk_covered)} cells; expected {expected}."
            )

    elif variant == Variant.KAKURO:
        from richards_sudoku.solver.variant_generators import build_kakuro_clue_positions  # noqa: PLC0415
        clues = constraints.get("clues", [])
        black_cells = constraints.get("black_cells", [])
        if not clues:
            raise ValueError("Kakuro variant requires a non-empty 'clues' list.")
        if not black_cells:
            raise ValueError("Kakuro variant requires a non-empty 'black_cells' list.")
        valid_dirs = {"across", "down"}
        across_covered: set[tuple[int, int]] = set()
        down_covered: set[tuple[int, int]] = set()
        for i, run in enumerate(clues):
            if (
                not isinstance(run, dict)
                or "cells" not in run
                or "sum" not in run
                or "dir" not in run
            ):
                raise ValueError(
                    f"Kakuro clue {i} is missing 'cells', 'sum', or 'dir' key."
                )
            direction = run.get("dir")
            if direction not in valid_dirs:
                raise ValueError(
                    f"Kakuro clue {i} dir must be 'across' or 'down'; got {direction!r}."
                )
            cells_i = run["cells"]
            if not isinstance(cells_i, list) or len(cells_i) < 2:
                raise ValueError(
                    f"Kakuro clue {i} must have at least 2 cells; got {len(cells_i) if isinstance(cells_i, list) else 0}."
                )
            covered = across_covered if direction == "across" else down_covered
            for entry in cells_i:
                if (
                    not isinstance(entry, (list, tuple))
                    or len(entry) != 2
                    or not all(isinstance(v, int) for v in entry)
                ):
                    raise ValueError(
                        f"Kakuro clue {i} cell {entry!r} is not a valid [row, col] pair."
                    )
                key = (int(entry[0]), int(entry[1]))
                if key in covered:
                    raise ValueError(
                        f"Kakuro clue {i} ({direction}): cell {list(key)} appears in multiple {direction} runs."
                    )
                covered.add(key)
        if across_covered != down_covered:
            only_across = across_covered - down_covered
            only_down = down_covered - across_covered
            if only_across:
                raise ValueError(
                    f"Kakuro cells in across runs but not down runs: {sorted(only_across)}."
                )
            if only_down:
                raise ValueError(
                    f"Kakuro cells in down runs but not across runs: {sorted(only_down)}."
                )
        # Rebuild clue_positions at load time (not persisted since dicts need tuple keys)
        meta.constraints["clue_positions"] = build_kakuro_clue_positions(clues)


def _deserialize(data: dict[str, Any]) -> SaveState:
    check_version(data)  # raises ValueError on bad/future version
    board = Board.from_dict(data["board"])
    variant_meta = VariantMetadata.from_dict(data["variant_meta"])
    _validate_variant_constraints(variant_meta)
    solution = data.get("solution")
    timer = GameTimer.from_dict(data["timer"])
    stats = GameStats.from_dict(data["stats"])
    # se_score/se_label absent in v1 files — default to "unrated" sentinel
    se_score: float = data.get("se_score", 0.0)
    se_label: str = data.get("se_label", "Unknown")
    hint_limit: int | None = data.get("hint_limit", 3)
    return SaveState(
        board=board,
        variant_meta=variant_meta,
        solution=solution,
        timer=timer,
        stats=stats,
        se_score=se_score,
        se_label=se_label,
        hint_limit=hint_limit,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save(state: SaveState, path: str | os.PathLike) -> None:
    """Serialise *state* to *path* as UTF-8 JSON using an atomic write.

    The file is written to a temporary sibling first; the rename is
    atomic on POSIX and best-effort atomic on Windows (os.replace).
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_serialize(state), indent=2, ensure_ascii=False)

    # Write to a temp file in the same directory so the rename stays on one
    # filesystem (required for atomicity on most OSes).
    fd, tmp_path = tempfile.mkstemp(dir=dest.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_path, dest)  # atomic on POSIX; best-effort on Windows
    except Exception:
        # Clean up the temp file if anything goes wrong before the rename.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load(path: str | os.PathLike) -> SaveState:
    """Load and deserialise a save file from *path*.

    Raises:
        FileNotFoundError: if the file does not exist.
        ValueError:        if the JSON is malformed or the schema version
                           is missing, invalid, or newer than supported.
    """
    src = Path(path)
    with src.open("r", encoding="utf-8") as fh:
        raw = fh.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PersistenceError(f"Malformed save file '{src}': {exc}") from exc

    if not isinstance(data, dict):
        raise PersistenceError(f"Save file '{src}' must contain a JSON object.")

    try:
        return _deserialize(data)
    except ValueError as exc:
        raise PersistenceError(str(exc)) from exc
