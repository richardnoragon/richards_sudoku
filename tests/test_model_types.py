"""Unit tests for core domain types and schema helpers."""
from __future__ import annotations

import pytest

from richards_sudoku.model.schema import (
    CURRENT_SCHEMA_VERSION,
    add_version,
    check_version,
)
from richards_sudoku.model.types import Board, Cell, Move, Variant, VariantMetadata


class TestCell:
    def test_default_is_empty(self) -> None:
        c = Cell()
        assert c.value is None
        assert c.candidates == set()
        assert c.region_id == 0
        assert c.is_fixed is False

    def test_copy_is_independent(self) -> None:
        c = Cell(value=5, candidates={1, 2}, region_id=3, is_fixed=True)
        c2 = c.copy()
        c2.candidates.add(9)
        assert 9 not in c.candidates

    def test_copy_preserves_all_fields(self) -> None:
        c = Cell(value=5, candidates={1, 2}, region_id=3, is_fixed=True)
        c2 = c.copy()
        assert c2.value == 5
        assert c2.region_id == 3
        assert c2.is_fixed is True

    def test_round_trip_dict(self) -> None:
        c = Cell(value=7, candidates={3, 5}, region_id=2, is_fixed=True)
        assert Cell.from_dict(c.to_dict()) == c

    def test_round_trip_empty_candidates(self) -> None:
        c = Cell()
        assert Cell.from_dict(c.to_dict()) == c


class TestMove:
    def test_is_frozen(self) -> None:
        m = Move(
            row=0, col=0,
            old_value=None, new_value=5,
            old_candidates=frozenset({1, 2}), new_candidates=frozenset(),
        )
        with pytest.raises((AttributeError, TypeError)):
            m.row = 1  # type: ignore[misc]

    def test_fields_accessible(self) -> None:
        m = Move(
            row=3, col=4,
            old_value=2, new_value=7,
            old_candidates=frozenset({1}), new_candidates=frozenset({3}),
        )
        assert m.row == 3
        assert m.col == 4
        assert m.old_value == 2
        assert m.new_value == 7
        assert m.old_candidates == frozenset({1})
        assert m.new_candidates == frozenset({3})


class TestVariantMetadata:
    def test_standard_9x9_size_and_symbols(self) -> None:
        meta = VariantMetadata.standard_9x9()
        assert meta.size == 9
        assert meta.symbols == list(range(1, 10))
        assert meta.name == Variant.STANDARD

    def test_standard_9x9_top_left_box_is_region_0(self) -> None:
        meta = VariantMetadata.standard_9x9()
        assert all(meta.region_layout[r][c] == 0 for r in range(3) for c in range(3))

    def test_standard_9x9_bottom_right_box_is_region_8(self) -> None:
        meta = VariantMetadata.standard_9x9()
        assert all(meta.region_layout[r][c] == 8 for r in range(6, 9) for c in range(6, 9))

    def test_standard_9x9_has_nine_distinct_regions(self) -> None:
        meta = VariantMetadata.standard_9x9()
        flat = {meta.region_layout[r][c] for r in range(9) for c in range(9)}
        assert flat == set(range(9))

    def test_invalid_layout_raises(self) -> None:
        with pytest.raises(ValueError):
            VariantMetadata(
                name=Variant.STANDARD,
                size=9,
                symbols=list(range(1, 10)),
                region_layout=[[0] * 8] * 9,  # wrong column count
            )

    def test_round_trip_dict(self) -> None:
        meta = VariantMetadata.standard_9x9()
        assert VariantMetadata.from_dict(meta.to_dict()) == meta


class TestBoard:
    def test_default_board_all_empty(self) -> None:
        b = Board(size=9, variant=Variant.STANDARD)
        assert all(b.cell(r, c).value is None for r in range(9) for c in range(9))

    def test_invalid_cell_grid_raises(self) -> None:
        with pytest.raises(ValueError):
            Board(size=9, variant=Variant.STANDARD, cells=[[Cell()] * 8] * 9)

    def test_copy_is_independent(self) -> None:
        b = Board(size=9, variant=Variant.STANDARD)
        b.cell(0, 0).value = 5
        b2 = b.copy()
        b2.cell(0, 0).value = 9
        assert b.cell(0, 0).value == 5

    def test_apply_move_sets_value_and_candidates(self) -> None:
        b = Board(size=9, variant=Variant.STANDARD)
        b.cell(0, 0).candidates = {1, 2}
        move = Move(
            row=0, col=0,
            old_value=None, new_value=7,
            old_candidates=frozenset({1, 2}), new_candidates=frozenset(),
        )
        b.apply_move(move)
        assert b.cell(0, 0).value == 7
        assert b.cell(0, 0).candidates == set()

    def test_reverse_move_restores_state(self) -> None:
        b = Board(size=9, variant=Variant.STANDARD)
        move = Move(
            row=0, col=0,
            old_value=None, new_value=7,
            old_candidates=frozenset({1, 2}), new_candidates=frozenset(),
        )
        b.apply_move(move)
        b.reverse_move(move)
        assert b.cell(0, 0).value is None
        assert b.cell(0, 0).candidates == {1, 2}

    def test_apply_move_to_fixed_cell_raises(self) -> None:
        b = Board(size=9, variant=Variant.STANDARD)
        b.cell(0, 0).is_fixed = True
        move = Move(
            row=0, col=0,
            old_value=None, new_value=3,
            old_candidates=frozenset(), new_candidates=frozenset(),
        )
        with pytest.raises(ValueError):
            b.apply_move(move)

    def test_round_trip_dict(self) -> None:
        b = Board(size=9, variant=Variant.STANDARD)
        b.cell(4, 4).value = 5
        b.cell(4, 4).is_fixed = True
        b2 = Board.from_dict(b.to_dict())
        assert b2.cell(4, 4).value == 5
        assert b2.cell(4, 4).is_fixed is True

    def test_round_trip_preserves_candidates(self) -> None:
        b = Board(size=9, variant=Variant.STANDARD)
        b.cell(1, 1).candidates = {3, 7}
        b2 = Board.from_dict(b.to_dict())
        assert b2.cell(1, 1).candidates == {3, 7}


class TestSchema:
    def test_add_version_injects_current(self) -> None:
        d = add_version({"foo": "bar"})
        assert d["version"] == CURRENT_SCHEMA_VERSION
        assert d["foo"] == "bar"

    def test_check_version_valid(self) -> None:
        assert check_version({"version": CURRENT_SCHEMA_VERSION}) == CURRENT_SCHEMA_VERSION

    def test_check_version_missing_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing"):
            check_version({})

    def test_check_version_future_raises(self) -> None:
        with pytest.raises(ValueError, match="newer"):
            check_version({"version": CURRENT_SCHEMA_VERSION + 1})

    def test_check_version_zero_raises(self) -> None:
        with pytest.raises(ValueError):
            check_version({"version": 0})

    def test_check_version_non_int_raises(self) -> None:
        with pytest.raises(ValueError):
            check_version({"version": "1"})

    def test_add_then_check_is_identity(self) -> None:
        original = {"puzzle": "data"}
        versioned = add_version(original)
        assert check_version(versioned) == CURRENT_SCHEMA_VERSION
