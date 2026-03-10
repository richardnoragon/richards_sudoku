"""Tests for persistence: save/load round-trips, atomic write, error handling."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from richards_sudoku.model.types import Board, Cell, Move, Variant, VariantMetadata
from richards_sudoku.persistence import PersistenceError, SaveState, load, save
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
        assert data["version"] == 2

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


# ---------------------------------------------------------------------------
# E5: hint_limit round-trips
# ---------------------------------------------------------------------------

def _make_state(board, meta, timer, stats, **kw) -> SaveState:
    return SaveState(board=board, variant_meta=meta, solution=None, timer=timer, stats=stats, **kw)


class TestHintLimit:

    def test_hint_limit_none_round_trips(self, tmp_path, board, meta, timer, stats):
        state = _make_state(board, meta, timer, stats, hint_limit=None)
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.hint_limit is None

    def test_hint_limit_5_round_trips(self, tmp_path, board, meta, timer, stats):
        state = _make_state(board, meta, timer, stats, hint_limit=5)
        dest = tmp_path / "game.json"
        save(state, dest)
        restored = load(dest)
        assert restored.hint_limit == 5

    def test_v2_save_without_hint_limit_defaults_to_3(self, tmp_path, state):
        dest = tmp_path / "game.json"
        save(state, dest)
        data = json.loads(dest.read_text(encoding="utf-8"))
        del data["hint_limit"]
        dest.write_text(json.dumps(data), encoding="utf-8")
        restored = load(dest)
        assert restored.hint_limit == 3


# ---------------------------------------------------------------------------
# E5: Jigsaw constraint round-trip and validation
# ---------------------------------------------------------------------------

def _jigsaw_region_layout() -> list[list[int]]:
    """Standard 3×3 box layout encoded as region IDs 0–8."""
    return [[3 * (r // 3) + (c // 3) for c in range(9)] for r in range(9)]


def _jigsaw_meta() -> VariantMetadata:
    return VariantMetadata(
        name=Variant.JIGSAW,
        size=9,
        symbols=list(range(1, 10)),
        region_layout=_jigsaw_region_layout(),
        constraints={},
    )


class TestJigsawConstraintRoundTrip:

    def test_jigsaw_region_layout_round_trips(self, tmp_path, board, timer, stats):
        meta = _jigsaw_meta()
        board_j = Board(size=9, variant=Variant.JIGSAW)
        state = _make_state(board_j, meta, timer, stats)
        dest = tmp_path / "jigsaw.json"
        save(state, dest)
        restored = load(dest)
        assert restored.variant_meta.region_layout == _jigsaw_region_layout()

    def test_jigsaw_bad_region_count_raises_persistence_error(self, tmp_path, board, timer, stats):
        # Corrupt the layout so all cells belong to region 0
        bad_layout = [[0] * 9 for _ in range(9)]
        meta = VariantMetadata(
            name=Variant.JIGSAW, size=9, symbols=list(range(1, 10)),
            region_layout=bad_layout, constraints={},
        )
        board_j = Board(size=9, variant=Variant.JIGSAW)
        state = _make_state(board_j, meta, timer, stats)
        dest = tmp_path / "bad_jigsaw.json"
        save(state, dest)
        with pytest.raises(PersistenceError, match="distinct regions"):
            load(dest)

    def test_jigsaw_bad_region_size_raises_persistence_error(self, tmp_path, timer, stats):
        # Layout where region 0 has 10 cells and region 8 has 8 cells
        layout = _jigsaw_region_layout()
        # Swap one cell from region 8 to region 0
        layout[8][8] = 0  # was 8, now 0 → region 0 has 10, region 8 has 8
        meta = VariantMetadata(
            name=Variant.JIGSAW, size=9, symbols=list(range(1, 10)),
            region_layout=layout, constraints={},
        )
        board_j = Board(size=9, variant=Variant.JIGSAW)
        state = _make_state(board_j, meta, timer, stats)
        dest = tmp_path / "bad_size.json"
        save(state, dest)
        with pytest.raises(PersistenceError):
            load(dest)


# ---------------------------------------------------------------------------
# E5: Str8ts constraint round-trip and validation
# ---------------------------------------------------------------------------

def _str8ts_meta(black_cells=None, black_givens=None) -> VariantMetadata:
    return VariantMetadata(
        name=Variant.STR8TS,
        size=9,
        symbols=list(range(1, 10)),
        region_layout=_jigsaw_region_layout(),
        constraints={
            "black_cells": black_cells or [],
            "black_givens": black_givens or [],
        },
    )


class TestStr8tsConstraintRoundTrip:

    def test_str8ts_black_cells_round_trips(self, tmp_path, timer, stats):
        blacks = [[0, 4], [3, 3], [8, 0]]
        meta = _str8ts_meta(black_cells=blacks)
        board_s = Board(size=9, variant=Variant.STR8TS)
        state = _make_state(board_s, meta, timer, stats)
        dest = tmp_path / "str8ts.json"
        save(state, dest)
        restored = load(dest)
        loaded_blacks = restored.variant_meta.constraints["black_cells"]
        assert [list(b) for b in loaded_blacks] == blacks

    def test_str8ts_black_givens_round_trips(self, tmp_path, timer, stats):
        givens = [[0, 4, 7], [3, 3, 2]]
        meta = _str8ts_meta(black_givens=givens)
        board_s = Board(size=9, variant=Variant.STR8TS)
        state = _make_state(board_s, meta, timer, stats)
        dest = tmp_path / "str8ts_givens.json"
        save(state, dest)
        restored = load(dest)
        loaded_givens = restored.variant_meta.constraints["black_givens"]
        assert [list(g) for g in loaded_givens] == givens

    def test_str8ts_duplicate_black_cell_raises_persistence_error(self, tmp_path, timer, stats):
        meta = _str8ts_meta(black_cells=[[0, 4], [0, 4]])
        board_s = Board(size=9, variant=Variant.STR8TS)
        state = _make_state(board_s, meta, timer, stats)
        dest = tmp_path / "dup_blacks.json"
        save(state, dest)
        with pytest.raises(PersistenceError, match="Duplicate black_cell"):
            load(dest)

    def test_str8ts_duplicate_black_given_raises_persistence_error(self, tmp_path, timer, stats):
        meta = _str8ts_meta(black_givens=[[1, 2, 5], [1, 2, 3]])
        board_s = Board(size=9, variant=Variant.STR8TS)
        state = _make_state(board_s, meta, timer, stats)
        dest = tmp_path / "dup_givens.json"
        save(state, dest)
        with pytest.raises(PersistenceError, match="Duplicate black_given"):
            load(dest)


# ---------------------------------------------------------------------------
# E5: Killer constraint round-trip and validation
# ---------------------------------------------------------------------------

def _killer_meta(cages: list[dict]) -> VariantMetadata:
    return VariantMetadata(
        name=Variant.KILLER,
        size=9,
        symbols=list(range(1, 10)),
        region_layout=_jigsaw_region_layout(),
        constraints={"cages": cages},
    )


def _full_single_cell_cages() -> list[dict]:
    """81 single-cell cages covering every cell."""
    return [{"cells": [[r, c]], "sum": 5} for r in range(9) for c in range(9)]


class TestKillerConstraintRoundTrip:

    def test_killer_cages_round_trips(self, tmp_path, timer, stats):
        cages = _full_single_cell_cages()
        meta = _killer_meta(cages)
        board_k = Board(size=9, variant=Variant.KILLER)
        state = _make_state(board_k, meta, timer, stats)
        dest = tmp_path / "killer.json"
        save(state, dest)
        restored = load(dest)
        loaded_cages = restored.variant_meta.constraints["cages"]
        assert len(loaded_cages) == 81

    def test_killer_cage_overlap_raises_persistence_error(self, tmp_path, timer, stats):
        cages = _full_single_cell_cages()
        # Duplicate cell (0,0) by adding it to a second cage
        cages.append({"cells": [[0, 0]], "sum": 3})
        meta = _killer_meta(cages)
        board_k = Board(size=9, variant=Variant.KILLER)
        state = _make_state(board_k, meta, timer, stats)
        dest = tmp_path / "overlap.json"
        save(state, dest)
        with pytest.raises(PersistenceError, match="overlap"):
            load(dest)

    def test_killer_incomplete_coverage_raises_persistence_error(self, tmp_path, timer, stats):
        # Leave out cell (8,8) → only 80 cells covered
        cages = [{"cells": [[r, c]], "sum": 5}
                 for r in range(9) for c in range(9)
                 if not (r == 8 and c == 8)]
        meta = _killer_meta(cages)
        board_k = Board(size=9, variant=Variant.KILLER)
        state = _make_state(board_k, meta, timer, stats)
        dest = tmp_path / "incomplete.json"
        save(state, dest)
        with pytest.raises(PersistenceError, match="cover"):
            load(dest)

