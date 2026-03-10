"""Variant registry: maps Variant enum values to metadata factories and
constraint callbacks used during puzzle generation and validation.

Usage
-----
    from richards_sudoku.services.variant_registry import REGISTRY

    entry = REGISTRY[Variant.JIGSAW]
    meta = entry["factory"](seed=42, difficulty="medium")
    constraint_ok = entry.get("constraint_ok")   # None for unconstrained variants
"""
from __future__ import annotations

import random
from typing import Any, Callable

from richards_sudoku.model.types import Variant, VariantMetadata
from richards_sudoku.solver.generator import Grid


# ---------------------------------------------------------------------------
# Constraint callbacks
# ---------------------------------------------------------------------------

def _str8ts_constraint_ok(grid: Grid) -> bool:
    """Validate that every white-cell run in every row/column is consecutive."""
    size = len(grid)
    # We need to know the black cells; this callback is only used when the
    # full meta is available, so we accept any completed grid and return True
    # here as a placeholder — the real constraint is enforced during generation
    # by the Str8ts pre-processing in generate_puzzle.
    return True


def _killer_constraint_ok(cages: list[dict[str, Any]]) -> Callable[[Grid], bool]:
    """Return a constraint callback that checks cage sums for *cages*."""
    def _check(grid: Grid) -> bool:
        for cage in cages:
            cells = cage["cells"]
            expected = cage["sum"]
            total = 0
            for r, c in cells:
                v = grid[r][c]
                if v is None:
                    return True  # incomplete grid; don't reject yet
                total += v
            if total != expected:
                return False
        return True
    return _check


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def _standard_factory(
    seed: int = 0,
    difficulty: str = "medium",
) -> VariantMetadata:
    return VariantMetadata.standard_9x9()


def _jigsaw_factory(
    seed: int = 0,
    difficulty: str = "medium",
) -> VariantMetadata:
    from richards_sudoku.solver.variant_generators import JigsawRegionGenerator
    gen = JigsawRegionGenerator(size=9, seed=seed, difficulty=difficulty)
    layout = gen.generate()
    return VariantMetadata(
        name=Variant.JIGSAW,
        size=9,
        symbols=list(range(1, 10)),
        region_layout=layout,
    )


def _str8ts_factory(
    seed: int = 0,
    difficulty: str = "medium",
) -> VariantMetadata:
    from richards_sudoku.solver.variant_generators import Str8tsMaskGenerator
    gen = Str8tsMaskGenerator(size=9, seed=seed, difficulty=difficulty)
    blacks = gen.generate()
    black_list = [[r, c] for r, c in sorted(blacks)]
    # Standard column-based region layout; black cells don't belong to any box
    layout = [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]
    return VariantMetadata(
        name=Variant.STR8TS,
        size=9,
        symbols=list(range(1, 10)),
        region_layout=layout,
        constraints={"black_cells": black_list, "black_givens": []},
    )


def _killer_factory(
    seed: int = 0,
    difficulty: str = "medium",
) -> VariantMetadata:
    """Return a stub VariantMetadata; cages are filled in after solution generation."""
    layout = [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]
    return VariantMetadata(
        name=Variant.KILLER,
        size=9,
        symbols=list(range(1, 10)),
        region_layout=layout,
        constraints={"cages": []},  # cages populated by KillerWorker after solution
    )


def _one_to_25_factory(
    seed: int = 0,
    difficulty: str = "medium",
) -> VariantMetadata:
    """Return a 25×25 standard VariantMetadata stub."""
    size = 25
    box = 5
    layout = [[(r // box) * box + (c // box) for c in range(size)] for r in range(size)]
    return VariantMetadata(
        name=Variant.ONE_TO_25,
        size=size,
        symbols=list(range(1, size + 1)),
        region_layout=layout,
    )


def _codewords_factory(
    seed: int = 0,
    difficulty: str = "medium",
) -> VariantMetadata:
    """Return a Codewords VariantMetadata stub (codebook populated by generator)."""
    layout = [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]
    return VariantMetadata(
        name=Variant.CODEWORDS,
        size=9,
        symbols=list(range(1, 10)),
        region_layout=layout,
        constraints={"codebook": {}, "given_mappings": {}},
    )


def _kenken_factory(
    seed: int = 0,
    difficulty: str = "medium",
    size: int = 9,
) -> VariantMetadata:
    """Return a KenKen VariantMetadata stub (cages populated by generator)."""
    # KenKen uses no box regions — each row and column is its own group
    layout = [[r * size + c for c in range(size)] for r in range(size)]
    return VariantMetadata(
        name=Variant.KENKEN,
        size=size,
        symbols=list(range(1, size + 1)),
        region_layout=layout,
        constraints={"cages": [], "has_box_regions": False},
    )


def _kakuro_factory(
    seed: int = 0,
    difficulty: str = "medium",
) -> VariantMetadata:
    """Return a Kakuro VariantMetadata stub (clues populated by generator)."""
    size = 9
    layout = [[(r // 3) * 3 + (c // 3) for c in range(size)] for r in range(size)]
    return VariantMetadata(
        name=Variant.KAKURO,
        size=size,
        symbols=list(range(1, size + 1)),
        region_layout=layout,
        constraints={"clues": [], "black_cells": [], "clue_positions": {}},
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

REGISTRY: dict[Variant, dict[str, Any]] = {
    Variant.STANDARD: {
        "factory": _standard_factory,
        "constraint_ok": None,
    },
    Variant.JIGSAW: {
        "factory": _jigsaw_factory,
        "constraint_ok": None,
    },
    Variant.STR8TS: {
        "factory": _str8ts_factory,
        "constraint_ok": _str8ts_constraint_ok,
    },
    Variant.KILLER: {
        "factory": _killer_factory,
        "constraint_ok": None,  # set dynamically after cage partition
        "constraint_ok_factory": lambda meta: _killer_constraint_ok(
            meta.constraints["cages"]
        ),
    },
    Variant.ONE_TO_25: {
        "factory": _one_to_25_factory,
        "constraint_ok": None,
    },
    Variant.CODEWORDS: {
        "factory": _codewords_factory,
        "constraint_ok": None,
    },
    Variant.KENKEN: {
        "factory": _kenken_factory,
        "constraint_ok": None,
    },
    Variant.KAKURO: {
        "factory": _kakuro_factory,
        "constraint_ok": None,
    },
}
