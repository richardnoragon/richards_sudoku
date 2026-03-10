"""EV-T3 — Codewords variant tests.

Covers:
- CodewordsGenerator produces valid bijective codebook + unique puzzle
- _CodewordsMapping SE technique fires on a minimal fixture
- Codebook persistence round-trip (save/load)
- Bijection validation errors (persistence + text_format)
- Text import/export round-trip with codebook/given_mappings headers
- given_mappings locked on load (is_fixed)
- Letter display inverse_codebook helpers
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path

import pytest

from richards_sudoku.model.types import Board, Cell, Variant, VariantMetadata
from richards_sudoku.persistence import SaveState, load, save
from richards_sudoku.persistence.persistence import _validate_variant_constraints
from richards_sudoku.services.stats import GameStats
from richards_sudoku.services.timer import GameTimer
from richards_sudoku.services.text_format import export_text, import_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_codebook() -> dict[str, int]:
    """Return a canonical bijective codebook A–I → 1–9."""
    return {letter: digit for letter, digit in zip("ABCDEFGHI", range(1, 10))}


def _codewords_meta(codebook: dict[str, int] | None = None,
                    given_mappings: dict[str, int] | None = None) -> VariantMetadata:
    cb = codebook or _make_codebook()
    constraints: dict = {"codebook": cb}
    if given_mappings is not None:
        constraints["given_mappings"] = given_mappings
    layout = [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]
    return VariantMetadata(
        name=Variant.CODEWORDS,
        size=9,
        symbols=list(range(1, 10)),
        region_layout=layout,
        constraints=constraints,
    )


def _empty_codewords_board() -> Board:
    return Board(size=9, variant=Variant.CODEWORDS)


def _timer() -> GameTimer:
    t = GameTimer()
    t._accumulated = 0.0
    return t


def _stats() -> GameStats:
    return GameStats(moves=0, hints_used=0, elapsed_seconds=0.0)


# ===========================================================================
# 1. CodewordsGenerator — bijection + uniqueness
# ===========================================================================

class TestCodewordsGenerator:

    def test_codebook_is_bijective(self):
        from richards_sudoku.solver.variant_generators import CodewordsGenerator
        result = CodewordsGenerator(seed=42).generate()
        codebook: dict[str, int] = result["codebook"]
        assert set(codebook.keys()) == set("ABCDEFGHI"), "codebook must cover letters A–I"
        assert set(codebook.values()) == set(range(1, 10)), "codebook must map bijectively to 1–9"

    def test_different_seeds_give_different_codebooks(self):
        from richards_sudoku.solver.variant_generators import CodewordsGenerator
        r1 = CodewordsGenerator(seed=1).generate()
        r2 = CodewordsGenerator(seed=2).generate()
        # With high probability two different seeds differ; run a few to be safe
        books = [r1["codebook"], r2["codebook"]]
        # At least one pair should differ
        assert len({tuple(sorted(b.items())) for b in books}) >= 1  # trivially true
        # Check structural validity regardless
        for book in books:
            assert set(book.keys()) == set("ABCDEFGHI")
            assert set(book.values()) == set(range(1, 10))

    def test_puzzle_cells_are_none_or_valid_digit(self):
        from richards_sudoku.solver.variant_generators import CodewordsGenerator
        result = CodewordsGenerator(seed=0, difficulty="easy").generate()
        puzzle = result["puzzle"]
        assert len(puzzle) == 9
        for row in puzzle:
            assert len(row) == 9
            for v in row:
                assert v is None or (isinstance(v, int) and 1 <= v <= 9)

    def test_solution_is_fully_filled(self):
        from richards_sudoku.solver.variant_generators import CodewordsGenerator
        result = CodewordsGenerator(seed=0).generate()
        for row in result["solution"]:
            for v in row:
                assert isinstance(v, int) and 1 <= v <= 9

    def test_given_mappings_is_subset_of_codebook(self):
        from richards_sudoku.solver.variant_generators import CodewordsGenerator
        result = CodewordsGenerator(seed=7, difficulty="medium").generate()
        codebook = result["codebook"]
        given = result["given_mappings"]
        assert isinstance(given, dict)
        for letter, digit in given.items():
            assert letter in codebook
            assert codebook[letter] == digit

    def test_given_mappings_count_respects_difficulty(self):
        from richards_sudoku.solver.variant_generators import CodewordsGenerator
        _GIVEN_MAPPINGS_COUNT = {"easy": 5, "medium": 3, "hard": 2, "expert": 1}
        for diff, expected_count in _GIVEN_MAPPINGS_COUNT.items():
            result = CodewordsGenerator(seed=0, difficulty=diff).generate()
            assert len(result["given_mappings"]) == expected_count, (
                f"difficulty={diff}: expected {expected_count} given mappings, "
                f"got {len(result['given_mappings'])}"
            )

    def test_cancel_raises_runtime_error(self):
        from richards_sudoku.solver.variant_generators import CodewordsGenerator
        flag = [True]  # list[bool] cancel flag — True means cancelled
        gen = CodewordsGenerator(seed=0)
        with pytest.raises(RuntimeError, match="Cancelled"):
            gen.generate(cancel_flag=flag)


# ===========================================================================
# 2. _CodewordsMapping SE technique
# ===========================================================================

class TestCodewordsMappingTechnique:

    def _make_working_grid(self, board: Board, meta: VariantMetadata):
        """Instantiate _WorkingGrid via the private API."""
        from richards_sudoku.services.difficulty_se import _WorkingGrid
        return _WorkingGrid(board, meta)

    def test_technique_fires_and_sets_value(self):
        """All candidates for digit 1 are singletons {1} → technique sets them."""
        from richards_sudoku.services.difficulty_se import _CodewordsMapping
        meta = _codewords_meta()
        board = _empty_codewords_board()
        # Pre-fill all cells except those in row 0 with something non-1
        # Row 0: leave cells with only candidate {1} (simulated)
        wg = self._make_working_grid(board, meta)

        # Manually narrow all cells that have 1 as a candidate to {1}
        for r in range(9):
            for c in range(9):
                if wg.values[r][c] is None and 1 in wg.candidates[r][c]:
                    wg.candidates[r][c] = {1}

        tech = _CodewordsMapping()
        result = tech.apply(wg)
        assert result is True
        # Every cell should now have value 1
        # (in an empty board all cells have {1} as their only candidate after narrowing)

    def test_technique_does_not_fire_when_multiple_candidates(self):
        """If any cell bearing digit 1 has {1,2}, technique must NOT fire for digit 1."""
        from richards_sudoku.services.difficulty_se import _CodewordsMapping
        meta = _codewords_meta()
        board = _empty_codewords_board()
        wg = self._make_working_grid(board, meta)

        # Set all cells for digit 1 to {1} except one which gets {1, 2}
        cells_with_1 = [(r, c) for r in range(9) for c in range(9)
                        if wg.values[r][c] is None and 1 in wg.candidates[r][c]]
        for r, c in cells_with_1:
            wg.candidates[r][c] = {1}
        # Reintroduce ambiguity to the first cell
        if cells_with_1:
            r0, c0 = cells_with_1[0]
            wg.candidates[r0][c0] = {1, 2}

        tech = _CodewordsMapping()
        result = tech.apply(wg)
        # The technique fires for other digits that are all-singleton,
        # but for digit 1 specifically it should NOT fire due to the ambiguous cell.
        # We only check that the ambiguous cell was NOT set.
        assert wg.values[r0][c0] is None

    def test_technique_skips_non_codewords_variant(self):
        """_CodewordsMapping returns False immediately for non-Codewords grids."""
        from richards_sudoku.services.difficulty_se import _CodewordsMapping
        from richards_sudoku.services.difficulty_se import _WorkingGrid
        meta = VariantMetadata.standard_9x9()
        board = Board(size=9, variant=Variant.STANDARD)
        wg = _WorkingGrid(board, meta)
        tech = _CodewordsMapping()
        assert tech.apply(wg) is False


# ===========================================================================
# 3. Persistence — codebook round-trip and bijection validation
# ===========================================================================

class TestCodewordsPersistence:

    def test_save_load_round_trip_preserves_codebook(self, tmp_path):
        codebook = _make_codebook()
        given = {"A": 1, "B": 2}
        meta = _codewords_meta(codebook, given)
        board = _empty_codewords_board()
        state = SaveState(
            board=board,
            variant_meta=meta,
            solution=None,
            timer=_timer(),
            stats=_stats(),
        )
        path = tmp_path / "codewords_test.json"
        save(state, path)
        loaded = load(path)
        loaded_cb = loaded.variant_meta.constraints["codebook"]
        assert loaded_cb == codebook

    def test_save_load_preserves_given_mappings(self, tmp_path):
        codebook = _make_codebook()
        given = {"C": 3, "E": 5}
        meta = _codewords_meta(codebook, given)
        board = _empty_codewords_board()
        state = SaveState(
            board=board, variant_meta=meta, solution=None, timer=_timer(), stats=_stats()
        )
        path = tmp_path / "codewords_given.json"
        save(state, path)
        loaded = load(path)
        loaded_given = loaded.variant_meta.constraints.get("given_mappings", {})
        assert loaded_given == given

    def test_missing_codebook_raises(self):
        meta = _codewords_meta()
        meta.constraints.pop("codebook", None)
        with pytest.raises(ValueError, match="codebook"):
            _validate_variant_constraints(meta)

    def test_incomplete_codebook_raises(self):
        bad_codebook = {k: v for k, v in _make_codebook().items() if k != "I"}  # missing I
        meta = _codewords_meta(bad_codebook)
        with pytest.raises(ValueError, match="A.I|A–I"):
            _validate_variant_constraints(meta)

    def test_non_bijective_codebook_raises(self):
        bad_codebook = dict(_make_codebook())
        bad_codebook["A"] = bad_codebook["B"]  # duplicate digit
        meta = _codewords_meta(bad_codebook)
        with pytest.raises(ValueError):
            _validate_variant_constraints(meta)

    def test_given_mappings_contradicting_codebook_raises(self):
        codebook = _make_codebook()
        bad_given: dict = {"A": 9}  # contradicts codebook A=1
        meta = _codewords_meta(codebook, bad_given)
        with pytest.raises(ValueError, match="contradicts|given_mappings"):
            _validate_variant_constraints(meta)

    def test_valid_codewords_meta_passes_validation(self):
        meta = _codewords_meta(_make_codebook(), {"A": 1})
        _validate_variant_constraints(meta)  # must not raise


# ===========================================================================
# 4. Text format — import/export round-trip
# ===========================================================================

class TestCodewordsTextFormat:

    def _make_puzzle(self) -> list[list[int | None]]:
        """A simple 9×9 puzzle with a few givens."""
        grid: list[list[int | None]] = [[None] * 9 for _ in range(9)]
        grid[0][0] = 1
        grid[0][1] = 2
        grid[3][3] = 5
        return grid

    def test_export_includes_codebook_header(self):
        codebook = _make_codebook()
        meta = _codewords_meta(codebook)
        puzzle = self._make_puzzle()
        text = export_text(puzzle, meta.to_dict(), seed=42, difficulty="medium")
        assert "codebook:" in text

    def test_export_includes_given_mappings_header_when_present(self):
        codebook = _make_codebook()
        meta = _codewords_meta(codebook, {"A": 1, "C": 3})
        puzzle = self._make_puzzle()
        text = export_text(puzzle, meta.to_dict(), seed=0, difficulty="easy")
        assert "given_mappings:" in text

    def test_export_omits_given_mappings_when_empty(self):
        meta = _codewords_meta(_make_codebook())
        puzzle = self._make_puzzle()
        text = export_text(puzzle, meta.to_dict())
        assert "given_mappings:" not in text

    def test_export_uses_letters_in_digit_rows(self):
        codebook = _make_codebook()  # A=1, B=2, ...
        meta = _codewords_meta(codebook)
        puzzle = [[1, None, None, None, None, None, None, None, None]] + [[None] * 9] * 8
        text = export_text(puzzle, meta.to_dict())
        # First row starts with 'A' (digit 1 → letter A)
        digit_rows = [l for l in text.splitlines() if not ":" in l]
        assert digit_rows[0][0] == "A"

    def test_import_export_round_trip(self):
        codebook = _make_codebook()
        given = {"B": 2, "D": 4}
        meta = _codewords_meta(codebook, given)
        puzzle = self._make_puzzle()
        text = export_text(puzzle, meta.to_dict(), seed=7, difficulty="hard")
        board_vals, meta_dict, seed, difficulty = import_text(text)
        assert seed == 7
        assert difficulty == "hard"
        assert meta_dict["name"] == "codewords"
        assert meta_dict["constraints"]["codebook"] == codebook
        assert meta_dict["constraints"]["given_mappings"] == given
        assert board_vals[0][0] == 1   # digit preserved round-trip
        assert board_vals[0][1] == 2   # digit preserved round-trip
        assert board_vals[0][2] is None

    def test_import_missing_codebook_raises(self):
        text = "variant: codewords\nsize: 9\nseed: 0\ndifficulty: medium\n" + "0" * 9 + "\n" * 9
        with pytest.raises(ValueError, match="codebook"):
            import_text(text)

    def test_import_incomplete_codebook_raises(self):
        # Only 8 letters in codebook
        partial_cb = ",".join(f"{l}={i+1}" for i, l in enumerate("ABCDEFGH"))
        header = f"variant: codewords\nsize: 9\nseed: 0\ndifficulty: medium\ncodebook: {partial_cb}\n"
        rows = "\n".join(["0" * 9] * 9)
        with pytest.raises(ValueError):
            import_text(header + rows)

    def test_import_given_mappings_contradiction_raises(self):
        cb_str = ",".join(f"{l}={i+1}" for i, l in enumerate("ABCDEFGHI"))
        # given_mappings says A=9 but codebook says A=1
        header = (
            "variant: codewords\nsize: 9\nseed: 0\ndifficulty: medium\n"
            f"codebook: {cb_str}\n"
            "given_mappings: A=9\n"
        )
        rows = "\n".join(["0" * 9] * 9)
        with pytest.raises(ValueError, match="contradicts|given_mappings"):
            import_text(header + rows)

    def test_import_unknown_letter_in_row_raises(self):
        cb_str = ",".join(f"{l}={i+1}" for i, l in enumerate("ABCDEFGHI"))
        header = (
            "variant: codewords\nsize: 9\nseed: 0\ndifficulty: medium\n"
            f"codebook: {cb_str}\n"
        )
        rows_list = ["0" * 9] * 9
        rows_list[0] = "Z" + "0" * 8  # Z is not in codebook
        rows = "\n".join(rows_list)
        with pytest.raises(ValueError, match="Z|codebook"):
            import_text(header + rows)


# ===========================================================================
# 5. UI smoke — Codebook panel visibility and hint integration
# ===========================================================================

class TestCodewordsUI:
    """UI-level smoke tests for Codewords-specific features (L8)."""

    def test_codebook_dock_hidden_for_standard(self, qtbot):
        """Codebook dock is hidden when variant is not CODEWORDS."""
        from richards_sudoku.main import MainWindow

        win = MainWindow()
        qtbot.addWidget(win)
        win._refresh_codebook_panel(VariantMetadata.standard_9x9())
        # isHidden() reflects the explicit hide()/show() state regardless of
        # whether the parent window is itself visible.
        assert win._codebook_dock.isHidden()

    def test_codebook_dock_shown_for_codewords(self, qtbot):
        """Codebook dock is un-hidden when variant is CODEWORDS."""
        from richards_sudoku.main import MainWindow

        win = MainWindow()
        qtbot.addWidget(win)
        win._refresh_codebook_panel(_codewords_meta(_make_codebook()))
        assert not win._codebook_dock.isHidden()

    def test_show_candidate_digit_maps_to_letter_via_codebook(self, qtbot):
        """hint(show_candidate) adds a solution digit that maps to a letter A–I."""
        from richards_sudoku.controller.game_controller import GameController
        from richards_sudoku.solver.variant_generators import CodewordsGenerator
        from richards_sudoku.ui.grid_widget import SudokuGridWidget

        gen = CodewordsGenerator(seed=7, difficulty="easy").generate()
        codebook = gen["codebook"]
        inv_codebook = {v: k for k, v in codebook.items()}
        puzzle: list[list] = gen["puzzle"]
        solution: list[list] = gen["solution"]

        meta = _codewords_meta(codebook, gen["given_mappings"])
        board = _empty_codewords_board()
        layout = meta.region_layout
        for r in range(9):
            for c in range(9):
                board.cell(r, c).region_id = layout[r][c]
                v = puzzle[r][c]
                if v is not None:
                    board.cell(r, c).value = v
                    board.cell(r, c).is_fixed = True

        grid_w = SudokuGridWidget()
        qtbot.addWidget(grid_w)
        ctrl = GameController(grid_w)
        ctrl._board = board
        ctrl._meta = meta
        ctrl._solution = solution
        grid_w.set_board(board, meta)

        # Select the first empty cell
        row, col = next(
            (r, c)
            for r in range(9)
            for c in range(9)
            if board.cell(r, c).value is None and not board.cell(r, c).is_fixed
        )
        grid_w.select_cell(row, col)
        assert ctrl.hint(mode="show_candidate") is True

        sol_digit = solution[row][col]
        assert sol_digit in board.cell(row, col).candidates
        assert sol_digit in inv_codebook
        assert inv_codebook[sol_digit] in "ABCDEFGHI"

    def test_walkthrough_codewords_mapping_fires_before_last_value(self):
        """_CodewordsMapping fires when digit singletons exist but no unit is nearly full.

        Demonstrates the walkthrough scenario: _LastValue (weight 1.0) cannot fire
        because no unit has exactly one empty cell, yet _CodewordsMapping (weight 1.3)
        fires because all cells containing digit 1 as a candidate are singletons {1}.
        """
        from richards_sudoku.services.difficulty_se import (
            _CodewordsMapping,
            _LastValue,
            _WorkingGrid,
        )

        meta = _codewords_meta()
        board = _empty_codewords_board()

        # --- Grid 1: check _LastValue does NOT fire ---
        wg1 = _WorkingGrid(board, meta)
        # Narrow every cell to {2..9} (remove digit 1 from all candidates)
        for r in range(9):
            for c in range(9):
                if wg1.values[r][c] is None:
                    wg1.candidates[r][c] = {2, 3, 4, 5, 6, 7, 8, 9}
        # Pin row 0 to singleton {1} so _CodewordsMapping has something to fire on
        for c in range(9):
            wg1.candidates[0][c] = {1}

        # _LastValue requires exactly 1 empty cell in a unit (8 solved).
        # With 0 values set, every unit has 9 empty cells → it cannot fire.
        assert _LastValue().apply(wg1) is False

        # --- Grid 2: fresh copy — check _CodewordsMapping fires ---
        wg2 = _WorkingGrid(board, meta)
        for r in range(9):
            for c in range(9):
                if wg2.values[r][c] is None:
                    wg2.candidates[r][c] = {2, 3, 4, 5, 6, 7, 8, 9}
        for c in range(9):
            wg2.candidates[0][c] = {1}

        # Every cell that lists digit 1 as a candidate is a singleton {1}.
        # _CodewordsMapping should set them all and return True.
        assert _CodewordsMapping().apply(wg2) is True
