"""M9 — KenKen variant tests.

Covers:
- M1: KenKenCagePartitioner (cage structure, coverage, ops, targets)
- M5: _KenKenCage SE technique (arithmetic elimination for +, *, -, /)
- M6: game_controller.is_complete KenKen arithmetic check
- M7: persistence validation (missing cages, overlap, coverage, bad op)
- M8: text_format export/import round-trip for KenKen
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from richards_sudoku.model.types import Board, Cell, Variant, VariantMetadata
from richards_sudoku.services.difficulty_se import (
    _KenKenCage,
    _KillerCage,
    _WorkingGrid,
    grade,
)
from richards_sudoku.services.text_format import export_text, import_text
from richards_sudoku.solver.variant_generators import KenKenCagePartitioner


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _kenken_layout(size: int) -> list[list[int]]:
    """KenKen region layout: each cell is its own region."""
    return [[r * size + c for c in range(size)] for r in range(size)]


def _kenken_meta(size: int, cages: list[dict]) -> VariantMetadata:
    return VariantMetadata(
        name=Variant.KENKEN,
        size=size,
        symbols=list(range(1, size + 1)),
        region_layout=_kenken_layout(size),
        constraints={"cages": cages, "has_box_regions": False},
    )


def _solved_4x4() -> list[list[int]]:
    """A valid 4×4 Latin square (rows and columns each contain 1–4)."""
    return [
        [1, 2, 3, 4],
        [2, 1, 4, 3],
        [3, 4, 1, 2],
        [4, 3, 2, 1],
    ]


def _board_from_solution(
    solution: list[list[int]],
    holes: set[tuple[int, int]],
    variant: Variant = Variant.KENKEN,
) -> Board:
    size = len(solution)
    board = Board(size=size, variant=variant)
    for r in range(size):
        for c in range(size):
            if (r, c) not in holes:
                cell = board.cell(r, c)
                cell.value = solution[r][c]
                cell.is_fixed = True
    return board


# ---------------------------------------------------------------------------
# M1 — KenKenCagePartitioner
# ---------------------------------------------------------------------------

class TestKenKenCagePartitioner:

    def _partition_4x4(self, seed: int = 0) -> list[dict]:
        solution = _solved_4x4()
        p = KenKenCagePartitioner(size=4, seed=seed)
        return p.partition(solution)

    def test_full_coverage(self) -> None:
        """Cages must cover every cell exactly once."""
        cages = self._partition_4x4()
        covered: set[tuple[int, int]] = set()
        for cage in cages:
            for r, c in cage["cells"]:
                key = (r, c)
                assert key not in covered, f"Cell {key} appears in multiple cages"
                covered.add(key)
        assert covered == {(r, c) for r in range(4) for c in range(4)}

    def test_required_keys(self) -> None:
        """Each cage dict must have 'cells', 'op', and 'target' keys."""
        for cage in self._partition_4x4():
            assert "cells" in cage
            assert "op" in cage
            assert "target" in cage

    def test_valid_ops(self) -> None:
        """All ops must be one of +, -, *, /."""
        valid_ops = {"+", "-", "*", "/"}
        for cage in self._partition_4x4():
            assert cage["op"] in valid_ops, f"Invalid op: {cage['op']!r}"

    def test_positive_targets(self) -> None:
        """All targets must be positive integers."""
        for cage in self._partition_4x4():
            assert isinstance(cage["target"], int)
            assert cage["target"] > 0

    def test_single_cell_cage_has_plus_op(self) -> None:
        """Single-cell cages always use op '+' and target == cell value."""
        solution = _solved_4x4()
        cages = self._partition_4x4()
        for cage in cages:
            if len(cage["cells"]) == 1:
                assert cage["op"] == "+"
                r, c = cage["cells"][0]
                assert cage["target"] == solution[r][c]

    def test_target_arithmetic_correct(self) -> None:
        """For each cage, the op applied to cell values must equal the target."""
        solution = _solved_4x4()
        for cage in self._partition_4x4(seed=42):
            vals = [solution[r][c] for r, c in cage["cells"]]
            op = cage["op"]
            target = cage["target"]
            if op == "+":
                assert sum(vals) == target
            elif op == "*":
                p = 1
                for v in vals:
                    p *= v
                assert p == target
            elif op == "-":
                assert max(vals) - min(vals) == target
            elif op == "/":
                big, small = max(vals), min(vals)
                assert small != 0 and big % small == 0
                assert big // small == target

    def test_cancel_flag_raises(self) -> None:
        """A pre-set cancel flag must raise RuntimeError."""
        solution = _solved_4x4()
        p = KenKenCagePartitioner(size=4, seed=0)
        with pytest.raises(RuntimeError):
            p.partition(solution, cancel_flag=[True])

    def test_different_seeds_may_differ(self) -> None:
        """Different seeds should (usually) produce different cage layouts."""
        c0 = self._partition_4x4(seed=0)
        c1 = self._partition_4x4(seed=999)
        # At least the cage count or first cage cells should differ
        differ = len(c0) != len(c1) or any(
            c0[i]["cells"] != c1[i]["cells"] for i in range(min(len(c0), len(c1)))
        )
        assert differ, "Seeds 0 and 999 produced identical partitions"


# ---------------------------------------------------------------------------
# M5 — _KenKenCage SE technique
# ---------------------------------------------------------------------------

class TestKenKenCageTechnique:

    def _make_grid(self, size: int, cages: list[dict]) -> _WorkingGrid:
        board = Board(size=size, variant=Variant.KENKEN)
        meta = _kenken_meta(size, cages)
        return _WorkingGrid(board, meta)

    def test_does_not_fire_for_non_kenken_variant(self) -> None:
        """_KenKenCage must not fire on a Standard grid."""
        board = Board(size=9, variant=Variant.STANDARD)
        meta = VariantMetadata.standard_9x9()
        grid = _WorkingGrid(board, meta)
        tech = _KenKenCage()
        assert tech.apply(grid) is False

    def test_does_not_fire_when_no_cages(self) -> None:
        """_KenKenCage must not fire when constraints has no cages."""
        board = Board(size=4, variant=Variant.KENKEN)
        meta = VariantMetadata(
            name=Variant.KENKEN,
            size=4,
            symbols=list(range(1, 5)),
            region_layout=_kenken_layout(4),
            constraints={"has_box_regions": False},
        )
        grid = _WorkingGrid(board, meta)
        tech = _KenKenCage()
        assert tech.apply(grid) is False

    def test_addition_cage_eliminates_invalid(self) -> None:
        """+ cage with sum 3 on 2 cells should restrict candidates to {1,2}."""
        cages = [{"cells": [[0, 0], [0, 1]], "op": "+", "target": 3}]
        grid = self._make_grid(4, cages)
        # Reset candidates to full so the technique can fire again
        for c in range(4):
            grid.candidates[0][c] = {1, 2, 3, 4}
        grid.values[0][0] = None
        grid.values[0][1] = None
        tech = _KenKenCage()
        changed = tech.apply(grid)
        assert changed is True
        assert grid.candidates[0][0] <= {1, 2}
        assert grid.candidates[0][1] <= {1, 2}

    def test_multiplication_cage_eliminates_invalid(self) -> None:
        """* cage with target 2 on 2 cells from {1..4} → only {1,2} or {2,1}."""
        cages = [{"cells": [[0, 0], [0, 1]], "op": "*", "target": 2}]
        grid = self._make_grid(4, cages)
        # Reset candidates to full
        for c in range(4):
            grid.candidates[0][c] = {1, 2, 3, 4}
        grid.values[0][0] = None
        grid.values[0][1] = None
        tech = _KenKenCage()
        changed = tech.apply(grid)
        assert changed is True
        # Only 1×2=2 is valid (same-row peers rule out {2,1} having both 2s)
        assert grid.candidates[0][0] <= {1, 2}
        assert grid.candidates[0][1] <= {1, 2}

    def test_subtraction_cage_eliminates_invalid(self) -> None:
        """- cage with target 3 on 2 cells: only {1,4}/{4,1} valid in {1..4}."""
        cages = [{"cells": [[1, 0], [2, 0]], "op": "-", "target": 3}]
        grid = self._make_grid(4, cages)
        # Reset candidates to full so technique can fire
        grid.candidates[1][0] = {1, 2, 3, 4}
        grid.candidates[2][0] = {1, 2, 3, 4}
        grid.values[1][0] = None
        grid.values[2][0] = None
        tech = _KenKenCage()
        changed = tech.apply(grid)
        assert changed is True
        # Only |a-b|=3 pairs from {1,2,3,4}: (1,4) and (4,1)
        assert grid.candidates[1][0] <= {1, 4}
        assert grid.candidates[2][0] <= {1, 4}

    def test_division_cage_eliminates_invalid(self) -> None:
        """/ cage with target 2 on 2 cells: valid if big÷small=2."""
        cages = [{"cells": [[1, 0], [2, 0]], "op": "/", "target": 2}]
        grid = self._make_grid(4, cages)
        # Reset candidates to full
        grid.candidates[1][0] = {1, 2, 3, 4}
        grid.candidates[2][0] = {1, 2, 3, 4}
        grid.values[1][0] = None
        grid.values[2][0] = None
        tech = _KenKenCage()
        changed = tech.apply(grid)
        assert changed is True
        # Valid pairs with big//small==2 from {1,2,3,4}: (2,1),(1,2),(4,2),(2,4)
        assert grid.candidates[1][0] <= {1, 2, 4}
        assert grid.candidates[2][0] <= {1, 2, 4}

    def test_single_cell_cage_seeds_value(self) -> None:
        """SE-V3: single-cell cage with target 3 should be placed during init."""
        cages = (
            [{"cells": [[r, c]], "op": "+", "target": v} for r in range(4) for c, v in enumerate([1, 2, 3, 4])]
            + [{"cells": [[r, c]], "op": "+", "target": v} for r in range(1, 4) for c, v in enumerate([2, 1, 4, 3])]
        )
        # Just check a minimal case: one single-cell cage for row 0, col 2 → target 3
        cages_simple = [
            {"cells": [[0, 2]], "op": "+", "target": 3},
        ] + [
            {"cells": [[r, c]], "op": "+", "target": 1}
            for r in range(4) for c in range(4) if (r, c) != (0, 2)
        ]
        grid = self._make_grid(4, cages_simple)
        # SE-V3 should have seeded (0,2) = 3 during _WorkingGrid init
        assert grid.values[0][2] == 3

    def test_kenken_cage_grade_does_not_crash(self) -> None:
        """grade() on a KenKen board with all-single-cell cages must not raise."""
        solution = _solved_4x4()
        holes: set[tuple[int, int]] = {(0, 0), (1, 1)}
        cages = [
            {"cells": [[r, c]], "op": "+", "target": solution[r][c]}
            for r in range(4) for c in range(4)
            if (r, c) in holes
        ]
        board = _board_from_solution(solution, holes)
        meta = _kenken_meta(4, cages)
        score, label = grade(board, meta)
        assert isinstance(score, float)
        assert isinstance(label, str)


# ---------------------------------------------------------------------------
# M6 — game_controller.is_complete KenKen check
# ---------------------------------------------------------------------------

class TestKenKenIsComplete:

    def _make_controller(self, solution: list[list[int]], cages: list[dict]) -> object:
        from richards_sudoku.controller.game_controller import GameController
        size = len(solution)
        meta = _kenken_meta(size, cages)
        board = Board(size=size, variant=Variant.KENKEN)
        for r in range(size):
            for c in range(size):
                cell = board.cell(r, c)
                cell.value = solution[r][c]
                cell.region_id = meta.region_layout[r][c]
        mock_grid = MagicMock()
        ctrl = GameController(mock_grid)
        ctrl._board = board
        ctrl._meta = meta
        return ctrl

    def test_complete_valid_board_returns_true(self) -> None:
        sol = _solved_4x4()
        cages = [
            {"cells": [[0, 0], [0, 1]], "op": "+", "target": sol[0][0] + sol[0][1]},
            {"cells": [[0, 2], [0, 3]], "op": "+", "target": sol[0][2] + sol[0][3]},
            {"cells": [[1, 0], [1, 1]], "op": "+", "target": sol[1][0] + sol[1][1]},
            {"cells": [[1, 2], [1, 3]], "op": "+", "target": sol[1][2] + sol[1][3]},
            {"cells": [[2, 0], [2, 1]], "op": "+", "target": sol[2][0] + sol[2][1]},
            {"cells": [[2, 2], [2, 3]], "op": "+", "target": sol[2][2] + sol[2][3]},
            {"cells": [[3, 0], [3, 1]], "op": "+", "target": sol[3][0] + sol[3][1]},
            {"cells": [[3, 2], [3, 3]], "op": "+", "target": sol[3][2] + sol[3][3]},
        ]
        ctrl = self._make_controller(sol, cages)
        assert ctrl.is_complete is True

    def test_wrong_cage_sum_returns_false(self) -> None:
        sol = _solved_4x4()
        cages = [
            {"cells": [[0, 0], [0, 1]], "op": "+", "target": 999},  # wrong
            {"cells": [[0, 2], [0, 3]], "op": "+", "target": sol[0][2] + sol[0][3]},
            {"cells": [[1, 0], [1, 1]], "op": "+", "target": sol[1][0] + sol[1][1]},
            {"cells": [[1, 2], [1, 3]], "op": "+", "target": sol[1][2] + sol[1][3]},
            {"cells": [[2, 0], [2, 1]], "op": "+", "target": sol[2][0] + sol[2][1]},
            {"cells": [[2, 2], [2, 3]], "op": "+", "target": sol[2][2] + sol[2][3]},
            {"cells": [[3, 0], [3, 1]], "op": "+", "target": sol[3][0] + sol[3][1]},
            {"cells": [[3, 2], [3, 3]], "op": "+", "target": sol[3][2] + sol[3][3]},
        ]
        ctrl = self._make_controller(sol, cages)
        assert ctrl.is_complete is False

    def test_multiplication_cage_passes(self) -> None:
        sol = _solved_4x4()
        cages = [
            {"cells": [[0, 0]], "op": "+", "target": sol[0][0]},
            {"cells": [[0, 1]], "op": "+", "target": sol[0][1]},
            {"cells": [[0, 2]], "op": "+", "target": sol[0][2]},
            {"cells": [[0, 3]], "op": "+", "target": sol[0][3]},
            {"cells": [[1, 0], [2, 0]], "op": "*", "target": sol[1][0] * sol[2][0]},
            {"cells": [[1, 1], [2, 1]], "op": "-", "target": abs(sol[1][1] - sol[2][1])},
            {"cells": [[1, 2], [2, 2]], "op": "/", "target": max(sol[1][2], sol[2][2]) // min(sol[1][2], sol[2][2])},
            {"cells": [[1, 3], [2, 3]], "op": "+", "target": sol[1][3] + sol[2][3]},
            {"cells": [[3, 0]], "op": "+", "target": sol[3][0]},
            {"cells": [[3, 1]], "op": "+", "target": sol[3][1]},
            {"cells": [[3, 2]], "op": "+", "target": sol[3][2]},
            {"cells": [[3, 3]], "op": "+", "target": sol[3][3]},
        ]
        ctrl = self._make_controller(sol, cages)
        assert ctrl.is_complete is True

    def test_empty_cell_returns_false(self) -> None:
        from richards_sudoku.controller.game_controller import GameController
        sol = _solved_4x4()
        cages = [{"cells": [[r, c]], "op": "+", "target": sol[r][c]} for r in range(4) for c in range(4)]
        meta = _kenken_meta(4, cages)
        board = Board(size=4, variant=Variant.KENKEN)
        # Leave (0,0) empty
        for r in range(4):
            for c in range(4):
                if (r, c) != (0, 0):
                    cell = board.cell(r, c)
                    cell.value = sol[r][c]
                    cell.region_id = meta.region_layout[r][c]
        mock_grid = MagicMock()
        ctrl = GameController(mock_grid)
        ctrl._board = board
        ctrl._meta = meta
        assert ctrl.is_complete is False


# ---------------------------------------------------------------------------
# M7 — persistence validation
# ---------------------------------------------------------------------------

class TestKenKenPersistence:

    def _meta(self, size: int, cages: list[dict]) -> VariantMetadata:
        return _kenken_meta(size, cages)

    def _full_single_cages(self, size: int) -> list[dict]:
        """Trivial all-single-cell KenKen cage set for a SIZE×SIZE grid."""
        return [
            {"cells": [[r, c]], "op": "+", "target": (r + c) % size + 1}
            for r in range(size)
            for c in range(size)
        ]

    def test_valid_meta_does_not_raise(self) -> None:
        from richards_sudoku.persistence.persistence import _validate_variant_constraints
        cages = self._full_single_cages(4)
        meta = self._meta(4, cages)
        _validate_variant_constraints(meta)  # must not raise

    def test_missing_cages_raises(self) -> None:
        from richards_sudoku.persistence.persistence import _validate_variant_constraints
        meta = VariantMetadata(
            name=Variant.KENKEN,
            size=4,
            symbols=list(range(1, 5)),
            region_layout=_kenken_layout(4),
            constraints={"has_box_regions": False},  # no 'cages' key
        )
        with pytest.raises(ValueError, match="non-empty 'cages'"):
            _validate_variant_constraints(meta)

    def test_empty_cages_list_raises(self) -> None:
        from richards_sudoku.persistence.persistence import _validate_variant_constraints
        meta = VariantMetadata(
            name=Variant.KENKEN,
            size=4,
            symbols=list(range(1, 5)),
            region_layout=_kenken_layout(4),
            constraints={"cages": [], "has_box_regions": False},
        )
        with pytest.raises(ValueError, match="non-empty 'cages'"):
            _validate_variant_constraints(meta)

    def test_cage_missing_op_raises(self) -> None:
        from richards_sudoku.persistence.persistence import _validate_variant_constraints
        cages = self._full_single_cages(4)
        del cages[0]["op"]
        meta = self._meta(4, cages)
        with pytest.raises(ValueError, match="'op'"):
            _validate_variant_constraints(meta)

    def test_cage_missing_target_raises(self) -> None:
        from richards_sudoku.persistence.persistence import _validate_variant_constraints
        cages = self._full_single_cages(4)
        del cages[0]["target"]
        meta = self._meta(4, cages)
        with pytest.raises(ValueError, match="'target'"):
            _validate_variant_constraints(meta)

    def test_invalid_op_raises(self) -> None:
        from richards_sudoku.persistence.persistence import _validate_variant_constraints
        cages = self._full_single_cages(4)
        cages[0]["op"] = "^"  # not a valid op
        meta = self._meta(4, cages)
        with pytest.raises(ValueError, match="op must be one of"):
            _validate_variant_constraints(meta)

    def test_cell_overlap_raises(self) -> None:
        from richards_sudoku.persistence.persistence import _validate_variant_constraints
        cages = self._full_single_cages(4)
        # Duplicate cell (0,0) in a second cage
        cages.append({"cells": [[0, 0]], "op": "+", "target": 1})
        meta = self._meta(4, cages)
        with pytest.raises(ValueError, match="overlap"):
            _validate_variant_constraints(meta)

    def test_incomplete_coverage_raises(self) -> None:
        from richards_sudoku.persistence.persistence import _validate_variant_constraints
        # Only put 15 cages (missing one cell)
        cages = self._full_single_cages(4)[:-1]
        meta = self._meta(4, cages)
        with pytest.raises(ValueError, match="cover"):
            _validate_variant_constraints(meta)


# ---------------------------------------------------------------------------
# M8 — text_format export / import
# ---------------------------------------------------------------------------

class TestKenKenTextFormat:

    _SOL = _solved_4x4()

    def _puzzle_none(self) -> list[list[int | None]]:
        """Return all-None 4×4 puzzle (empty)."""
        return [[None] * 4 for _ in range(4)]

    def _full_cages_4x4(self) -> list[dict]:
        """Two-cell cages covering the full 4×4 grid (row pairs)."""
        sol = self._SOL
        cages = []
        for r in range(4):
            for c in range(0, 4, 2):
                cages.append({
                    "cells": [[r, c], [r, c + 1]],
                    "op": "+",
                    "target": sol[r][c] + sol[r][c + 1],
                })
        return cages

    def _meta_dict(self, cages: list[dict]) -> dict:
        return {
            "name": "kenken",
            "size": 4,
            "symbols": [1, 2, 3, 4],
            "region_layout": _kenken_layout(4),
            "constraints": {"cages": cages, "has_box_regions": False},
        }

    def test_export_contains_cage_lines(self) -> None:
        cages = self._full_cages_4x4()
        text = export_text(self._puzzle_none(), self._meta_dict(cages), seed=7)
        assert "cage:" in text

    def test_export_cage_line_format(self) -> None:
        """Each cage line must contain op and target separated by ':'."""
        cages = self._full_cages_4x4()
        text = export_text(self._puzzle_none(), self._meta_dict(cages), seed=0)
        cage_lines = [ln for ln in text.splitlines() if ln.startswith("cage:")]
        assert len(cage_lines) == len(cages)
        for line in cage_lines:
            # Format: "cage: r,c r,c:op:target"
            parts = line[len("cage: "):].rsplit(":", 2)
            assert len(parts) == 3, f"Bad cage line: {line!r}"
            _, op, target_str = parts
            assert op.strip() in {"+", "-", "*", "/"}
            assert int(target_str.strip()) > 0

    def test_import_round_trip(self) -> None:
        """Export then import must preserve cage count, ops, and targets."""
        cages = self._full_cages_4x4()
        text = export_text(self._puzzle_none(), self._meta_dict(cages), seed=5, difficulty="easy")
        board_vals, meta_dict, seed, difficulty = import_text(text)
        assert meta_dict["name"] == "kenken"
        assert meta_dict["constraints"]["has_box_regions"] is False
        recovered_cages = meta_dict["constraints"]["cages"]
        assert len(recovered_cages) == len(cages)
        for orig, rec in zip(cages, recovered_cages):
            assert rec["op"] == orig["op"]
            assert rec["target"] == orig["target"]
            assert len(rec["cells"]) == len(orig["cells"])
        assert seed == 5
        assert difficulty == "easy"

    def test_import_sets_region_layout(self) -> None:
        """Imported KenKen must have per-cell region layout (r*size+c)."""
        cages = self._full_cages_4x4()
        text = export_text(self._puzzle_none(), self._meta_dict(cages))
        _, meta_dict, _, _ = import_text(text)
        layout = meta_dict["region_layout"]
        expected = _kenken_layout(4)
        assert layout == expected

    def test_import_wrong_op_raises(self) -> None:
        cages = self._full_cages_4x4()
        text = export_text(self._puzzle_none(), self._meta_dict(cages))
        # Corrupt one cage line by replacing op with '^'
        lines = text.splitlines()
        for i, ln in enumerate(lines):
            if ln.startswith("cage:"):
                # Replace last part ':+:N' with ':^:N'
                lines[i] = ln.replace(":+:", ":^:", 1)
                break
        with pytest.raises(ValueError, match="op"):
            import_text("\n".join(lines))

    def test_import_missing_cage_lines_raises(self) -> None:
        """A kenken puzzle with no cage: lines must raise ValueError."""
        text = "variant: kenken\nsize: 4\nseed: 0\ndifficulty: easy\n"
        text += "0000\n0000\n0000\n0000\n"
        with pytest.raises(ValueError, match="cage"):
            import_text(text)

    def test_import_incomplete_coverage_raises(self) -> None:
        """KenKen import with cages covering < N² cells must raise."""
        # Only provide 7 cells out of 16
        partial_cages = self._full_cages_4x4()[:-1]  # drop last cage (2 cells)
        text = export_text(self._puzzle_none(), self._meta_dict(partial_cages))
        # Override the last two cage lines to remove them
        lines = [ln for ln in text.splitlines() if not ln.startswith("cage:")]
        cage_lines = [f"cage: {' '.join(str(r)+','+str(c) for r,c in cage['cells'])}:{cage['op']}:{cage['target']}"
                      for cage in partial_cages]
        combined = "\n".join(lines + cage_lines)
        with pytest.raises(ValueError, match="cover"):
            import_text(combined)

    def test_export_with_division_and_subtraction(self) -> None:
        """Export/import round-trip preserves - and / ops."""
        sol = self._SOL
        # Build cages using / and - where valid
        cages = []
        # (0,0) and (1,0): diff
        cages.append({"cells": [[0, 0], [1, 0]], "op": "-", "target": abs(sol[0][0] - sol[1][0])})
        # (0,1) and (1,1): div if valid, else +
        big, small = max(sol[0][1], sol[1][1]), min(sol[0][1], sol[1][1])
        if small != 0 and big % small == 0:
            cages.append({"cells": [[0, 1], [1, 1]], "op": "/", "target": big // small})
        else:
            cages.append({"cells": [[0, 1], [1, 1]], "op": "+", "target": sol[0][1] + sol[1][1]})
        # fill remainder with single-cell cages
        used = {(0, 0), (1, 0), (0, 1), (1, 1)}
        for r in range(4):
            for c in range(4):
                if (r, c) not in used:
                    cages.append({"cells": [[r, c]], "op": "+", "target": sol[r][c]})
        text = export_text(self._puzzle_none(), self._meta_dict(cages), seed=3, difficulty="hard")
        _, meta_dict, seed2, diff2 = import_text(text)
        assert meta_dict["name"] == "kenken"
        assert seed2 == 3
        assert diff2 == "hard"
        ops_exported = {c["op"] for c in cages}
        ops_imported = {c["op"] for c in meta_dict["constraints"]["cages"]}
        assert ops_exported == ops_imported
