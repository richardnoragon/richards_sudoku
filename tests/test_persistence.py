"""Tests for persistence: save/load round-trips, atomic write, error handling."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from richards_sudoku.model.types import Board, Cell, Move, Variant, VariantMetadata
from richards_sudoku.persistence import SaveState, load, save
from richards_sudoku.services.stats import GameStats
from richards_sudoku.services.timer import GameTimer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def meta() -> VariantMetadata:
    return VariantMetadata.standard_9x9()


@pytest.fixture()
def board(meta: VariantMetadata) -> Board:
    b = Board(size=9, variant=Variant.STANDARD)
    # Fix a few clues
    b.cell(0, 0).value = 5
    b.cell(0, 0).is_fixed = True
    b.cell(1, 1).value = 3
    b.cell(1, 1).is_fixed = True
    # Add a candidate set on an empty cell
    b.cell(4, 4).candidates = {1, 2, 7}
    return b


@pytest.fixture()
def solution() -> list[list[int | None]]:
    # A minimal placeholder solution grid (9×9 filled with 1s for fixture simplicity)
    return [[((r + c) % 9) + 1 for c in range(9)] for r in range(9)]


@pytest.fixture()
def timer() -> GameTimer:
    t = GameTimer()
    t._accumulated = 42.5  # inject elapsed directly to avoid real-time dependency
    return t


@pytest.fixture()
def stats() -> GameStats:
    return GameStats(moves=7, hints_used=2, elapsed_seconds=42.5)


@pytest.fixture()
def state(board, meta, solution, timer, stats) -> SaveState:
    return SaveState(
        board=board,
        variant_meta=meta,
        solution=solution,
        timer=timer,
        stats=stats,
    )


# ---------------------------------------------------------------------------
# Round-trip: full fidelity
# ---------------------------------------------------------------------------

class TestRoundTrip:

    def test_save_creates_file(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        assert dest.exists()

    def test_file_is_valid_json(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        data = json.loads(dest.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_version_field_present(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        data = json.loads(dest.read_text(encoding="utf-8"))
        assert data["version"] == 1

    def test_board_values_preserved(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.board.cell(0, 0).value == 5
        assert restored.board.cell(0, 0).is_fixed is True
        assert restored.board.cell(1, 1).value == 3

    def test_candidate_set_preserved(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.board.cell(4, 4).candidates == {1, 2, 7}

    def test_empty_cells_preserved(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.board.cell(8, 8).value is None
        assert restored.board.cell(8, 8).is_fixed is False

    def test_variant_meta_preserved(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.variant_meta.name == Variant.STANDARD
        assert restored.variant_meta.size == 9
        assert restored.variant_meta.symbols == list(range(1, 10))

    def test_region_layout_preserved(self, tmp_path, state, meta):
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.variant_meta.region_layout == meta.region_layout

    def test_solution_preserved(self, tmp_path, state, solution):
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.solution == solution

    def test_solution_none_preserved(self, tmp_path, board, meta, timer, stats):
        state_no_sol = SaveState(board=board, variant_meta=meta, solution=None,
                                 timer=timer, stats=stats)
        dest = tmp_path / "game.json"
        save(state_no_sol, dest)
        restored = load(dest)
        assert restored.solution is None

    def test_timer_elapsed_preserved(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.timer.elapsed_seconds() == pytest.approx(42.5)

    def test_timer_always_paused_on_load(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert not restored.timer.is_running

    def test_stats_preserved(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.stats.moves == 7
        assert restored.stats.hints_used == 2
        assert restored.stats.elapsed_seconds == pytest.approx(42.5)

    def test_board_size_preserved(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.board.size == 9

    def test_double_save_overwrites(self, tmp_path, state, board, meta, timer, stats):
        dest = tmp_path / "game.json"
        save(state, dest)
        # Save a different state to same path
        board2 = Board(size=9, variant=Variant.STANDARD)
        board2.cell(0, 0).value = 9
        state2 = SaveState(board=board2, variant_meta=meta, solution=None,
                           timer=timer, stats=stats)
        save(state2, dest)
        restored = load(dest)
        assert restored.board.cell(0, 0).value == 9


# ---------------------------------------------------------------------------
# Atomic write behaviour
# ---------------------------------------------------------------------------

class TestAtomicWrite:

    def test_no_tmp_file_left_behind(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []

    def test_save_creates_parent_dirs(self, tmp_path, state):
        dest = tmp_path / "sub" / "dir" / "game.json"
        save(state, dest)
        assert dest.exists()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestLoadErrors:

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load(tmp_path / "nonexistent.json")

    def test_malformed_json_raises_value_error(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ValueError, match="Malformed save file"):
            load(bad)

    def test_json_array_raises_value_error(self, tmp_path):
        bad = tmp_path / "array.json"
        bad.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(ValueError, match="JSON object"):
            load(bad)

    def test_missing_version_raises_value_error(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        data = json.loads(dest.read_text(encoding="utf-8"))
        del data["version"]
        dest.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="Missing 'version'"):
            load(dest)

    def test_future_version_raises_value_error(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        data = json.loads(dest.read_text(encoding="utf-8"))
        data["version"] = 9999
        dest.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="newer than supported"):
            load(dest)

    def test_invalid_version_type_raises_value_error(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        data = json.loads(dest.read_text(encoding="utf-8"))
        data["version"] = "one"
        dest.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid schema version"):
            load(dest)


# ---------------------------------------------------------------------------
# Path types: str and Path both accepted
# ---------------------------------------------------------------------------

class TestPathTypes:

    def test_save_and_load_with_string_path(self, tmp_path, state):
        dest = str(tmp_path / "game.json")
        save(state, dest)
        restored = load(dest)
        assert restored.board.cell(0, 0).value == 5

    def test_save_and_load_with_path_object(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.board.cell(0, 0).value == 5
