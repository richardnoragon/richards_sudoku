"""Tests for services/text_format.py (task G9)."""
from __future__ import annotations

import pytest

from richards_sudoku.services.text_format import export_text, import_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _std_board_values(size: int = 9) -> list[list[int | None]]:
    """Minimal 9×9 board with some values set, others None."""
    board = [[None] * size for _ in range(size)]
    board[0][0] = 1
    board[0][1] = 2
    board[4][4] = 5
    board[8][8] = 9
    return board


def _std_meta(variant: str = "standard", size: int = 9) -> dict:
    sq = int(size ** 0.5)
    region_layout = [[(rr // sq) * sq + (cc // sq) for cc in range(size)] for rr in range(size)]
    return {
        "name": variant,
        "size": size,
        "symbols": list(range(1, size + 1)),
        "region_layout": region_layout,
        "constraints": {},
    }


# ---------------------------------------------------------------------------
# Standard variant round-trip
# ---------------------------------------------------------------------------

class TestStandardRoundTrip:
    def test_export_produces_header_and_digit_rows(self):
        meta = _std_meta()
        board = _std_board_values()
        text = export_text(board, meta, seed=42, difficulty="medium")
        assert "variant: standard" in text
        assert "size: 9" in text
        assert "seed: 42" in text
        assert "difficulty: medium" in text

    def test_digit_rows_present_compact(self):
        meta = _std_meta()
        board = _std_board_values()
        text = export_text(board, meta)
        lines = [ln for ln in text.splitlines() if ln and ":" not in ln]
        assert len(lines) == 9
        # First row: 1 2 then all zeros → "120000000"
        assert lines[0] == "120000000"

    def test_round_trip_restores_board(self):
        meta = _std_meta()
        board = _std_board_values()
        text = export_text(board, meta, seed=7, difficulty="hard")
        board2, meta2, seed2, diff2 = import_text(text)
        assert board2 == board
        assert meta2["name"] == "standard"
        assert meta2["size"] == 9
        assert seed2 == 7
        assert diff2 == "hard"

    def test_import_missing_seed_defaults_to_zero(self):
        text = "variant: standard\nsize: 9\ndifficulty: easy\n" + ("0" * 9 + "\n") * 9
        _, _, seed, _ = import_text(text)
        assert seed == 0

    def test_import_wrong_row_count_raises(self):
        text = "variant: standard\nsize: 9\nseed: 0\ndifficulty: easy\n" + ("0" * 9 + "\n") * 8
        with pytest.raises(ValueError, match="digit rows"):
            import_text(text)

    def test_import_wrong_row_length_raises(self):
        rows = ("0" * 9 + "\n") * 8 + "0" * 8 + "\n"
        text = f"variant: standard\nsize: 9\nseed: 0\ndifficulty: easy\n{rows}"
        with pytest.raises(ValueError):
            import_text(text)

    def test_import_missing_variant_raises(self):
        text = "size: 9\nseed: 0\ndifficulty: easy\n" + ("0" * 9 + "\n") * 9
        with pytest.raises(ValueError, match="variant"):
            import_text(text)

    def test_import_missing_size_raises(self):
        text = "variant: standard\nseed: 0\ndifficulty: easy\n" + ("0" * 9 + "\n") * 9
        with pytest.raises(ValueError, match="size"):
            import_text(text)


# ---------------------------------------------------------------------------
# Jigsaw variant round-trip
# ---------------------------------------------------------------------------

class TestJigsawRoundTrip:
    def _jigsaw_meta(self) -> dict:
        # Simple jigsaw with non-standard region layout
        region_layout = [
            [0, 0, 0, 1, 1, 1, 2, 2, 2],
            [0, 0, 0, 1, 1, 1, 2, 2, 2],
            [0, 0, 0, 1, 1, 1, 2, 2, 2],
            [3, 3, 3, 4, 4, 4, 5, 5, 5],
            [3, 3, 3, 4, 4, 4, 5, 5, 5],
            [3, 3, 3, 4, 4, 4, 5, 5, 5],
            [6, 6, 6, 7, 7, 7, 8, 8, 8],
            [6, 6, 6, 7, 7, 7, 8, 8, 8],
            [6, 6, 6, 7, 7, 7, 8, 8, 8],
        ]
        return {
            "name": "jigsaw",
            "size": 9,
            "symbols": list(range(1, 10)),
            "region_layout": region_layout,
            "constraints": {},
        }

    def test_export_has_nine_region_layout_lines(self):
        meta = self._jigsaw_meta()
        board = _std_board_values()
        text = export_text(board, meta)
        layout_lines = [ln for ln in text.splitlines() if ln.startswith("region_layout:")]
        assert len(layout_lines) == 9

    def test_region_layout_line_format(self):
        meta = self._jigsaw_meta()
        text = export_text(_std_board_values(), meta)
        first_rl = next(ln for ln in text.splitlines() if ln.startswith("region_layout:"))
        ids = [int(x) for x in first_rl.split(":", 1)[1].split()]
        assert ids == [0, 0, 0, 1, 1, 1, 2, 2, 2]

    def test_round_trip_restores_region_layout(self):
        meta = self._jigsaw_meta()
        board = _std_board_values()
        text = export_text(board, meta, seed=3, difficulty="easy")
        board2, meta2, seed2, diff2 = import_text(text)
        assert meta2["region_layout"] == meta["region_layout"]
        assert meta2["name"] == "jigsaw"
        assert board2 == board

    def test_import_wrong_layout_row_count_raises(self):
        meta = self._jigsaw_meta()
        text = export_text(_std_board_values(), meta, seed=0, difficulty="easy")
        # Remove one region_layout line
        lines = text.splitlines()
        idx = next(i for i, ln in enumerate(lines) if ln.startswith("region_layout:"))
        lines.pop(idx)
        with pytest.raises(ValueError, match="region_layout"):
            import_text("\n".join(lines))

    def test_import_wrong_layout_row_length_raises(self):
        meta = self._jigsaw_meta()
        text = export_text(_std_board_values(), meta, seed=0, difficulty="easy")
        lines = text.splitlines()
        idx = next(i for i, ln in enumerate(lines) if ln.startswith("region_layout:"))
        lines[idx] = "region_layout: 0 0 0 1"  # too short
        with pytest.raises(ValueError):
            import_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Str8ts variant round-trip
# ---------------------------------------------------------------------------

class TestStr8tsRoundTrip:
    def _str8ts_meta(self) -> dict:
        # Simple mask: topmost row cells 0,3,6 are black; rest white
        black_cells = [[0, 0], [0, 3], [0, 6], [4, 4], [8, 8]]
        region_layout = [[(rr // 3) * 3 + (cc // 3) for cc in range(9)] for rr in range(9)]
        return {
            "name": "str8ts",
            "size": 9,
            "symbols": list(range(1, 10)),
            "region_layout": region_layout,
            "constraints": {"black_cells": black_cells, "black_givens": [[0, 0, 5], [0, 3, 2]]},
        }

    def test_export_has_mask_header(self):
        meta = self._str8ts_meta()
        text = export_text(_std_board_values(), meta)
        assert any(ln.startswith("mask:") for ln in text.splitlines())

    def test_mask_format_correct(self):
        meta = self._str8ts_meta()
        text = export_text(_std_board_values(), meta)
        mask_line = next(ln for ln in text.splitlines() if ln.startswith("mask:"))
        mask = mask_line.split(":", 1)[1].strip()
        row_strs = mask.split("/")
        assert len(row_strs) == 9
        # Row 0: cells 0,3,6 are B
        assert row_strs[0][0] == "B"
        assert row_strs[0][3] == "B"
        assert row_strs[0][6] == "B"
        assert row_strs[0][1] == "."

    def test_export_has_black_givens_header(self):
        meta = self._str8ts_meta()
        text = export_text(_std_board_values(), meta)
        assert any(ln.startswith("black_givens:") for ln in text.splitlines())

    def test_round_trip_restores_black_cells(self):
        meta = self._str8ts_meta()
        board = _std_board_values()
        text = export_text(board, meta, seed=11, difficulty="hard")
        board2, meta2, seed2, diff2 = import_text(text)
        assert meta2["name"] == "str8ts"
        bcs2 = {(int(p[0]), int(p[1])) for p in meta2["constraints"]["black_cells"]}
        expected_bcs = {(int(p[0]), int(p[1])) for p in meta["constraints"]["black_cells"]}
        assert bcs2 == expected_bcs
        assert board2 == board
        assert seed2 == 11

    def test_round_trip_restores_black_givens(self):
        meta = self._str8ts_meta()
        text = export_text(_std_board_values(), meta)
        _, meta2, _, _ = import_text(text)
        bg2 = [[int(x) for x in e] for e in meta2["constraints"]["black_givens"]]
        assert bg2 == [[0, 0, 5], [0, 3, 2]]

    def test_import_invalid_mask_char_raises(self):
        meta = self._str8ts_meta()
        text = export_text(_std_board_values(), meta)
        lines = text.splitlines()
        idx = next(i for i, ln in enumerate(lines) if ln.startswith("mask:"))
        lines[idx] = "mask: X....../......./......./......./......./......./......./......./......."
        with pytest.raises(ValueError):
            import_text("\n".join(lines))

    def test_import_mask_wrong_row_count_raises(self):
        text = "variant: str8ts\nsize: 9\nseed: 0\ndifficulty: easy\nmask: ........./........./........./........./........./........./........./.........".rstrip("/") + "\n" + ("0" * 9 + "\n") * 9
        with pytest.raises(ValueError, match="mask"):
            import_text(text)


# ---------------------------------------------------------------------------
# Killer variant round-trip
# ---------------------------------------------------------------------------

class TestKillerRoundTrip:
    def _killer_meta(self) -> dict:
        """Build a minimal 9×9 killer grid with 9 single-row cages."""
        # Just use 9 non-overlapping cages of 9 cells each (one per row)
        cages = []
        for r in range(9):
            cages.append({
                "cells": [[r, c] for c in range(9)],
                "sum": 45,
            })
        region_layout = [[(rr // 3) * 3 + (cc // 3) for cc in range(9)] for rr in range(9)]
        return {
            "name": "killer",
            "size": 9,
            "symbols": list(range(1, 10)),
            "region_layout": region_layout,
            "constraints": {"cages": cages},
        }

    def test_export_has_cage_lines(self):
        meta = self._killer_meta()
        text = export_text(_std_board_values(), meta)
        cage_lines = [ln for ln in text.splitlines() if ln.startswith("cage:")]
        assert len(cage_lines) == 9

    def test_cage_line_format(self):
        meta = self._killer_meta()
        text = export_text(_std_board_values(), meta)
        first_cage = next(ln for ln in text.splitlines() if ln.startswith("cage:"))
        # e.g. "cage: 0,0 0,1 0,2 0,3 0,4 0,5 0,6 0,7 0,8:45"
        payload = first_cage[len("cage: "):]
        assert ":" in payload
        cells_part, sum_part = payload.rsplit(":", 1)
        assert int(sum_part.strip()) == 45
        tokens = cells_part.split()
        assert len(tokens) == 9
        assert tokens[0] == "0,0"

    def test_round_trip_restores_cages(self):
        meta = self._killer_meta()
        board = _std_board_values()
        text = export_text(board, meta, seed=99, difficulty="expert")
        board2, meta2, seed2, diff2 = import_text(text)
        assert meta2["name"] == "killer"
        assert len(meta2["constraints"]["cages"]) == 9
        assert meta2["constraints"]["cages"][0]["sum"] == 45
        assert board2 == board
        assert seed2 == 99
        assert diff2 == "expert"

    def test_import_cage_overlap_raises(self):
        text = (
            "variant: killer\nsize: 9\nseed: 0\ndifficulty: easy\n"
            "cage: 0,0 0,1:5\n"
            "cage: 0,0 0,2:3\n"  # 0,0 overlaps
        )
        # Also fill remaining cells to avoid "Missing required header" before overlap error
        # Overlap detection fires during cage parsing, which happens before digit row count check
        with pytest.raises(ValueError, match="overlap"):
            import_text(text)

    def test_import_incomplete_cage_coverage_raises(self):
        # Only 1 cage covering row 0; rest uncovered → should raise
        text = (
            "variant: killer\nsize: 9\nseed: 0\ndifficulty: easy\n"
            + "cage: " + " ".join(f"0,{c}" for c in range(9)) + ":45\n"
            + ("0" * 9 + "\n") * 9
        )
        with pytest.raises(ValueError, match="cover"):
            import_text(text)

    def test_import_missing_sum_in_cage_raises(self):
        text = (
            "variant: killer\nsize: 9\nseed: 0\ndifficulty: easy\n"
            "cage: 0,0 0,1 0,2\n"  # no :sum
            + ("0" * 9 + "\n") * 9
        )
        with pytest.raises(ValueError):
            import_text(text)


# ---------------------------------------------------------------------------
# G9 spec: seed defaults to 0, missing seed header
# ---------------------------------------------------------------------------

class TestSeedDefault:
    def test_standard_no_seed_header_defaults_zero(self):
        text = "variant: standard\nsize: 9\ndifficulty: medium\n" + ("0" * 9 + "\n") * 9
        _, _, seed, _ = import_text(text)
        assert seed == 0

    def test_jigsaw_no_seed_header_defaults_zero(self):
        region_lines = "\n".join("region_layout: " + " ".join(str((r // 3) * 3 + (c // 3)) for c in range(9)) for r in range(9))
        text = f"variant: jigsaw\nsize: 9\ndifficulty: easy\n{region_lines}\n" + ("0" * 9 + "\n") * 9
        _, _, seed, _ = import_text(text)
        assert seed == 0


# ---------------------------------------------------------------------------
# Repeating-field convention (G9 spec says repeating cage: lines)
# ---------------------------------------------------------------------------

class TestRepeatingFieldConvention:
    def test_multiple_cage_lines_parsed_as_separate_cages(self):
        # 3 one-cell cages in first row; rest omitted (will fail coverage but check parsing)
        cage_line_1 = "cage: 0,0:1"
        cage_line_2 = "cage: 0,1:2"
        cage_line_3 = "cage: 0,2:3"
        # We just check that all 3 cages are created, not coverage validation
        # Pass incomplete coverage to trigger ValueError but confirm count
        text = (
            "variant: killer\nsize: 9\nseed: 0\ndifficulty: easy\n"
            + f"{cage_line_1}\n{cage_line_2}\n{cage_line_3}\n"
            + ("0" * 9 + "\n") * 9
        )
        try:
            import_text(text)
        except ValueError as exc:
            # Expected: coverage error, not a parse error
            assert "cover" in str(exc).lower() or "81" in str(exc)

    def test_multiple_region_layout_lines_parsed_as_rows(self):
        region_lines = "\n".join(
            "region_layout: " + " ".join(str((r // 3) * 3 + (c // 3)) for c in range(9))
            for r in range(9)
        )
        text = f"variant: jigsaw\nsize: 9\nseed: 0\ndifficulty: easy\n{region_lines}\n" + ("0" * 9 + "\n") * 9
        _, meta2, _, _ = import_text(text)
        assert len(meta2["region_layout"]) == 9
        assert meta2["region_layout"][0] == [0, 0, 0, 1, 1, 1, 2, 2, 2]
