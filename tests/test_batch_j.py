"""EV-T1 — Batch J tests.

Covers:
- New Variant enum values (CODEWORDS, KENKEN, KAKURO) round-trip in JSON
- REGISTRY entries exist for all 7 variants
- NewGameDialog enables/disables correct variant options
"""
from __future__ import annotations

import json

import pytest

from richards_sudoku.model.types import Variant, VariantMetadata
from richards_sudoku.services.variant_registry import REGISTRY


# ---------------------------------------------------------------------------
# J1 — Variant enum round-trip in JSON
# ---------------------------------------------------------------------------

class TestBatchJEnumRoundTrip:
    @pytest.mark.parametrize("variant", [
        Variant.CODEWORDS,
        Variant.KENKEN,
        Variant.KAKURO,
        Variant.ONE_TO_25,
    ])
    def test_variant_value_is_string(self, variant: Variant) -> None:
        assert isinstance(variant.value, str)

    @pytest.mark.parametrize("variant", [
        Variant.CODEWORDS,
        Variant.KENKEN,
        Variant.KAKURO,
        Variant.ONE_TO_25,
    ])
    def test_variant_json_round_trip(self, variant: Variant) -> None:
        serialized = json.dumps({"variant": variant.value})
        data = json.loads(serialized)
        recovered = Variant(data["variant"])
        assert recovered == variant

    def test_all_expected_variants_present(self) -> None:
        expected = {
            Variant.STANDARD, Variant.JIGSAW, Variant.STR8TS, Variant.KILLER,
            Variant.ONE_TO_25, Variant.CODEWORDS, Variant.KENKEN, Variant.KAKURO,
        }
        actual = set(Variant)
        assert expected.issubset(actual)


# ---------------------------------------------------------------------------
# J2 — REGISTRY entries exist for all 7 variants
# ---------------------------------------------------------------------------

class TestBatchJRegistry:
    @pytest.mark.parametrize("variant", list(Variant))
    def test_registry_has_entry(self, variant: Variant) -> None:
        assert variant in REGISTRY, f"REGISTRY missing entry for {variant!r}"

    @pytest.mark.parametrize("variant", list(Variant))
    def test_registry_entry_has_factory(self, variant: Variant) -> None:
        entry = REGISTRY[variant]
        assert "factory" in entry
        assert callable(entry["factory"])

    def test_one_to_25_factory_produces_25x25_meta(self) -> None:
        meta = REGISTRY[Variant.ONE_TO_25]["factory"](seed=0)
        assert meta.size == 25
        assert meta.name == Variant.ONE_TO_25
        assert meta.symbols == list(range(1, 26))

    def test_kenken_factory_has_no_box_regions(self) -> None:
        meta = REGISTRY[Variant.KENKEN]["factory"](seed=0)
        assert meta.constraints.get("has_box_regions") is False

    def test_killer_has_constraint_ok_factory(self) -> None:
        entry = REGISTRY[Variant.KILLER]
        assert "constraint_ok_factory" in entry
        assert callable(entry["constraint_ok_factory"])

    def test_codewords_factory_has_codebook_constraint(self) -> None:
        meta = REGISTRY[Variant.CODEWORDS]["factory"](seed=0)
        assert "codebook" in meta.constraints

    def test_kakuro_factory_has_clues_constraint(self) -> None:
        meta = REGISTRY[Variant.KAKURO]["factory"](seed=0)
        assert "clues" in meta.constraints


# ---------------------------------------------------------------------------
# J3 — NewGameDialog correct enable/disable state
# ---------------------------------------------------------------------------

@pytest.mark.qt
class TestBatchJDialog:
    def test_dialog_has_all_variants(self, qtbot) -> None:
        from PyQt6.QtWidgets import QApplication
        from richards_sudoku.ui.new_game_dialog import NewGameDialog

        dlg = NewGameDialog(initial_seed=42)
        qtbot.addWidget(dlg)

        labels = [label for label, *_ in NewGameDialog._VARIANTS]
        assert "Standard" in labels
        assert "Jigsaw" in labels
        assert "Str8ts" in labels
        assert "Killer" in labels
        assert "1 to 25" in labels
        assert "Codewords" in labels
        assert "KenKen" in labels
        assert "Kakuro" in labels

    def test_one_to_25_is_enabled(self, qtbot) -> None:
        from richards_sudoku.ui.new_game_dialog import NewGameDialog

        dlg = NewGameDialog(initial_seed=1)
        qtbot.addWidget(dlg)

        # Find the "1 to 25" item index
        idx = next(
            i for i, (label, *_) in enumerate(NewGameDialog._VARIANTS)
            if label == "1 to 25"
        )
        model = dlg._variant_combo.model()
        item = model.item(idx)
        assert item.isEnabled(), "The '1 to 25' variant combo item should be enabled"

    @pytest.mark.qt
    def test_kenken_is_enabled(self, qtbot) -> None:
        from richards_sudoku.ui.new_game_dialog import NewGameDialog

        dlg = NewGameDialog(initial_seed=6)
        qtbot.addWidget(dlg)

        idx = next(
            i for i, (lbl, *_) in enumerate(NewGameDialog._VARIANTS)
            if lbl == "KenKen"
        )
        model = dlg._variant_combo.model()
        item = model.item(idx)
        assert item.isEnabled(), "KenKen variant combo item should be enabled"

    @pytest.mark.qt
    def test_codewords_is_enabled(self, qtbot) -> None:
        from richards_sudoku.ui.new_game_dialog import NewGameDialog

        dlg = NewGameDialog(initial_seed=5)
        qtbot.addWidget(dlg)

        idx = next(
            i for i, (lbl, *_) in enumerate(NewGameDialog._VARIANTS)
            if lbl == "Codewords"
        )
        model = dlg._variant_combo.model()
        item = model.item(idx)
        assert item.isEnabled(), "Codewords variant combo item should be enabled"

    def test_size_combo_shows_25x25_for_one_to_25(self, qtbot) -> None:
        from richards_sudoku.ui.new_game_dialog import NewGameDialog

        dlg = NewGameDialog(initial_seed=3)
        qtbot.addWidget(dlg)

        idx = next(
            i for i, (label, *_) in enumerate(NewGameDialog._VARIANTS)
            if label == "1 to 25"
        )
        dlg._variant_combo.setCurrentIndex(idx)
        assert dlg._size_combo.currentText() == "25×25"

    def test_size_combo_shows_9x9_for_standard(self, qtbot) -> None:
        from richards_sudoku.ui.new_game_dialog import NewGameDialog

        dlg = NewGameDialog(initial_seed=4)
        qtbot.addWidget(dlg)

        idx = next(
            i for i, (label, *_) in enumerate(NewGameDialog._VARIANTS)
            if label == "Standard"
        )
        dlg._variant_combo.setCurrentIndex(idx)
        assert dlg._size_combo.currentText() == "9×9"
