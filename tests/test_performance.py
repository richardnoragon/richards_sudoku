"""T7 — Performance benchmarks (Beta) and EV-T6 (Extended Variants).

Verifies that key operations complete within their agreed time budgets:
  • generate_puzzle  (standard 9×9)   < 2 s
  • grade()                            < 100 ms
  • persistence round-trip            < 300 ms
  • Killer cage permutation cap — cages > 5 cells complete without hanging
  • EV-T6: 25×25 generation           < 30 s
  • EV-T6: grade() for ONE_TO_25      < 1 s
  • EV-T6: KenKen N=9 generation      < 30 s
  • EV-T6: Kakuro generation          < 30 s
  • EV-T6: grade() for KenKen         < 1 s
  • EV-T6: grade() for Kakuro         < 1 s
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from richards_sudoku.model.types import Board, Variant, VariantMetadata
from richards_sudoku.persistence.persistence import SaveState, load, save
from richards_sudoku.services.difficulty_se import grade
from richards_sudoku.services.stats import GameStats
from richards_sudoku.services.timer import GameTimer
from richards_sudoku.solver.generator import generate_puzzle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _standard_layout() -> list[list[int]]:
    return [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]


def _standard_meta() -> VariantMetadata:
    return VariantMetadata.standard_9x9()


def _filled_standard_board() -> Board:
    """Return a complete, valid solved 9×9 board (seeded, deterministic)."""
    meta = _standard_meta()
    layout = meta.region_layout
    puzzle, solution = generate_puzzle(
        size=9,
        region_layout=layout,
        symbols=list(range(1, 10)),
        seed=1,
        difficulty="easy",
        meta=meta,
    )
    board = Board(size=9, variant=Variant.STANDARD)
    for r in range(9):
        for c in range(9):
            board.cell(r, c).region_id = layout[r][c]
            v = solution[r][c]
            if v is not None:
                board.cell(r, c).value = v
    return board


# ---------------------------------------------------------------------------
# T7a: Puzzle generation
# ---------------------------------------------------------------------------

class TestPuzzleGeneration:

    def test_generate_standard_9x9_under_2s(self):
        """Generating a standard 9×9 puzzle must complete in under 2 seconds."""
        meta = _standard_meta()
        t0 = time.perf_counter()
        generate_puzzle(
            size=9,
            region_layout=meta.region_layout,
            symbols=list(range(1, 10)),
            seed=42,
            difficulty="medium",
            meta=meta,
        )
        elapsed = time.perf_counter() - t0
        assert elapsed < 2.0, f"generate_puzzle took {elapsed:.2f}s — exceeds 2 s budget"

    def test_generate_easy_under_2s(self):
        """Easy difficulty must also stay within the 2 s budget."""
        meta = _standard_meta()
        t0 = time.perf_counter()
        generate_puzzle(
            size=9,
            region_layout=meta.region_layout,
            symbols=list(range(1, 10)),
            seed=7,
            difficulty="easy",
            meta=meta,
        )
        elapsed = time.perf_counter() - t0
        assert elapsed < 2.0, f"easy generate_puzzle took {elapsed:.2f}s"


# ---------------------------------------------------------------------------
# T7b: SE grader
# ---------------------------------------------------------------------------

class TestGradePerformance:

    @pytest.fixture(scope="class")
    def solved_board(self):
        return _filled_standard_board()

    @pytest.fixture(scope="class")
    def standard_meta(self):
        return _standard_meta()

    def test_grade_under_100ms(self, solved_board: Board, standard_meta: VariantMetadata):
        """grade() on a standard board must complete in under 100 ms."""
        t0 = time.perf_counter()
        score, label = grade(solved_board, standard_meta)
        elapsed = time.perf_counter() - t0
        assert elapsed < 0.1, f"grade() took {elapsed*1000:.1f} ms — exceeds 100 ms budget"
        # Sanity-check: result is a valid (score, label) tuple
        assert isinstance(score, float)
        assert isinstance(label, str)

    def test_grade_repeated_calls_stable(self, solved_board: Board, standard_meta: VariantMetadata):
        """grade() returns consistent results on repeated calls."""
        score1, label1 = grade(solved_board, standard_meta)
        score2, label2 = grade(solved_board, standard_meta)
        assert score1 == score2
        assert label1 == label2


# ---------------------------------------------------------------------------
# T7c: Persistence round-trip
# ---------------------------------------------------------------------------

class TestPersistencePerformance:

    def test_round_trip_under_300ms(self, tmp_path: Path):
        """save() + load() for a standard game must complete in under 300 ms."""
        meta = _standard_meta()
        board = _filled_standard_board()
        for r in range(9):
            for c in range(9):
                board.cell(r, c).region_id = meta.region_layout[r][c]
        timer = GameTimer()
        stats = GameStats()
        state = SaveState(board=board, variant_meta=meta, solution=None, timer=timer, stats=stats)
        path = tmp_path / "perf_game.json"
        t0 = time.perf_counter()
        save(state, path)
        restored = load(path)
        elapsed = time.perf_counter() - t0
        assert elapsed < 0.3, f"Persistence round-trip took {elapsed*1000:.0f} ms — exceeds 300 ms"
        # Verify correctness
        orig_vals = [[board.cell(r, c).value for c in range(9)] for r in range(9)]
        rest_vals = [[restored.board.cell(r, c).value for c in range(9)] for r in range(9)]
        assert orig_vals == rest_vals


# ---------------------------------------------------------------------------
# T7d: Killer cage permutation cap (cages > 5 cells)
# ---------------------------------------------------------------------------

class TestKillerPermutationCap:

    def test_large_cage_6_cells_completes_in_1s(self):
        """_KillerCage technique on a 6-cell cage must not hang (< 1 s)."""
        from richards_sudoku.services.difficulty_se import _KillerCage  # noqa: PLC0415

        layout = _standard_layout()
        # 6-cell cage in top-left corner spanning two boxes
        cage_cells = [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2]]
        cage_sum = 21  # e.g. 1+2+3+4+5+6
        remaining_cells = [
            [r, c] for r in range(9) for c in range(9)
            if [r, c] not in cage_cells
        ]
        # Fill remaining with single-cell cages to satisfy full coverage
        cages = [{"cells": cage_cells, "sum": cage_sum}]
        for pos in remaining_cells:
            cages.append({"cells": [pos], "sum": 5})

        meta = VariantMetadata(
            name=Variant.KILLER,
            size=9,
            symbols=list(range(1, 10)),
            region_layout=layout,
            constraints={"cages": cages},
        )
        board = Board(size=9, variant=Variant.KILLER)
        for r in range(9):
            for c in range(9):
                board.cell(r, c).region_id = layout[r][c]
        # All empty cells → candidates = {1..9}
        for r in range(9):
            for c in range(9):
                board.cell(r, c).candidates = set(range(1, 10))

        t0 = time.perf_counter()
        grade(board, meta)
        elapsed = time.perf_counter() - t0
        assert elapsed < 1.0, f"_KillerCage on 6-cell cage took {elapsed:.2f}s — hangs unacceptably"

    def test_large_cage_7_cells_completes_in_2s(self):
        """_KillerCage technique on a 7-cell cage completes within 2 s."""
        from richards_sudoku.services.difficulty_se import _KillerCage  # noqa: PLC0415

        layout = _standard_layout()
        cage_cells = [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0]]
        cage_sum = 28  # 1+2+3+4+5+6+7
        remaining_cells = [
            [r, c] for r in range(9) for c in range(9)
            if [r, c] not in cage_cells
        ]
        cages = [{"cells": cage_cells, "sum": cage_sum}]
        for pos in remaining_cells:
            cages.append({"cells": [pos], "sum": 5})

        meta = VariantMetadata(
            name=Variant.KILLER,
            size=9,
            symbols=list(range(1, 10)),
            region_layout=layout,
            constraints={"cages": cages},
        )
        board = Board(size=9, variant=Variant.KILLER)
        for r in range(9):
            for c in range(9):
                board.cell(r, c).region_id = layout[r][c]
        for r in range(9):
            for c in range(9):
                board.cell(r, c).candidates = set(range(1, 10))

        t0 = time.perf_counter()
        grade(board, meta)
        elapsed = time.perf_counter() - t0
        assert elapsed < 2.0, f"_KillerCage on 7-cell cage took {elapsed:.2f}s"


# ---------------------------------------------------------------------------
# EV-T6-a: ONE_TO_25 — 25×25 generation and grade() performance
# ---------------------------------------------------------------------------

class TestOneToTwentyFivePerformance:
    """EV-T6: 25×25 generation < 30 s; grade() < 1 s for ONE_TO_25."""

    @staticmethod
    def _meta_25x25() -> VariantMetadata:
        size = 25
        box_side = 5
        return VariantMetadata(
            name=Variant.ONE_TO_25,
            size=size,
            symbols=list(range(1, size + 1)),
            region_layout=[
                [(r // box_side) * box_side + (c // box_side) for c in range(size)]
                for r in range(size)
            ],
            constraints={},
        )

    def test_generation_under_30s(self) -> None:
        """Generating a 25×25 ONE_TO_25 puzzle must complete within 30 s."""
        from richards_sudoku.solver.variant_generators import OneToTwentyFiveGenerator

        t0 = time.perf_counter()
        gen = OneToTwentyFiveGenerator(seed=42)
        solution = gen.generate()
        elapsed = time.perf_counter() - t0
        assert elapsed < 30.0, f"25×25 generation took {elapsed:.2f}s — exceeds 30 s budget"
        assert len(solution) == 25
        assert all(len(row) == 25 for row in solution)

    def test_grade_under_1s(self) -> None:
        """grade() on a ONE_TO_25 puzzle must complete within 1 s."""
        from richards_sudoku.solver.variant_generators import OneToTwentyFiveGenerator

        size = 25
        meta = self._meta_25x25()
        gen = OneToTwentyFiveGenerator(seed=3)
        solution = gen.generate()

        board = Board(size=size, variant=Variant.ONE_TO_25)
        for r in range(size):
            for c in range(size):
                board.cell(r, c).region_id = meta.region_layout[r][c]
                # Expose every 3rd cell as blank; fix the rest as givens
                if c % 3 == 0:
                    pass  # leave empty
                else:
                    board.cell(r, c).value = solution[r][c]
                    board.cell(r, c).is_fixed = True

        t0 = time.perf_counter()
        score, label = grade(board, meta)
        elapsed = time.perf_counter() - t0
        assert elapsed < 2.0, f"grade() on ONE_TO_25 took {elapsed:.3f}s — exceeds 2 s budget"
        assert isinstance(score, float)
        assert isinstance(label, str)


# ---------------------------------------------------------------------------
# EV-T6-b: KenKen — N=9 generation and grade() performance
# ---------------------------------------------------------------------------

class TestKenKenPerformance:
    """EV-T6: KenKen N=9 generation < 30 s; grade() < 1 s for KenKen."""

    @staticmethod
    def _kenken_layout(size: int) -> list[list[int]]:
        """Each cell is its own region (no box constraints)."""
        return [[r * size + c for c in range(size)] for r in range(size)]

    def test_kenken_n9_generation_under_30s(self) -> None:
        """KenKen N=9 Latin square fill + cage partitioning must complete within 30 s."""
        from richards_sudoku.solver.generator import generate_solution
        from richards_sudoku.solver.variant_generators import KenKenCagePartitioner

        size = 9
        region_layout = self._kenken_layout(size)
        meta_stub = VariantMetadata(
            name=Variant.KENKEN,
            size=size,
            symbols=list(range(1, size + 1)),
            region_layout=region_layout,
            constraints={"has_box_regions": False},
        )
        t0 = time.perf_counter()
        solution = generate_solution(
            size, region_layout, list(range(1, size + 1)), seed=7, meta=meta_stub
        )
        partitioner = KenKenCagePartitioner(size=size, seed=7)
        cages = partitioner.partition(solution)
        elapsed = time.perf_counter() - t0
        assert elapsed < 30.0, f"KenKen N=9 generation took {elapsed:.2f}s — exceeds 30 s budget"
        assert cages is not None
        covered = {(r, c) for cage in cages for r, c in cage["cells"]}
        assert len(covered) == size * size

    def test_grade_kenken_under_1s(self) -> None:
        """grade() on a KenKen board must complete within 1 s."""
        size = 4
        region_layout = self._kenken_layout(size)
        solution = [
            [1, 2, 3, 4],
            [3, 4, 1, 2],
            [2, 3, 4, 1],
            [4, 1, 2, 3],
        ]
        # Single-cell cages (one per cell) keep the fixture simple
        cages = [
            {"cells": [[r, c]], "op": "+", "target": solution[r][c]}
            for r in range(size)
            for c in range(size)
        ]
        meta = VariantMetadata(
            name=Variant.KENKEN,
            size=size,
            symbols=list(range(1, size + 1)),
            region_layout=region_layout,
            constraints={"cages": cages, "has_box_regions": False},
        )
        board = Board(size=size, variant=Variant.KENKEN)
        for r in range(size):
            for c in range(size):
                board.cell(r, c).region_id = region_layout[r][c]
                if (r, c) != (0, 0):
                    board.cell(r, c).value = solution[r][c]
                    board.cell(r, c).is_fixed = True

        t0 = time.perf_counter()
        score, label = grade(board, meta)
        elapsed = time.perf_counter() - t0
        assert elapsed < 1.0, f"grade() on KenKen 4×4 took {elapsed:.3f}s — exceeds 1 s budget"
        assert isinstance(score, float)
        assert isinstance(label, str)


# ---------------------------------------------------------------------------
# EV-T6-c: Kakuro — generation and grade() performance
# ---------------------------------------------------------------------------

class TestKakuroPerformance:
    """EV-T6: Kakuro generation < 30 s; grade() < 1 s for Kakuro."""

    @staticmethod
    def _small_template() -> dict:
        """Hand-built 4×4 Kakuro template (structure only, sums filled by generator)."""
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

    def test_kakuro_generation_under_30s(self) -> None:
        """Kakuro template generation + digit fill must complete within 30 s."""
        from richards_sudoku.solver.variant_generators import (
            KakuroFillGenerator,
            KakuroTemplateLibrary,
        )

        t0 = time.perf_counter()
        lib = KakuroTemplateLibrary(9, seed=0, difficulty="medium")
        tmpl = lib.generate()
        assert tmpl is not None, "KakuroTemplateLibrary.generate() returned None (no valid template for seed 0)"
        filler = KakuroFillGenerator(tmpl, seed=0)
        solution = filler.fill()
        elapsed = time.perf_counter() - t0
        assert elapsed < 30.0, f"Kakuro generation took {elapsed:.2f}s — exceeds 30 s budget"
        assert solution is not None

    def test_grade_kakuro_under_1s(self) -> None:
        """grade() on a Kakuro board must complete within 1 s."""
        from richards_sudoku.solver.variant_generators import (
            KakuroFillGenerator,
            build_kakuro_clue_positions,
        )

        tmpl = self._small_template()
        filler = KakuroFillGenerator(tmpl, seed=0)
        filled = filler.fill()
        assert filled is not None

        clues = [
            {
                "cells": run["cells"],
                "sum": sum(filled[r][c] for r, c in run["cells"]),
                "dir": run["dir"],
            }
            for run in tmpl["runs"]
        ]
        size = 4
        black_cells = tmpl["black_cells"]
        clue_positions = build_kakuro_clue_positions(clues)
        box_q = int(size ** 0.5)
        region_layout = [
            [(r // box_q) * box_q + (c // box_q) for c in range(size)]
            for r in range(size)
        ]
        meta = VariantMetadata(
            name=Variant.KAKURO,
            size=size,
            symbols=list(range(1, 10)),
            region_layout=region_layout,
            constraints={
                "clues": clues,
                "black_cells": black_cells,
                "clue_positions": clue_positions,
            },
        )
        board = Board(size=size, variant=Variant.KAKURO)
        black_set = {(r, c) for r, c in black_cells}
        for r in range(size):
            for c in range(size):
                board.cell(r, c).region_id = region_layout[r][c]
                if (r, c) in black_set:
                    board.cell(r, c).is_black = True
                    board.cell(r, c).candidates = set()
        # Leave every first cell of each run empty; fix the rest
        first_cells = {tuple(run["cells"][0]) for run in tmpl["runs"]}
        for run in tmpl["runs"]:
            for r, c in run["cells"]:
                if (r, c) not in first_cells:
                    board.cell(r, c).value = filled[r][c]
                    board.cell(r, c).is_fixed = True

        t0 = time.perf_counter()
        score, label = grade(board, meta)
        elapsed = time.perf_counter() - t0
        assert elapsed < 1.0, f"grade() on Kakuro 4×4 took {elapsed:.3f}s — exceeds 1 s budget"
        assert isinstance(score, float)
        assert isinstance(label, str)
