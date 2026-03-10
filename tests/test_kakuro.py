"""Tests for the Kakuro variant implementation (Batch N tasks N1-N9)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from richards_sudoku.model.types import Board, Cell, Variant, VariantMetadata
from richards_sudoku.services.difficulty_se import (
    _KakuroRun,
    _WorkingGrid,
    _kakuro_can_reach,
    _kakuro_run_step,
)
from richards_sudoku.services.text_format import export_text, import_text
from richards_sudoku.solver.variant_generators import (
    KakuroFillGenerator,
    KakuroTemplateLibrary,
    build_kakuro_clue_positions,
)


# ---------------------------------------------------------------------------
# Shared helpers / fixtures
# ---------------------------------------------------------------------------

def _box_layout(size: int = 9) -> list[list[int]]:
    sq = int(size ** 0.5)
    return [[(r // sq) * sq + (c // sq) for c in range(size)] for r in range(size)]


def _kakuro_meta_minimal() -> VariantMetadata:
    """4×4 Kakuro meta with a 3×3 interior white region.

    Layout (B = black, . = white):
        B B B B
        B . . .
        B . . .
        B . . .
    Across runs: row 1, 2, 3 each cells 1-3.
    Down runs:   col 1, 2, 3 each cells row 1-3.
    """
    size = 4
    clues = [
        {"cells": [[1, 1], [1, 2], [1, 3]], "sum": 6,  "dir": "across"},
        {"cells": [[2, 1], [2, 2], [2, 3]], "sum": 15, "dir": "across"},
        {"cells": [[3, 1], [3, 2], [3, 3]], "sum": 24, "dir": "across"},
        {"cells": [[1, 1], [2, 1], [3, 1]], "sum": 12, "dir": "down"},
        {"cells": [[1, 2], [2, 2], [3, 2]], "sum": 15, "dir": "down"},
        {"cells": [[1, 3], [2, 3], [3, 3]], "sum": 18, "dir": "down"},
    ]
    black_cells = [[0, 0], [0, 1], [0, 2], [0, 3], [1, 0], [2, 0], [3, 0]]
    clue_positions = build_kakuro_clue_positions(clues)
    return VariantMetadata(
        name=Variant.KAKURO,
        size=size,
        symbols=list(range(1, 10)),
        region_layout=_box_layout(size),
        constraints={
            "clues": clues,
            "black_cells": black_cells,
            "clue_positions": clue_positions,
        },
    )


def _kakuro_board_minimal() -> Board:
    """Empty kakuro board matching _kakuro_meta_minimal (black cells marked)."""
    size = 4
    board = Board(size=size, variant=Variant.KAKURO)
    black_set = {(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (3, 0)}
    for r, c in black_set:
        board.cell(r, c).is_black = True
        board.cell(r, c).candidates = set()
    return board


def _small_template() -> dict:
    """A hand-built 4×4 Kakuro template (no sums yet, just structure)."""
    return {
        "size": 4,
        "black_cells": [[0, 0], [0, 1], [0, 2], [0, 3], [1, 0], [2, 0], [3, 0]],
        "runs": [
            {"cells": [[1, 1], [1, 2], [1, 3]], "dir": "across"},
            {"cells": [[2, 1], [2, 2], [2, 3]], "dir": "across"},
            {"cells": [[3, 1], [3, 2], [3, 3]], "dir": "across"},
            {"cells": [[1, 1], [2, 1], [3, 1]], "dir": "down"},
            {"cells": [[1, 2], [2, 2], [3, 2]], "dir": "down"},
            {"cells": [[1, 3], [2, 3], [3, 3]], "dir": "down"},
        ],
    }


# ---------------------------------------------------------------------------
# N1 — KakuroFillGenerator
# ---------------------------------------------------------------------------

class TestKakuroFillGenerator:

    def test_fill_returns_non_none(self):
        tmpl = _small_template()
        gen = KakuroFillGenerator(tmpl, seed=0)
        filled = gen.fill()
        assert filled is not None

    def test_fill_across_runs_no_repeat(self):
        tmpl = _small_template()
        gen = KakuroFillGenerator(tmpl, seed=0)
        filled = gen.fill()
        assert filled is not None
        for run in tmpl["runs"]:
            if run["dir"] != "across":
                continue
            vals = [filled[r][c] for r, c in run["cells"]]
            assert len(set(vals)) == len(vals), f"Repeat in across run {run['cells']}: {vals}"

    def test_fill_down_runs_no_repeat(self):
        tmpl = _small_template()
        gen = KakuroFillGenerator(tmpl, seed=0)
        filled = gen.fill()
        assert filled is not None
        for run in tmpl["runs"]:
            if run["dir"] != "down":
                continue
            vals = [filled[r][c] for r, c in run["cells"]]
            assert len(set(vals)) == len(vals), f"Repeat in down run {run['cells']}: {vals}"

    def test_fill_uses_digits_1_to_9(self):
        tmpl = _small_template()
        gen = KakuroFillGenerator(tmpl, seed=0)
        filled = gen.fill()
        assert filled is not None
        black_set = {(int(r), int(c)) for r, c in tmpl["black_cells"]}
        for r in range(4):
            for c in range(4):
                if (r, c) not in black_set:
                    assert filled[r][c] is not None
                    assert 1 <= filled[r][c] <= 9

    def test_fill_different_seeds_may_differ(self):
        tmpl = _small_template()
        filled_a = KakuroFillGenerator(tmpl, seed=1).fill()
        filled_b = KakuroFillGenerator(tmpl, seed=999).fill()
        assert filled_a is not None
        assert filled_b is not None
        # At least a chance they differ (not a hard requirement, just sanity check)
        same = all(
            filled_a[r][c] == filled_b[r][c]
            for r in range(4) for c in range(4)
        )
        # We can't assert they must differ; just check both are valid
        for grid in (filled_a, filled_b):
            for run in tmpl["runs"]:
                vals = [grid[r][c] for r, c in run["cells"]]
                assert len(set(vals)) == len(vals)

    def test_fill_cancellable(self):
        tmpl = _small_template()
        gen = KakuroFillGenerator(tmpl, seed=0)
        cancel = [True]  # pre-cancelled
        result = gen.fill(cancel_flag=cancel)
        assert result is None


# ---------------------------------------------------------------------------
# N1 — KakuroTemplateLibrary
# ---------------------------------------------------------------------------

class TestKakuroTemplateLibrary:

    def test_generate_returns_dict(self):
        lib = KakuroTemplateLibrary(9, seed=0, difficulty="medium")
        tmpl = lib.generate()
        assert tmpl is not None
        assert "size" in tmpl
        assert "black_cells" in tmpl
        assert "runs" in tmpl

    def test_generate_all_white_cells_in_valid_runs(self):
        lib = KakuroTemplateLibrary(9, seed=1, difficulty="easy")
        tmpl = lib.generate()
        assert tmpl is not None
        black_set = {(int(r), int(c)) for r, c in tmpl["black_cells"]}
        white_cells = {
            (r, c) for r in range(9) for c in range(9)
            if (r, c) not in black_set
        }
        across_covered = {(int(p[0]), int(p[1])) for run in tmpl["runs"] if run["dir"] == "across" for p in run["cells"]}
        down_covered = {(int(p[0]), int(p[1])) for run in tmpl["runs"] if run["dir"] == "down" for p in run["cells"]}
        assert across_covered == white_cells, "Every white cell must be in an across run"
        assert down_covered == white_cells, "Every white cell must be in a down run"

    def test_generate_row_0_and_col_0_are_black(self):
        lib = KakuroTemplateLibrary(9, seed=2, difficulty="medium")
        tmpl = lib.generate()
        assert tmpl is not None
        black_set = {(int(r), int(c)) for r, c in tmpl["black_cells"]}
        for i in range(9):
            assert (0, i) in black_set, f"(0,{i}) should be black"
            assert (i, 0) in black_set, f"({i},0) should be black"

    def test_generate_no_run_longer_than_9(self):
        lib = KakuroTemplateLibrary(9, seed=3, difficulty="hard")
        tmpl = lib.generate()
        if tmpl is None:
            pytest.skip("Template generation returned None for this seed")
        for run in tmpl["runs"]:
            assert len(run["cells"]) <= 9, f"Run length {len(run['cells'])} exceeds 9"

    def test_generate_cancellable(self):
        lib = KakuroTemplateLibrary(9, seed=0, difficulty="medium")
        result = lib.generate(cancel_flag=[True])
        assert result is None


# ---------------------------------------------------------------------------
# N1 — build_kakuro_clue_positions
# ---------------------------------------------------------------------------

class TestBuildKakuroCluePositions:

    def test_across_clue_maps_to_left_cell(self):
        clues = [{"cells": [[3, 2], [3, 3]], "sum": 5, "dir": "across"}]
        pos = build_kakuro_clue_positions(clues)
        # Header for across run starting at (3,2) is (3, 1)
        assert (3, 1) in pos
        assert pos[(3, 1)]["across"] == 5

    def test_down_clue_maps_to_above_cell(self):
        clues = [{"cells": [[2, 5], [3, 5]], "sum": 8, "dir": "down"}]
        pos = build_kakuro_clue_positions(clues)
        # Header for down run starting at (2,5) is (1, 5)
        assert (1, 5) in pos
        assert pos[(1, 5)]["down"] == 8

    def test_both_directions_share_black_cell(self):
        clues = [
            {"cells": [[1, 2], [1, 3]], "sum": 7, "dir": "across"},
            {"cells": [[1, 1], [2, 1]], "sum": 4, "dir": "down"},
        ]
        pos = build_kakuro_clue_positions(clues)
        # Across header: (1, 1); Down header: (0, 1)
        assert pos[(1, 1)]["across"] == 7
        assert pos[(0, 1)]["down"] == 4


# ---------------------------------------------------------------------------
# N5 — _kakuro_can_reach
# ---------------------------------------------------------------------------

class TestKakuroCanReach:

    def test_zero_count_needs_zero(self):
        assert _kakuro_can_reach(0, 0, set()) is True
        assert _kakuro_can_reach(1, 0, set()) is False

    def test_simple_one_cell(self):
        assert _kakuro_can_reach(5, 1, set()) is True   # 5 is available
        assert _kakuro_can_reach(0, 1, set()) is False  # 0 not in 1-9
        assert _kakuro_can_reach(10, 1, set()) is False  # > 9; max single digit

    def test_two_cells_sum_3(self):
        # Only {1,2} sums to 3 with 2 distinct cells
        assert _kakuro_can_reach(3, 2, set()) is True
        assert _kakuro_can_reach(2, 2, set()) is False  # min is 1+2=3 > 2

    def test_respects_used_set(self):
        # With 1 and 2 used, min available is 3. Two-cell min = 3+4=7.
        assert _kakuro_can_reach(7, 2, {1, 2}) is True
        assert _kakuro_can_reach(4, 2, {1, 2}) is False

    def test_all_digits_used_returns_false(self):
        assert _kakuro_can_reach(1, 1, {1, 2, 3, 4, 5, 6, 7, 8, 9}) is False


# ---------------------------------------------------------------------------
# N5 — _KakuroRun technique
# ---------------------------------------------------------------------------

class TestKakuroRunTechnique:

    def _make_wg(self, clues: list[dict]) -> _WorkingGrid:
        size = 4
        black_cells = [[0, 0], [0, 1], [0, 2], [0, 3], [1, 0], [2, 0], [3, 0]]
        meta = VariantMetadata(
            name=Variant.KAKURO,
            size=size,
            symbols=list(range(1, 10)),
            region_layout=_box_layout(size),
            constraints={
                "clues": clues,
                "black_cells": black_cells,
                "clue_positions": {},
            },
        )
        board = Board(size=size, variant=Variant.KAKURO)
        black_set = {(int(r), int(c)) for r, c in black_cells}
        for r, c in black_set:
            board.cell(r, c).is_black = True
        return _WorkingGrid(board, meta)

    def test_technique_name_and_weight(self):
        tech = _KakuroRun()
        assert tech.name == "Kakuro Run"
        assert tech.weight == pytest.approx(2.1)

    def test_ignores_non_kakuro_variant(self):
        board = Board(size=9, variant=Variant.STANDARD)
        meta = VariantMetadata.standard_9x9()
        wg = _WorkingGrid(board, meta)
        tech = _KakuroRun()
        assert tech.apply(wg) is False

    def test_two_cell_run_sum_3_restricts_to_1_2(self):
        """A run [(1,1),(1,2)] summing to 3 must use digits {1, 2}."""
        clues = [
            {"cells": [[1, 1], [1, 2]], "sum": 3, "dir": "across"},
            {"cells": [[1, 1], [2, 1]], "sum": 3, "dir": "down"},
            {"cells": [[1, 2], [2, 2]], "sum": 3, "dir": "down"},
            {"cells": [[2, 1], [2, 2]], "sum": 3, "dir": "across"},
        ]
        wg = self._make_wg(clues)
        # SE-V4 seeding already runs _kakuro_run_step; re-verify final state
        for cell in [(1, 1), (1, 2)]:
            assert wg.candidates[cell[0]][cell[1]] <= {1, 2}

    def test_technique_returns_true_when_change_made(self):
        """Applying the technique when candidates can be narrowed returns True."""
        clues = [
            {"cells": [[1, 1], [1, 2]], "sum": 3, "dir": "across"},
            {"cells": [[1, 1], [2, 1]], "sum": 10, "dir": "down"},
            {"cells": [[1, 2], [2, 2]], "sum": 10, "dir": "down"},
            {"cells": [[2, 1], [2, 2]], "sum": 17, "dir": "across"},
        ]
        size = 4
        black_cells = [[0, 0], [0, 1], [0, 2], [0, 3], [1, 0], [2, 0], [3, 0]]
        meta = VariantMetadata(
            name=Variant.KAKURO,
            size=size,
            symbols=list(range(1, 10)),
            region_layout=_box_layout(size),
            constraints={
                "clues": clues,
                "black_cells": black_cells,
                "clue_positions": {},
            },
        )
        board = Board(size=size, variant=Variant.KAKURO)
        black_set = {(int(r), int(c)) for r, c in black_cells}
        for r, c in black_set:
            board.cell(r, c).is_black = True
        wg = _WorkingGrid(board, meta)
        # Re-open all candidates to test apply() from scratch
        for r in range(size):
            for c in range(size):
                if (r, c) not in black_set:
                    wg.candidates[r][c] = set(range(1, 10))
        tech = _KakuroRun()
        result = tech.apply(wg)
        assert result is True
        # The across run summing to 3 must restrict to {1, 2}
        assert wg.candidates[1][1] <= {1, 2}
        assert wg.candidates[1][2] <= {1, 2}


# ---------------------------------------------------------------------------
# N6 — GameController.is_complete for Kakuro
# ---------------------------------------------------------------------------

class TestKakuroIsComplete:
    """Test is_complete logic for Kakuro via direct object manipulation."""

    def _make_controller(self, board: Board, meta: VariantMetadata):
        from unittest.mock import MagicMock
        from richards_sudoku.controller.game_controller import GameController
        ctrl = MagicMock(spec=GameController)
        ctrl._board = board
        ctrl._meta = meta
        ctrl._solution = None
        ctrl._hints_remaining = None
        # Re-bind is_complete as an unbound call on the real class
        ctrl.is_complete = GameController.is_complete.__get__(ctrl)
        return ctrl

    def _make_kakuro_9x9_meta_with_one_run(self, run_cells, run_sum):
        clues = [{"cells": list(run_cells), "sum": run_sum, "dir": "across"}]
        # Add a matching down run to satisfy persistence, but for is_complete only across matters
        return VariantMetadata(
            name=Variant.KAKURO,
            size=9,
            symbols=list(range(1, 10)),
            region_layout=_box_layout(9),
            constraints={"clues": clues, "black_cells": [], "clue_positions": {}},
        )

    def test_complete_when_all_runs_satisfied(self):
        from richards_sudoku.controller.game_controller import GameController
        # Build a board where a 2-cell run [(0,0),(0,1)] with sum 3 is filled with 1,2
        board = Board(size=9, variant=Variant.KAKURO)
        board.cell(0, 0).value = 1
        board.cell(0, 1).value = 2
        # Fill remaining cells with dummy values so all-filled check passes
        for r in range(9):
            for c in range(9):
                if board.cell(r, c).value is None:
                    board.cell(r, c).value = 1  # dummy; these cells not in any clue

        meta = self._make_kakuro_9x9_meta_with_one_run([[0, 0], [0, 1]], 3)

        ctrl = MagicMock(spec=GameController)
        ctrl._board = board
        ctrl._meta = meta
        ctrl._solution = None
        ctrl._has_conflicts.return_value = False
        result = GameController.is_complete.fget(ctrl)
        assert result is True

    def test_incomplete_when_run_sum_wrong(self):
        from richards_sudoku.controller.game_controller import GameController
        board = Board(size=9, variant=Variant.KAKURO)
        board.cell(0, 0).value = 3  # wrong sum: 3+3=6 ≠ 3
        board.cell(0, 1).value = 3
        for r in range(9):
            for c in range(9):
                if board.cell(r, c).value is None:
                    board.cell(r, c).value = 1

        meta = self._make_kakuro_9x9_meta_with_one_run([[0, 0], [0, 1]], 3)

        ctrl = MagicMock(spec=GameController)
        ctrl._board = board
        ctrl._meta = meta
        ctrl._solution = None
        result = GameController.is_complete.fget(ctrl)
        assert result is False

    def test_incomplete_when_run_has_repeat(self):
        from richards_sudoku.controller.game_controller import GameController
        board = Board(size=9, variant=Variant.KAKURO)
        board.cell(0, 0).value = 2  # repeat: 2+1=3 is correct sum but... wait need repeat
        board.cell(0, 1).value = 1
        for r in range(9):
            for c in range(9):
                if board.cell(r, c).value is None:
                    board.cell(r, c).value = 1

        # Run sum=3, cells have values 2,1 → sum OK but check repeat
        # Actually 2,1 are distinct, let's use sum=4 with repeated 2,2
        board.cell(0, 0).value = 2
        board.cell(0, 1).value = 2  # repeat; sum=4

        meta = self._make_kakuro_9x9_meta_with_one_run([[0, 0], [0, 1]], 4)

        ctrl = MagicMock(spec=GameController)
        ctrl._board = board
        ctrl._meta = meta
        ctrl._solution = None
        result = GameController.is_complete.fget(ctrl)
        assert result is False

    def test_incomplete_when_cell_is_none(self):
        from richards_sudoku.controller.game_controller import GameController
        board = Board(size=9, variant=Variant.KAKURO)
        # Leave (0,0) empty
        board.cell(0, 1).value = 2
        meta = self._make_kakuro_9x9_meta_with_one_run([[0, 0], [0, 1]], 3)

        ctrl = MagicMock(spec=GameController)
        ctrl._board = board
        ctrl._meta = meta
        ctrl._solution = None
        result = GameController.is_complete.fget(ctrl)
        assert result is False


# ---------------------------------------------------------------------------
# N7 — Persistence round-trip
# ---------------------------------------------------------------------------

class TestKakuroPersistence:

    def _make_save_state(self):
        from richards_sudoku.persistence import SaveState
        from richards_sudoku.services.stats import GameStats
        from richards_sudoku.services.timer import GameTimer

        meta = _kakuro_meta_minimal()
        board = _kakuro_board_minimal()
        solution: list[list] = [[None] * 4 for _ in range(4)]
        # A valid fill: rows = [1,2,3], [4,5,6], [7,8,9] (demo sums don't matter for schema)
        for r_off, row_vals in enumerate(([1, 2, 3], [4, 5, 6], [7, 8, 9])):
            for c_off, v in enumerate(row_vals):
                solution[r_off + 1][c_off + 1] = v

        return SaveState(
            board=board,
            variant_meta=meta,
            solution=solution,
            timer=GameTimer(),
            stats=GameStats(),
            se_score=0.0,
            se_label="Unrated",
        )

    def test_roundtrip_json_preserves_clues(self, tmp_path: Path):
        from richards_sudoku.persistence import load, save
        state = self._make_save_state()
        path = tmp_path / "kakuro_test.json"
        save(state, path)
        loaded = load(path)
        orig_clues = state.variant_meta.constraints["clues"]
        loaded_clues = loaded.variant_meta.constraints["clues"]
        assert len(loaded_clues) == len(orig_clues)
        for orig, loaded_c in zip(orig_clues, loaded_clues):
            assert loaded_c["sum"] == orig["sum"]
            assert loaded_c["dir"] == orig["dir"]

    def test_roundtrip_rebuilds_clue_positions(self, tmp_path: Path):
        from richards_sudoku.persistence import load, save
        state = self._make_save_state()
        path = tmp_path / "kakuro_cluepos_test.json"
        save(state, path)
        loaded = load(path)
        # clue_positions must be non-empty after load (rebuilt in persistence)
        clue_pos = loaded.variant_meta.constraints.get("clue_positions", {})
        assert len(clue_pos) > 0

    def test_validation_rejects_missing_clues(self):
        from richards_sudoku.persistence.persistence import _validate_variant_constraints
        meta = VariantMetadata(
            name=Variant.KAKURO,
            size=4,
            symbols=list(range(1, 10)),
            region_layout=_box_layout(4),
            constraints={"clues": [], "black_cells": [[0, 0]], "clue_positions": {}},
        )
        with pytest.raises(ValueError, match="non-empty 'clues'"):
            _validate_variant_constraints(meta)

    def test_validation_rejects_bad_direction(self):
        from richards_sudoku.persistence.persistence import _validate_variant_constraints
        meta = VariantMetadata(
            name=Variant.KAKURO,
            size=4,
            symbols=list(range(1, 10)),
            region_layout=_box_layout(4),
            constraints={
                "clues": [{"cells": [[1, 1], [1, 2]], "sum": 3, "dir": "diagonal"}],
                "black_cells": [[0, 0]],
                "clue_positions": {},
            },
        )
        with pytest.raises(ValueError, match="across.*down|down.*across"):
            _validate_variant_constraints(meta)

    def test_validation_rejects_run_of_one(self):
        from richards_sudoku.persistence.persistence import _validate_variant_constraints
        meta = VariantMetadata(
            name=Variant.KAKURO,
            size=4,
            symbols=list(range(1, 10)),
            region_layout=_box_layout(4),
            constraints={
                "clues": [{"cells": [[1, 1]], "sum": 3, "dir": "across"}],
                "black_cells": [[0, 0]],
                "clue_positions": {},
            },
        )
        with pytest.raises(ValueError, match="at least 2 cells"):
            _validate_variant_constraints(meta)


# ---------------------------------------------------------------------------
# N8 — Text format round-trip
# ---------------------------------------------------------------------------

class TestKakuroTextFormat:

    def _meta_and_board(self):
        """Return (meta_dict, board_values) for a minimal 4×4 Kakuro."""
        meta = _kakuro_meta_minimal()
        meta_dict = meta.to_dict()
        # board: all white cells empty (None), black cells also None
        board_values = [[None] * 4 for _ in range(4)]
        return meta_dict, board_values

    def test_export_contains_variant_header(self):
        meta_dict, bv = self._meta_and_board()
        text = export_text(bv, meta_dict, seed=42, difficulty="medium")
        assert "variant: kakuro" in text

    def test_export_contains_mask_header(self):
        meta_dict, bv = self._meta_and_board()
        text = export_text(bv, meta_dict, seed=1, difficulty="easy")
        assert "mask: " in text

    def test_export_contains_clue_lines(self):
        meta_dict, bv = self._meta_and_board()
        text = export_text(bv, meta_dict, seed=0, difficulty="medium")
        clue_count = sum(1 for line in text.splitlines() if line.startswith("clue: "))
        assert clue_count == len(meta_dict["constraints"]["clues"])

    def test_export_digit_rows_use_underscore_for_black(self):
        meta_dict, bv = self._meta_and_board()
        text = export_text(bv, meta_dict, seed=0, difficulty="medium")
        lines = text.strip().splitlines()
        # Digit rows are lines not matching header pattern
        digit_rows = [l for l in lines if not ":" in l or l.count(":") == 0]
        # Actually they do contain no ":" — let's find them differently
        import re
        header_re = re.compile(r"^\w+(?:_\w+)*:\s")
        digit_rows = [l for l in lines if not header_re.match(l)]
        assert len(digit_rows) == 4, f"Expected 4 digit rows, got: {digit_rows}"
        # Row 0 = all black (B in mask → _ in digit row)
        assert digit_rows[0] == "____"
        # Row 1: col 0 is black, cols 1-3 are white/empty → "_000"
        assert digit_rows[1] == "_000"

    def test_roundtrip_preserves_clues(self):
        meta_dict, bv = self._meta_and_board()
        text = export_text(bv, meta_dict, seed=7, difficulty="hard")
        board2, meta2, seed2, diff2 = import_text(text)
        orig_clues = sorted(
            (tuple(tuple(c) for c in run["cells"]), run["sum"], run["dir"])
            for run in meta_dict["constraints"]["clues"]
        )
        loaded_clues = sorted(
            (tuple(tuple(c) for c in run["cells"]), run["sum"], run["dir"])
            for run in meta2["constraints"]["clues"]
        )
        assert orig_clues == loaded_clues

    def test_roundtrip_preserves_black_cells(self):
        meta_dict, bv = self._meta_and_board()
        text = export_text(bv, meta_dict, seed=0, difficulty="medium")
        board2, meta2, seed2, diff2 = import_text(text)
        orig_blacks = sorted(tuple(c) for c in meta_dict["constraints"]["black_cells"])
        loaded_blacks = sorted(tuple(c) for c in meta2["constraints"]["black_cells"])
        assert orig_blacks == loaded_blacks

    def test_roundtrip_filled_board(self):
        """Round-trip a board with some white cells filled."""
        meta_dict, bv = self._meta_and_board()
        bv[1][1] = 1
        bv[1][2] = 2
        bv[1][3] = 3
        text = export_text(bv, meta_dict, seed=0, difficulty="medium")
        board2, meta2, seed2, diff2 = import_text(text)
        assert board2[1][1] == 1
        assert board2[1][2] == 2
        assert board2[1][3] == 3
        assert board2[1][0] is None  # black cell stays None

    def test_import_rejects_wrong_dir(self):
        text = (
            "variant: kakuro\nsize: 4\nseed: 0\ndifficulty: medium\n"
            "mask: BBBB/B.../B.../B.../\n"
            "clue: 1,1 1,2:5:sideways\n"
        )
        with pytest.raises(ValueError, match="across.*down|down.*across"):
            import_text(text)

    def test_import_rejects_missing_clue_lines(self):
        text = (
            "variant: kakuro\nsize: 4\nseed: 0\ndifficulty: medium\n"
            "mask: BBBB/B.../B.../B.../\n"
        )
        with pytest.raises(ValueError, match="at least one 'clue'"):
            import_text(text)
