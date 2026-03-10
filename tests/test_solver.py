"""Unit tests for the solver, validator, and generator."""
from __future__ import annotations

import time

import pytest

from richards_sudoku.model.types import VariantMetadata
from richards_sudoku.solver import (
    Grid,
    generate_puzzle,
    generate_solution,
    is_valid_and_unique,
    solve,
    validate,
)
from richards_sudoku.solver.generator import GenerationCancelled, check_unique

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _meta() -> VariantMetadata:
    return VariantMetadata.standard_9x9()


def _solved_grid() -> Grid:
    """A known valid solved 9×9 grid."""
    return [
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


def _puzzle_with_one_solution() -> Grid:
    """A well-known uniquely-solvable 9×9 puzzle (0/None = empty)."""
    N = None
    return [
        [5, 3, N, N, 7, N, N, N, N],
        [6, N, N, 1, 9, 5, N, N, N],
        [N, 9, 8, N, N, N, N, 6, N],
        [8, N, N, N, 6, N, N, N, 3],
        [4, N, N, 8, N, 3, N, N, 1],
        [7, N, N, N, 2, N, N, N, 6],
        [N, 6, N, N, N, N, 2, 8, N],
        [N, N, N, 4, 1, 9, N, N, 5],
        [N, N, N, N, 8, N, N, 7, 9],
    ]


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------

class TestValidate:
    def test_solved_grid_is_valid(self) -> None:
        m = _meta()
        assert validate(_solved_grid(), m.size, m.region_layout, m.symbols) is True

    def test_empty_grid_is_valid(self) -> None:
        m = _meta()
        empty: Grid = [[None] * 9 for _ in range(9)]
        assert validate(empty, m.size, m.region_layout, m.symbols) is True

    def test_row_duplicate_is_invalid(self) -> None:
        m = _meta()
        g = _solved_grid()
        g[0][1] = g[0][0]  # duplicate in row 0
        assert validate(g, m.size, m.region_layout, m.symbols) is False

    def test_col_duplicate_is_invalid(self) -> None:
        m = _meta()
        g = _solved_grid()
        g[1][0] = g[0][0]  # duplicate in column 0
        assert validate(g, m.size, m.region_layout, m.symbols) is False

    def test_region_duplicate_is_invalid(self) -> None:
        m = _meta()
        g = _solved_grid()
        g[1][1] = g[0][0]  # both in top-left box
        assert validate(g, m.size, m.region_layout, m.symbols) is False

    def test_out_of_symbol_range_is_invalid(self) -> None:
        m = _meta()
        g = _solved_grid()
        g[0][0] = 10  # 10 not in 1–9 symbols
        assert validate(g, m.size, m.region_layout, m.symbols) is False


# ---------------------------------------------------------------------------
# Solver tests
# ---------------------------------------------------------------------------

class TestSolve:
    def test_solved_grid_returns_itself(self) -> None:
        m = _meta()
        sols = solve(_solved_grid(), m.size, m.region_layout, m.symbols)
        assert len(sols) == 1

    def test_puzzle_with_one_solution_returns_one(self) -> None:
        m = _meta()
        sols = solve(_puzzle_with_one_solution(), m.size, m.region_layout, m.symbols, limit=2)
        assert len(sols) == 1

    def test_solution_is_valid_and_complete(self) -> None:
        m = _meta()
        sols = solve(_puzzle_with_one_solution(), m.size, m.region_layout, m.symbols)
        solution = sols[0]
        assert all(solution[r][c] is not None for r in range(9) for c in range(9))
        assert validate(solution, m.size, m.region_layout, m.symbols)

    def test_empty_grid_returns_empty(self) -> None:
        m = _meta()
        empty: Grid = [[None] * 9 for _ in range(9)]
        # Naked/hidden singles alone cannot make any progress on an empty grid.
        sols = solve(empty, m.size, m.region_layout, m.symbols, limit=2)
        assert sols == []

    def test_unsolvable_grid_returns_empty(self) -> None:
        m = _meta()
        g: Grid = [[None] * 9 for _ in range(9)]
        g[0][0] = 1
        g[0][1] = 1  # row conflict → no solution
        sols = solve(g, m.size, m.region_layout, m.symbols)
        assert sols == []

    def test_solver_performance_under_2s(self) -> None:
        m = _meta()
        start = time.perf_counter()
        solve(_puzzle_with_one_solution(), m.size, m.region_layout, m.symbols)
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"Solver took {elapsed:.3f}s (> 2s budget)"


# ---------------------------------------------------------------------------
# is_valid_and_unique tests
# ---------------------------------------------------------------------------

class TestIsValidAndUnique:
    def test_uniquely_solvable_puzzle_returns_true(self) -> None:
        m = _meta()
        assert is_valid_and_unique(_puzzle_with_one_solution(), m.size, m.region_layout, m.symbols)

    def test_solved_grid_is_unique(self) -> None:
        m = _meta()
        assert is_valid_and_unique(_solved_grid(), m.size, m.region_layout, m.symbols)

    def test_empty_grid_is_not_unique(self) -> None:
        m = _meta()
        empty: Grid = [[None] * 9 for _ in range(9)]
        assert not is_valid_and_unique(empty, m.size, m.region_layout, m.symbols)

    def test_invalid_grid_is_not_unique(self) -> None:
        m = _meta()
        g: Grid = [[None] * 9 for _ in range(9)]
        g[0][0] = 1
        g[0][1] = 1
        assert not is_valid_and_unique(g, m.size, m.region_layout, m.symbols)


# ---------------------------------------------------------------------------
# Generator tests
# ---------------------------------------------------------------------------

class TestGenerateSolution:
    def test_solution_is_complete_and_valid(self) -> None:
        m = _meta()
        sol = generate_solution(m.size, m.region_layout, m.symbols, seed=42)
        assert all(sol[r][c] is not None for r in range(9) for c in range(9))
        assert validate(sol, m.size, m.region_layout, m.symbols)

    def test_same_seed_gives_same_solution(self) -> None:
        m = _meta()
        sol_a = generate_solution(m.size, m.region_layout, m.symbols, seed=7)
        sol_b = generate_solution(m.size, m.region_layout, m.symbols, seed=7)
        assert sol_a == sol_b

    def test_different_seeds_give_different_solutions(self) -> None:
        m = _meta()
        sol_a = generate_solution(m.size, m.region_layout, m.symbols, seed=1)
        sol_b = generate_solution(m.size, m.region_layout, m.symbols, seed=2)
        assert sol_a != sol_b


class TestGeneratePuzzle:
    def test_puzzle_is_valid(self) -> None:
        m = _meta()
        puzzle, solution = generate_puzzle(
            m.size, m.region_layout, m.symbols, seed=42, difficulty="medium"
        )
        # Generator guarantees uniqueness; verify structural validity here.
        assert validate(puzzle, m.size, m.region_layout, m.symbols)

    def test_solution_solves_the_puzzle(self) -> None:
        m = _meta()
        puzzle, solution = generate_puzzle(
            m.size, m.region_layout, m.symbols, seed=42, difficulty="medium"
        )
        # Every given in puzzle must match solution
        for r in range(m.size):
            for c in range(m.size):
                if puzzle[r][c] is not None:
                    assert puzzle[r][c] == solution[r][c]

    def test_solution_is_complete_and_valid(self) -> None:
        m = _meta()
        _, solution = generate_puzzle(
            m.size, m.region_layout, m.symbols, seed=42, difficulty="easy"
        )
        assert all(solution[r][c] is not None for r in range(9) for c in range(9))
        assert validate(solution, m.size, m.region_layout, m.symbols)

    def test_same_seed_and_difficulty_is_reproducible(self) -> None:
        m = _meta()
        p1, s1 = generate_puzzle(m.size, m.region_layout, m.symbols, seed=99, difficulty="hard")
        p2, s2 = generate_puzzle(m.size, m.region_layout, m.symbols, seed=99, difficulty="hard")
        assert p1 == p2
        assert s1 == s2

    def test_unknown_difficulty_raises(self) -> None:
        m = _meta()
        with pytest.raises(ValueError, match="Unknown difficulty"):
            generate_puzzle(m.size, m.region_layout, m.symbols, seed=1, difficulty="impossible")

    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard", "expert"])
    def test_all_difficulties_produce_valid_puzzles(self, difficulty: str) -> None:
        m = _meta()
        puzzle, _ = generate_puzzle(
            m.size, m.region_layout, m.symbols, seed=42, difficulty=difficulty
        )
        # Generator guarantees uniqueness; verify structural validity here.
        assert validate(puzzle, m.size, m.region_layout, m.symbols)

    def test_easy_has_more_givens_than_expert(self) -> None:
        m = _meta()
        easy, _ = generate_puzzle(m.size, m.region_layout, m.symbols, seed=42, difficulty="easy")
        expert, _ = generate_puzzle(m.size, m.region_layout, m.symbols, seed=42, difficulty="expert")
        easy_count = sum(1 for r in range(9) for c in range(9) if easy[r][c] is not None)
        expert_count = sum(1 for r in range(9) for c in range(9) if expert[r][c] is not None)
        assert easy_count > expert_count


# ---------------------------------------------------------------------------
# B5 — GenerationCancelled and check_unique
# ---------------------------------------------------------------------------

class TestGenerationCancelled:
    def test_cancel_flag_raises_immediately(self) -> None:
        """generate_puzzle raises GenerationCancelled when cancel_flag=[True]."""
        m = _meta()
        with pytest.raises(GenerationCancelled):
            generate_puzzle(
                m.size, m.region_layout, m.symbols,
                seed=1, cancel_flag=[True],
            )

    def test_cancel_flag_false_does_not_raise(self) -> None:
        """generate_puzzle completes normally when cancel_flag=[False]."""
        m = _meta()
        puzzle, solution = generate_puzzle(
            m.size, m.region_layout, m.symbols,
            seed=1, cancel_flag=[False],
        )
        assert solution is not None


class TestCheckUnique:
    def test_uniquely_solvable_returns_true(self) -> None:
        m = _meta()
        board: list[list[int | None]] = [list(row) for row in _puzzle_with_one_solution()]
        assert check_unique(m, board) is True

    def test_empty_board_returns_false(self) -> None:
        m = _meta()
        board: list[list[int | None]] = [[None] * 9 for _ in range(9)]
        assert check_unique(m, board) is False

    def test_cancel_flag_returns_false(self) -> None:
        m = _meta()
        board: list[list[int | None]] = [list(row) for row in _puzzle_with_one_solution()]
        assert check_unique(m, board, cancel_flag=[True]) is False
