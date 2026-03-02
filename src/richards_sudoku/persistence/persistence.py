"""Versioned JSON persistence for Richards Sudoku.

Save format (schema version 1)
-------------------------------
{
  "version": 1,
  "board": { ... Board.to_dict() ... },
  "variant_meta": { ... VariantMetadata.to_dict() ... },
  "solution": [[int|null, ...], ...],   // null-free row-major Grid or null
  "timer": { "elapsed_seconds": float, "is_running": bool },
  "stats": { "moves": int, "hints_used": int, "elapsed_seconds": float }
}

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
    """

    __slots__ = ("board", "variant_meta", "solution", "timer", "stats")

    def __init__(
        self,
        board: Board,
        variant_meta: VariantMetadata,
        solution: Grid | None,
        timer: GameTimer,
        stats: GameStats,
    ) -> None:
        self.board = board
        self.variant_meta = variant_meta
        self.solution = solution
        self.timer = timer
        self.stats = stats


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
        }
    )


def _deserialize(data: dict[str, Any]) -> SaveState:
    check_version(data)  # raises ValueError on bad/future version
    board = Board.from_dict(data["board"])
    variant_meta = VariantMetadata.from_dict(data["variant_meta"])
    solution = data.get("solution")
    timer = GameTimer.from_dict(data["timer"])
    stats = GameStats.from_dict(data["stats"])
    return SaveState(
        board=board,
        variant_meta=variant_meta,
        solution=solution,
        timer=timer,
        stats=stats,
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
        raise ValueError(f"Malformed save file '{src}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Save file '{src}' must contain a JSON object.")

    return _deserialize(data)
