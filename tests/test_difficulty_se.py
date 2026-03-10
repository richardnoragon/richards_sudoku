"""Tests for the SukakuExplainer difficulty grader (difficulty_se.py)."""
from __future__ import annotations

import time

import pytest

from richards_sudoku.model.types import Board, Variant, VariantMetadata
from richards_sudoku.services.difficulty_se import (
    _Claiming,
    _HiddenPair,
    _HiddenQuad,
    _HiddenSingleBlock,
    _HiddenSingleLinear,
    _HiddenTriple,
    _Jellyfish,
    _KillerCage,
    _LastValue,
    _NakedPair,
    _NakedQuad,
    _NakedSingle,
    _NakedTriple,
    _Pointing,
    _Str8tsRun,
    _Swordfish,
    _WorkingGrid,
    _XWing,
    grade,
    score_to_label,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _standard_meta() -> VariantMetadata:
    return VariantMetadata.standard_9x9()


def _empty_grid() -> _WorkingGrid:
    """Working grid with no fixed clues — all candidates open ({1..9})."""
    board = Board(size=9, variant=Variant.STANDARD)
    return _WorkingGrid(board, _standard_meta())


def _make_board_from_solution(
    solution: list[list[int]],
    holes: set[tuple[int, int]],
) -> Board:
    """Return a Board from a full solution grid with *holes* left empty."""
    meta = _standard_meta()
    board = Board(size=9, variant=Variant.STANDARD)
    for r in range(9):
        for c in range(9):
            if (r, c) not in holes:
                cell = board.cell(r, c)
                cell.value = solution[r][c]
                cell.is_fixed = True
                cell.region_id = meta.region_layout[r][c]
    return board


# A well-known valid 9×9 Sudoku solution used throughout the tests.
_SOLUTION = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]

# A Latin transversal of the 9×9 grid: exactly one empty per row, per col,
# and per 3×3 box.  A puzzle with only these 9 holes is solvable by LastValue
# alone, so grade() will return (1.0, "Easy") or similar trivial score.
_TRANSVERSAL_HOLES: set[tuple[int, int]] = {
    (0, 0), (1, 3), (2, 6), (3, 1), (4, 4), (5, 7), (6, 2), (7, 5), (8, 8)
}


# ---------------------------------------------------------------------------
# score_to_label
# ---------------------------------------------------------------------------

class TestScoreToLabel:

    @pytest.mark.parametrize("score,expected", [
        (0.0,  "Unknown"),
        (0.1,  "Easy"),
        (1.0,  "Easy"),
        (2.0,  "Easy"),
        (2.1,  "Medium"),
        (3.0,  "Medium"),
        (4.0,  "Medium"),
        (4.1,  "Hard"),
        (6.0,  "Hard"),
        (6.1,  "Extreme"),
        (8.0,  "Extreme"),
    ])
    def test_boundary_values(self, score: float, expected: str) -> None:
        assert score_to_label(score) == expected


# ---------------------------------------------------------------------------
# grade() — special board states
# ---------------------------------------------------------------------------

class TestGradeSpecialBoards:

    def test_pre_solved_board_returns_unknown(self) -> None:
        """All cells already fixed → no solving steps → (0.0, 'Unknown')."""
        meta = _standard_meta()
        board = Board(size=9, variant=Variant.STANDARD)
        for r in range(9):
            for c in range(9):
                cell = board.cell(r, c)
                cell.value = _SOLUTION[r][c]
                cell.is_fixed = True
                cell.region_id = meta.region_layout[r][c]
        score, label = grade(board, meta)
        assert score == 0.0
        assert label == "Unknown"

    def test_contradictory_board_returns_invalid(self) -> None:
        """Duplicate fixed value in same row → (8.0, 'Invalid')."""
        meta = _standard_meta()
        board = Board(size=9, variant=Variant.STANDARD)
        for c in (0, 1):
            cell = board.cell(0, c)
            cell.value = 5
            cell.is_fixed = True
            cell.region_id = meta.region_layout[0][c]
        score, label = grade(board, meta)
        assert score == 8.0
        assert label == "Invalid"

    def test_last_value_only_puzzle_is_easy(self) -> None:
        """Transversal holes → only Last Value needed → score ≤ 2.0 (Easy)."""
        board = _make_board_from_solution(_SOLUTION, _TRANSVERSAL_HOLES)
        score, label = grade(board, _standard_meta())
        assert score <= 2.0
        assert label == "Easy"


# ---------------------------------------------------------------------------
# Regression: known-label puzzles
# ---------------------------------------------------------------------------

class TestGradeRegression:

    def test_easy_puzzle_label(self) -> None:
        board = _make_board_from_solution(_SOLUTION, _TRANSVERSAL_HOLES)
        _score, label = grade(board, _standard_meta())
        assert label == "Easy"

    def test_near_empty_board_terminates_as_extreme(self) -> None:
        """Single-clue board is unsolvable by our technique set → Extreme."""
        meta = _standard_meta()
        board = Board(size=9, variant=Variant.STANDARD)
        cell = board.cell(0, 0)
        cell.value = 5
        cell.is_fixed = True
        cell.region_id = meta.region_layout[0][0]
        _score, label = grade(board, meta)
        assert label in ("Extreme", "Invalid")


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------

class TestGradePerformance:

    def test_grade_completes_in_100ms(self) -> None:
        """grade() on a typical puzzle must complete within 100 ms."""
        board = _make_board_from_solution(_SOLUTION, _TRANSVERSAL_HOLES)
        meta = _standard_meta()
        start = time.perf_counter()
        grade(board, meta)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1

    def test_killer_cage_large_cage_completes_in_1s(self) -> None:
        """Killer cage permutation on a 5-cell cage must not hang (< 1 s)."""
        layout = [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]
        meta = VariantMetadata(
            name=Variant.STANDARD,
            size=9,
            symbols=list(range(1, 10)),
            region_layout=layout,
            constraints={
                "cages": [
                    {"cells": [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1]], "sum": 25}
                ]
            },
        )
        board = Board(size=9, variant=Variant.STANDARD)
        start = time.perf_counter()
        grade(board, meta)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0


# ---------------------------------------------------------------------------
# Variant paths
# ---------------------------------------------------------------------------

class TestVariantPaths:

    def test_str8ts_run_eliminates_impossible_digits(self) -> None:
        """_Str8tsRun reduces run candidates that cannot form a consecutive sequence."""
        layout = [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]
        meta = VariantMetadata(
            name=Variant.STR8TS,
            size=9,
            symbols=list(range(1, 10)),
            region_layout=layout,
            # Cell (0,2) is black: creates run [(0,0),(0,1)] of length 2.
            constraints={"black_cells": [[0, 2]]},
        )
        board = Board(size=9, variant=Variant.STR8TS)
        grid = _WorkingGrid(board, meta)

        # Candidates {1,7,8,9}: valid windows of size 2 are {7,8} and {8,9}.
        # Digit 1 cannot participate in any valid window → should be eliminated.
        grid.candidates[0][0] = {1, 7, 8, 9}
        grid.candidates[0][1] = {1, 7, 8, 9}

        tech = _Str8tsRun()
        assert tech.apply(grid) is True
        assert 1 not in grid.candidates[0][0]
        assert 1 not in grid.candidates[0][1]

    def test_killer_cage_eliminates_invalid_values(self) -> None:
        """_KillerCage restricts cell candidates to those satisfying the cage sum."""
        layout = [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]
        meta = VariantMetadata(
            name=Variant.STANDARD,
            size=9,
            symbols=list(range(1, 10)),
            region_layout=layout,
            # 2-cell cage summing to 3: only {1,2} / {2,1} are valid.
            constraints={"cages": [{"cells": [[0, 0], [0, 1]], "sum": 3}]},
        )
        board = Board(size=9, variant=Variant.STANDARD)
        grid = _WorkingGrid(board, meta)

        tech = _KillerCage()
        assert tech.apply(grid) is True
        assert grid.candidates[0][0] <= {1, 2}
        assert grid.candidates[0][1] <= {1, 2}


# ---------------------------------------------------------------------------
# Technique unit tests — _LastValue
# ---------------------------------------------------------------------------

class TestTechniqueLastValue:

    def test_fires_when_one_empty_cell_in_row(self) -> None:
        grid = _empty_grid()
        for c in range(1, 9):
            grid.set_value(0, c, c)  # place 1–8 in row 0, cols 1–8
        tech = _LastValue()
        assert tech.apply(grid) is True
        assert grid.values[0][0] == 9

    def test_does_not_fire_when_multiple_empty_cells(self) -> None:
        grid = _empty_grid()
        grid.set_value(0, 0, 1)  # only one value placed; row 0 still has 8 empty cells
        tech = _LastValue()
        assert tech.apply(grid) is False


# ---------------------------------------------------------------------------
# Technique unit tests — _HiddenSingleBlock
# ---------------------------------------------------------------------------

class TestTechniqueHiddenSingleBlock:

    def test_fires_when_value_unique_in_region(self) -> None:
        grid = _empty_grid()
        # Region 0 = cells (0-2)×(0-2).  Eliminate 9 from all except (0,0).
        for r, c in [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]:
            grid.candidates[r][c].discard(9)
        tech = _HiddenSingleBlock()
        assert tech.apply(grid) is True
        assert grid.values[0][0] == 9


# ---------------------------------------------------------------------------
# Technique unit tests — _HiddenSingleLinear
# ---------------------------------------------------------------------------

class TestTechniqueHiddenSingleLinear:

    def test_fires_when_value_unique_in_row(self) -> None:
        grid = _empty_grid()
        # Row 0: eliminate 9 from all cells except (0,0).
        for c in range(1, 9):
            grid.candidates[0][c].discard(9)
        tech = _HiddenSingleLinear()
        assert tech.apply(grid) is True
        assert grid.values[0][0] == 9


# ---------------------------------------------------------------------------
# Technique unit tests — _NakedSingle
# ---------------------------------------------------------------------------

class TestTechniqueNakedSingle:

    def test_fires_when_cell_has_one_candidate(self) -> None:
        grid = _empty_grid()
        grid.candidates[4][4] = {5}
        tech = _NakedSingle()
        assert tech.apply(grid) is True
        assert grid.values[4][4] == 5


# ---------------------------------------------------------------------------
# Technique unit tests — _Pointing
# ---------------------------------------------------------------------------

class TestTechniquePointing:

    def test_fires_and_eliminates_from_column(self) -> None:
        grid = _empty_grid()
        # Region 0 (rows 0-2, cols 0-2): 9 confined to col 0 only.
        for r, c in [(0, 1), (0, 2), (1, 1), (1, 2), (2, 1), (2, 2)]:
            grid.candidates[r][c].discard(9)
        tech = _Pointing()
        assert tech.apply(grid) is True
        # 9 must be gone from col 0 outside region 0 (rows 3–8).
        for r in range(3, 9):
            assert 9 not in grid.candidates[r][0]


# ---------------------------------------------------------------------------
# Technique unit tests — _Claiming
# ---------------------------------------------------------------------------

class TestTechniqueClaiming:

    def test_fires_and_eliminates_from_region(self) -> None:
        grid = _empty_grid()
        # Row 0: 9 confined to region 0 (cols 0-2) only.
        for c in range(3, 9):
            grid.candidates[0][c].discard(9)
        tech = _Claiming()
        assert tech.apply(grid) is True
        # 9 must be gone from region 0 cells outside row 0.
        for r, c in [(1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]:
            assert 9 not in grid.candidates[r][c]


# ---------------------------------------------------------------------------
# Technique unit tests — _NakedPair
# ---------------------------------------------------------------------------

class TestTechniqueNakedPair:

    def test_fires_and_eliminates_pair_from_row(self) -> None:
        grid = _empty_grid()
        for c in range(9):
            grid.candidates[0][c] = {1, 2, 3, 4, 5, 6, 7}
        grid.candidates[0][0] = {3, 7}
        grid.candidates[0][1] = {3, 7}
        tech = _NakedPair()
        assert tech.apply(grid) is True
        for c in range(2, 9):
            assert 3 not in grid.candidates[0][c]
            assert 7 not in grid.candidates[0][c]


# ---------------------------------------------------------------------------
# Technique unit tests — _XWing
# ---------------------------------------------------------------------------

class TestTechniqueXWing:

    def test_fires_and_eliminates_from_non_base_rows(self) -> None:
        grid = _empty_grid()
        # Value 9 in rows 0 and 3 confined to cols 0 and 3 only.
        for r in (0, 3):
            for c in range(9):
                if c not in (0, 3):
                    grid.candidates[r][c].discard(9)
        tech = _XWing()
        assert tech.apply(grid) is True
        for r in range(9):
            if r not in (0, 3):
                assert 9 not in grid.candidates[r][0]
                assert 9 not in grid.candidates[r][3]


# ---------------------------------------------------------------------------
# Technique unit tests — _HiddenPair
# ---------------------------------------------------------------------------

class TestTechniqueHiddenPair:

    def test_fires_and_reduces_pair_cells_to_pair_values(self) -> None:
        grid = _empty_grid()
        # Row 0: values 3 and 7 appear ONLY in (0,0) and (0,1).
        for c in range(2, 9):
            grid.candidates[0][c].discard(3)
            grid.candidates[0][c].discard(7)
        tech = _HiddenPair()
        assert tech.apply(grid) is True
        assert grid.candidates[0][0] == {3, 7}
        assert grid.candidates[0][1] == {3, 7}


# ---------------------------------------------------------------------------
# Technique unit tests — _NakedTriple
# ---------------------------------------------------------------------------

class TestTechniqueNakedTriple:

    def test_fires_and_eliminates_triple_from_row(self) -> None:
        grid = _empty_grid()
        for c in range(9):
            grid.candidates[0][c] = {1, 2, 3, 4, 5}
        grid.candidates[0][0] = {1, 2}
        grid.candidates[0][1] = {2, 3}
        grid.candidates[0][2] = {1, 3}
        tech = _NakedTriple()
        assert tech.apply(grid) is True
        for c in range(3, 9):
            assert 1 not in grid.candidates[0][c]
            assert 2 not in grid.candidates[0][c]
            assert 3 not in grid.candidates[0][c]


# ---------------------------------------------------------------------------
# Technique unit tests — _Swordfish
# ---------------------------------------------------------------------------

class TestTechniqueSwordfish:

    def test_fires_on_degree_3_fish(self) -> None:
        grid = _empty_grid()
        # Value 9 in rows 0, 3, 6 confined to cols 0, 3, 6 only.
        for r in (0, 3, 6):
            for c in range(9):
                if c not in (0, 3, 6):
                    grid.candidates[r][c].discard(9)
        tech = _Swordfish()
        assert tech.apply(grid) is True
        for r in range(9):
            if r not in (0, 3, 6):
                for c in (0, 3, 6):
                    assert 9 not in grid.candidates[r][c]


# ---------------------------------------------------------------------------
# Technique unit tests — _HiddenTriple
# ---------------------------------------------------------------------------

class TestTechniqueHiddenTriple:

    def test_fires_and_reduces_triple_cells(self) -> None:
        grid = _empty_grid()
        # Row 0: values 1, 2, 3 appear ONLY in (0,0), (0,1), (0,2).
        for c in range(3, 9):
            for v in (1, 2, 3):
                grid.candidates[0][c].discard(v)
        tech = _HiddenTriple()
        assert tech.apply(grid) is True
        assert grid.candidates[0][0] == {1, 2, 3}
        assert grid.candidates[0][1] == {1, 2, 3}
        assert grid.candidates[0][2] == {1, 2, 3}


# ---------------------------------------------------------------------------
# Technique unit tests — _NakedQuad
# ---------------------------------------------------------------------------

class TestTechniqueNakedQuad:

    def test_fires_and_eliminates_quad_from_row(self) -> None:
        grid = _empty_grid()
        for c in range(9):
            grid.candidates[0][c] = {1, 2, 3, 4, 5}
        grid.candidates[0][0] = {1, 2}
        grid.candidates[0][1] = {2, 3}
        grid.candidates[0][2] = {3, 4}
        grid.candidates[0][3] = {1, 4}
        tech = _NakedQuad()
        assert tech.apply(grid) is True
        for c in range(4, 9):
            for v in (1, 2, 3, 4):
                assert v not in grid.candidates[0][c]


# ---------------------------------------------------------------------------
# Technique unit tests — _Jellyfish
# ---------------------------------------------------------------------------

class TestTechniqueJellyfish:

    def test_fires_on_degree_4_fish(self) -> None:
        grid = _empty_grid()
        # Value 9 in rows 0, 1, 3, 6 confined to cols 0, 3, 6, 8 only.
        for r in (0, 1, 3, 6):
            for c in range(9):
                if c not in (0, 3, 6, 8):
                    grid.candidates[r][c].discard(9)
        tech = _Jellyfish()
        assert tech.apply(grid) is True
        for r in range(9):
            if r not in (0, 1, 3, 6):
                for c in (0, 3, 6, 8):
                    assert 9 not in grid.candidates[r][c]


# ---------------------------------------------------------------------------
# Technique unit tests — _HiddenQuad
# ---------------------------------------------------------------------------

class TestTechniqueHiddenQuad:

    def test_fires_and_reduces_quad_cells(self) -> None:
        grid = _empty_grid()
        # Row 0: values 1, 2, 3, 4 appear ONLY in (0,0)–(0,3).
        for c in range(4, 9):
            for v in (1, 2, 3, 4):
                grid.candidates[0][c].discard(v)
        tech = _HiddenQuad()
        assert tech.apply(grid) is True
        assert grid.candidates[0][0] == {1, 2, 3, 4}
        assert grid.candidates[0][1] == {1, 2, 3, 4}
        assert grid.candidates[0][2] == {1, 2, 3, 4}
        assert grid.candidates[0][3] == {1, 2, 3, 4}


# ---------------------------------------------------------------------------
# DC4 — Calibration regression tests
# (verify current thresholds hold across tested Beta variants)
# ---------------------------------------------------------------------------

def _std_layout() -> list[list[int]]:
    return [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]


class TestDC4Calibration:
    """DC4: SE grader thresholds are calibrated for Standard, Str8ts, and Killer.

    Each test locks down that an easy near-complete puzzle does not drift into
    Hard/Extreme after weight changes.  Thresholds will be refined per-variant
    after the EV-T6 labelled corpus is available (see TODO in score_to_label).
    """

    def test_standard_easy_puzzle_grades_easy(self) -> None:
        """Standard transversal puzzle (LastValue-only) still grades as Easy."""
        board = _make_board_from_solution(_SOLUTION, _TRANSVERSAL_HOLES)
        _, label = grade(board, _standard_meta())
        assert label == "Easy"

    def test_str8ts_near_complete_no_black_cells_grades_easy(self) -> None:
        """Str8ts with no black cells behaves identically to Standard → Easy."""
        meta = VariantMetadata(
            name=Variant.STR8TS,
            size=9,
            symbols=list(range(1, 10)),
            region_layout=_std_layout(),
            constraints={"black_cells": []},
        )
        board = _make_board_from_solution(_SOLUTION, _TRANSVERSAL_HOLES)
        _, label = grade(board, meta)
        assert label == "Easy"

    def test_str8ts_with_black_cell_outside_holes_grades_easy(self) -> None:
        """Str8ts with one fixed black cell (not a hole) still grades as Easy."""
        meta = VariantMetadata(
            name=Variant.STR8TS,
            size=9,
            symbols=list(range(1, 10)),
            region_layout=_std_layout(),
            # (4,8) has solution value 1 and is not in _TRANSVERSAL_HOLES
            constraints={"black_cells": [[4, 8]]},
        )
        board = _make_board_from_solution(_SOLUTION, _TRANSVERSAL_HOLES)
        _, label = grade(board, meta)
        assert label in ("Easy", "Medium")

    def test_killer_all_single_cell_cages_preseeded_not_hard(self) -> None:
        """All-single-cell-cage Killer: SE-V2 pre-seeds every hole → Unknown, not Hard."""
        holes = sorted(_TRANSVERSAL_HOLES)
        cages = [
            {"cells": [[r, c]], "sum": _SOLUTION[r][c]}
            for r, c in holes
        ]
        meta = VariantMetadata(
            name=Variant.KILLER,
            size=9,
            symbols=list(range(1, 10)),
            region_layout=_std_layout(),
            constraints={"cages": cages},
        )
        board = _make_board_from_solution(_SOLUTION, _TRANSVERSAL_HOLES)
        score, label = grade(board, meta)
        # SE-V2 seeds all single-cell cages before the technique loop → already solved
        assert label in ("Unknown", "Easy")
        assert score <= 2.0

    def test_killer_two_cell_cage_grades_easy_or_unknown(self) -> None:
        """One 2-cell cage + 7 single-cell cages: KillerCage resolves it → Easy/Unknown."""
        holes = sorted(_TRANSVERSAL_HOLES)
        two_cell = {"cells": [list(holes[0]), list(holes[1])],
                    "sum": _SOLUTION[holes[0][0]][holes[0][1]] + _SOLUTION[holes[1][0]][holes[1][1]]}
        singles = [{"cells": [[r, c]], "sum": _SOLUTION[r][c]} for r, c in holes[2:]]
        meta = VariantMetadata(
            name=Variant.KILLER,
            size=9,
            symbols=list(range(1, 10)),
            region_layout=_std_layout(),
            constraints={"cages": [two_cell] + singles},
        )
        board = _make_board_from_solution(_SOLUTION, _TRANSVERSAL_HOLES)
        _score, label = grade(board, meta)
        assert label in ("Unknown", "Easy", "Medium")
