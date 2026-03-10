"""K5 / EV-T2 — Tests for the ONE_TO_25 variant."""
from __future__ import annotations

import time

import pytest

from richards_sudoku.model.types import Board, Variant, VariantMetadata
from richards_sudoku.solver.variant_generators import OneToTwentyFiveGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_25x25_meta() -> VariantMetadata:
    size = 25
    box = 5
    layout = [[(r // box) * box + (c // box) for c in range(size)] for r in range(size)]
    return VariantMetadata(
        name=Variant.ONE_TO_25,
        size=size,
        symbols=list(range(1, size + 1)),
        region_layout=layout,
    )


def _is_valid_25x25(grid: list[list[int]]) -> bool:
    """Return True iff grid is a valid 25×25 Sudoku solution."""
    size = 25
    box = 5
    expected = set(range(1, size + 1))
    for r in range(size):
        if set(grid[r]) != expected:
            return False
    for c in range(size):
        if {grid[r][c] for r in range(size)} != expected:
            return False
    for br in range(box):
        for bc in range(box):
            box_vals = {
                grid[br * box + i][bc * box + j]
                for i in range(box)
                for j in range(box)
            }
            if box_vals != expected:
                return False
    return True


# ---------------------------------------------------------------------------
# Generator tests
# ---------------------------------------------------------------------------

class TestOneToTwentyFiveGenerator:
    def test_generates_valid_solution(self) -> None:
        gen = OneToTwentyFiveGenerator(seed=42)
        sol = gen.generate()
        assert len(sol) == 25
        assert all(len(row) == 25 for row in sol)
        assert _is_valid_25x25(sol)

    def test_different_seeds_produce_different_solutions(self) -> None:
        s1 = OneToTwentyFiveGenerator(seed=1).generate()
        s2 = OneToTwentyFiveGenerator(seed=2).generate()
        assert s1 != s2

    def test_same_seed_is_reproducible(self) -> None:
        s1 = OneToTwentyFiveGenerator(seed=99).generate()
        s2 = OneToTwentyFiveGenerator(seed=99).generate()
        assert s1 == s2

    def test_cancel_flag_returns_empty(self) -> None:
        gen = OneToTwentyFiveGenerator(seed=7)
        result = gen.generate(cancel_flag=[True])
        assert result == []

    def test_generation_speed(self) -> None:
        """Band-shuffle should complete in well under 1 second."""
        t0 = time.time()
        for i in range(10):
            OneToTwentyFiveGenerator(seed=i).generate()
        elapsed = time.time() - t0
        assert elapsed < 5.0, f"10 × 25×25 generation took {elapsed:.2f}s (expected < 5s)"

    def test_rng_threading(self) -> None:
        """Results differ when a shared rng is used vs fresh seed."""
        import random
        rng = random.Random(42)
        s1 = OneToTwentyFiveGenerator(seed=42, rng=rng).generate()
        assert _is_valid_25x25(s1)


# ---------------------------------------------------------------------------
# Uniqueness / clue-removal smoke (K5: terminates within 30 s budget)
# ---------------------------------------------------------------------------

class TestOneToTwentyFiveUniqueness:
    @pytest.mark.slow
    def test_check_unique_25x25_terminates(self) -> None:
        """A filled 25×25 grid with one cell removed is unique — verify terminates."""
        gen = OneToTwentyFiveGenerator(seed=11)
        solution = gen.generate()
        meta = _make_25x25_meta()

        puzzle = [row[:] for row in solution]
        puzzle[0][0] = None  # remove one cell

        from richards_sudoku.solver.generator import check_unique
        t0 = time.time()
        result = check_unique(meta, puzzle)
        elapsed = time.time() - t0
        assert result is True
        assert elapsed < 30.0, f"check_unique took {elapsed:.2f}s (budget: 30s)"


# ---------------------------------------------------------------------------
# Text format round-trip (K4 / K5)
# ---------------------------------------------------------------------------

class TestOneToTwentyFiveTextFormat:
    def _build_puzzle_and_solution(self, seed: int = 5) -> tuple:
        gen = OneToTwentyFiveGenerator(seed=seed)
        solution = gen.generate()
        # Expose ~250 givens (medium ≈ 246 for 25×25)
        puzzle = [row[:] for row in solution]
        for r in range(25):
            for c in range(0, 25, 4):  # blank every 4th cell
                puzzle[r][c] = None
        return puzzle, solution

    def test_export_import_round_trip(self) -> None:
        from richards_sudoku.services.text_format import export_text, import_text

        puzzle, _ = self._build_puzzle_and_solution()
        meta = _make_25x25_meta()
        exported = export_text(puzzle, {"name": "1to25", "size": 25}, seed=5, difficulty="medium")

        assert "variant: 1to25" in exported
        assert "size: 25" in exported
        # digit rows must be space-separated
        digit_lines = [ln for ln in exported.splitlines() if ln and not ln.startswith(("variant", "seed", "difficulty", "size"))]
        assert len(digit_lines) == 25
        tokens = digit_lines[0].split()
        assert len(tokens) == 25

        board_vals, meta_dict, seed, diff = import_text(exported)
        assert meta_dict["size"] == 25
        assert meta_dict["name"] == "1to25"
        assert len(board_vals) == 25
        assert all(len(row) == 25 for row in board_vals)
        assert board_vals == puzzle

    def test_import_wrong_row_length_raises(self) -> None:
        from richards_sudoku.services.text_format import import_text

        lines = ["variant: 1to25", "size: 25", "seed: 1", "difficulty: easy"]
        # Only one digit row with wrong token count
        lines.append("1 2 3")  # 3 tokens instead of 25
        lines += ["0 " * 25] * 24

        with pytest.raises(ValueError):
            import_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Persistence round-trip (K5)
# ---------------------------------------------------------------------------

class TestOneToTwentyFivePersistence:
    def test_persistence_round_trip(self, tmp_path) -> None:
        from richards_sudoku.persistence.persistence import save, load, SaveState
        from richards_sudoku.services.timer import GameTimer
        from richards_sudoku.services.stats import GameStats

        gen = OneToTwentyFiveGenerator(seed=3)
        solution = gen.generate()
        puzzle = [row[:] for row in solution]
        puzzle[2][3] = None

        meta = _make_25x25_meta()
        size = meta.size
        board = Board(size=size, variant=Variant.ONE_TO_25)
        for r in range(size):
            for c in range(size):
                cell = board.cell(r, c)
                cell.region_id = meta.region_layout[r][c]
                v = puzzle[r][c]
                if v is not None:
                    cell.value = v
                    cell.is_fixed = True

        timer = GameTimer()
        stats = GameStats()
        state = SaveState(
            board=board,
            variant_meta=meta,
            solution=solution,
            timer=timer,
            stats=stats,
        )

        fpath = tmp_path / "one_to_25.json"
        save(state, fpath)
        loaded = load(fpath)

        assert loaded.variant_meta.size == 25
        assert loaded.variant_meta.name == Variant.ONE_TO_25
        assert loaded.board.size == 25


# ---------------------------------------------------------------------------
# UI smoke (K5)
# ---------------------------------------------------------------------------

@pytest.mark.qt
class TestOneToTwentyFiveUISmoke:
    def test_grid_renders_25x25(self, qtbot) -> None:
        from richards_sudoku.ui.grid_widget import SudokuGridWidget

        gen = OneToTwentyFiveGenerator(seed=17)
        solution = gen.generate()
        puzzle = [row[:] for row in solution]
        puzzle[0][0] = None

        meta = _make_25x25_meta()
        size = 25
        board = Board(size=size, variant=Variant.ONE_TO_25)
        for r in range(size):
            for c in range(size):
                cell = board.cell(r, c)
                cell.region_id = meta.region_layout[r][c]
                v = puzzle[r][c]
                if v is not None:
                    cell.value = v
                    cell.is_fixed = True

        widget = SudokuGridWidget()
        qtbot.addWidget(widget)
        widget.resize(700, 700)
        widget.set_board(board, meta)
        widget.show()
        qtbot.waitExposed(widget)

        # sizeHint should scale with 25×25
        hint = widget.sizeHint()
        assert hint.width() == 25 * SudokuGridWidget._PREFERRED_CELL_PX
        assert hint.height() == 25 * SudokuGridWidget._PREFERRED_CELL_PX

    def test_cell_selection_25x25(self, qtbot) -> None:
        from PyQt6.QtCore import Qt
        from richards_sudoku.ui.grid_widget import SudokuGridWidget

        gen = OneToTwentyFiveGenerator(seed=21)
        solution = gen.generate()
        puzzle = [row[:] for row in solution]

        meta = _make_25x25_meta()
        size = 25
        board = Board(size=size, variant=Variant.ONE_TO_25)
        for r in range(size):
            for c in range(size):
                cell = board.cell(r, c)
                cell.region_id = meta.region_layout[r][c]
                v = puzzle[r][c]
                if v is not None:
                    cell.value = v
                    cell.is_fixed = True

        widget = SudokuGridWidget()
        qtbot.addWidget(widget)
        size_px = 700
        widget.resize(size_px, size_px)
        widget.set_board(board, meta)
        widget.show()
        qtbot.waitExposed(widget)

        # Click on ~row 12, col 12 (centre of board)
        cell_px = size_px / 25
        x = int(12.5 * cell_px)
        y = int(12.5 * cell_px)
        from PyQt6.QtCore import QPoint
        qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=QPoint(x, y))

        sel = widget._selected
        assert sel is not None
        assert 10 <= sel[0] <= 14
        assert 10 <= sel[1] <= 14
