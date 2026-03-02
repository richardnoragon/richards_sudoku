"""Core domain types for the richards_sudoku model layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Variant(str, Enum):
    """Supported puzzle variants."""

    STANDARD = "standard"
    JIGSAW = "jigsaw"
    STR8TS = "str8ts"
    EXTENDED = "extended"


@dataclass
class Cell:
    """A single cell on the Sudoku board."""

    value: int | None = None
    candidates: set[int] = field(default_factory=set)
    region_id: int = 0
    is_fixed: bool = False

    def copy(self) -> Cell:
        return Cell(
            value=self.value,
            candidates=set(self.candidates),
            region_id=self.region_id,
            is_fixed=self.is_fixed,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "candidates": sorted(self.candidates),
            "region_id": self.region_id,
            "is_fixed": self.is_fixed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Cell:
        return cls(
            value=data["value"],
            candidates=set(data["candidates"]),
            region_id=data["region_id"],
            is_fixed=data["is_fixed"],
        )


@dataclass(frozen=True)
class Move:
    """An undoable board action capturing before/after state of one cell.

    Covers both value edits and pencil-mark changes; what changed is
    implied by which fields differ.
    """

    row: int
    col: int
    old_value: int | None
    new_value: int | None
    old_candidates: frozenset[int]
    new_candidates: frozenset[int]


@dataclass
class VariantMetadata:
    """Rules and layout descriptor for a Sudoku variant."""

    name: Variant
    size: int
    symbols: list[int]  # valid fill values, e.g. list(range(1, 10))
    region_layout: list[list[int]]  # size×size grid mapping (row,col) -> region_id
    constraints: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.region_layout) != self.size or any(
            len(row) != self.size for row in self.region_layout
        ):
            raise ValueError(
                f"region_layout must be {self.size}×{self.size} "
                f"for variant '{self.name.value}'"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name.value,
            "size": self.size,
            "symbols": self.symbols,
            "region_layout": self.region_layout,
            "constraints": self.constraints,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VariantMetadata:
        return cls(
            name=Variant(data["name"]),
            size=data["size"],
            symbols=data["symbols"],
            region_layout=data["region_layout"],
            constraints=data.get("constraints", {}),
        )

    @classmethod
    def standard_9x9(cls) -> VariantMetadata:
        """Factory for the standard 9×9 Sudoku variant."""
        # region_id = (row // 3) * 3 + (col // 3) for the nine 3×3 boxes
        layout = [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]
        return cls(
            name=Variant.STANDARD,
            size=9,
            symbols=list(range(1, 10)),
            region_layout=layout,
        )


@dataclass
class Board:
    """The full Sudoku board state."""

    size: int
    variant: Variant
    cells: list[list[Cell]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.cells:
            self.cells = [
                [Cell() for _ in range(self.size)] for _ in range(self.size)
            ]
        if len(self.cells) != self.size or any(
            len(row) != self.size for row in self.cells
        ):
            raise ValueError(f"cells must be a {self.size}×{self.size} grid")

    def cell(self, row: int, col: int) -> Cell:
        return self.cells[row][col]

    def apply_move(self, move: Move) -> None:
        """Apply a Move to the board (do / redo)."""
        c = self.cells[move.row][move.col]
        if c.is_fixed:
            raise ValueError(
                f"Cannot modify fixed cell at ({move.row}, {move.col})"
            )
        c.value = move.new_value
        c.candidates = set(move.new_candidates)

    def reverse_move(self, move: Move) -> None:
        """Reverse a Move on the board (undo)."""
        c = self.cells[move.row][move.col]
        c.value = move.old_value
        c.candidates = set(move.old_candidates)

    def copy(self) -> Board:
        return Board(
            size=self.size,
            variant=self.variant,
            cells=[[c.copy() for c in row] for row in self.cells],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "size": self.size,
            "variant": self.variant.value,
            "cells": [[c.to_dict() for c in row] for row in self.cells],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Board:
        cells = [[Cell.from_dict(c) for c in row] for row in data["cells"]]
        return cls(
            size=data["size"],
            variant=Variant(data["variant"]),
            cells=cells,
        )
