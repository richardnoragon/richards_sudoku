"""Text-format import and export for Richards Sudoku.

Format specification (G9)
--------------------------
Each puzzle file has a header block followed by digit rows.

Common headers (all variants):
    variant: <name>
    size: <N>
    seed: <int>          (optional; defaults to 0 on import)
    difficulty: <label>

Variant-specific headers:
  Jigsaw:
    region_layout: r0c0 r0c1 ... r0cN    (one line per board row, 0-indexed region IDs)

  Str8ts:
    mask: <row0>/<row1>/.../<rowN-1>     (each row: N chars — '.' white, 'B' black)
    black_givens: r,c,v ...              (space-separated triples; omitted if empty)

  Killer:
    cage: r0,c0 r1,c1 ...:sum           (one line per cage)

  Codewords:
    codebook: A=1,B=2,...,I=9           (required; bijective mapping of letters A-I to digits 1-9)
    given_mappings: A=1,C=3,...         (optional; pre-revealed letter-to-digit assignments)

  One-to-25 (1to25):
    (no extra headers; digit rows are space-separated)

Digit rows (one per board row):
  Standard/Jigsaw/Str8ts/Killer:  compact 9 chars, '0' = empty
  Codewords:  compact 9 chars, letter (A-I) for filled cells, '0' = empty
  ONE_TO_25 (25-wide):  space-separated integers, '0' = empty
"""
from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_text(
    board_values: list[list[int | None]],
    meta_dict: dict[str, Any],
    seed: int = 0,
    difficulty: str = "medium",
) -> str:
    """Serialise a puzzle to text format.

    Parameters
    ----------
    board_values:
        size×size grid of int|None (None = empty cell).
    meta_dict:
        The ``VariantMetadata.to_dict()`` snapshot.
    seed:
        RNG seed used to generate the puzzle.
    difficulty:
        Difficulty label string.

    Returns
    -------
    str
        Multi-line text representation.
    """
    variant = meta_dict["name"]
    size = meta_dict["size"]
    constraints: dict[str, Any] = meta_dict.get("constraints", {}) or {}

    lines: list[str] = []

    # --- common headers ---
    lines.append(f"variant: {variant}")
    lines.append(f"size: {size}")
    lines.append(f"seed: {seed}")
    lines.append(f"difficulty: {difficulty}")

    # --- variant-specific headers ---
    if variant == "jigsaw":
        region_layout: list[list[int]] = meta_dict["region_layout"]
        for row in region_layout:
            lines.append("region_layout: " + " ".join(str(rid) for rid in row))

    elif variant == "str8ts":
        black_cells: list = constraints.get("black_cells", []) or []
        black_set = {(int(p[0]), int(p[1])) for p in black_cells}
        rows = []
        for r in range(size):
            rows.append("".join("B" if (r, c) in black_set else "." for c in range(size)))
        lines.append("mask: " + "/".join(rows))
        black_givens: list = constraints.get("black_givens", []) or []
        if black_givens:
            triples = " ".join(f"{int(e[0])},{int(e[1])},{int(e[2])}" for e in black_givens)
            lines.append(f"black_givens: {triples}")

    elif variant == "killer":
        for cage in (constraints.get("cages") or []):
            cells_part = " ".join(f"{int(p[0])},{int(p[1])}" for p in cage["cells"])
            lines.append(f"cage: {cells_part}:{cage['sum']}")

    elif variant == "kenken":
        for cage in (constraints.get("cages") or []):
            cells_part = " ".join(f"{int(p[0])},{int(p[1])}" for p in cage["cells"])
            lines.append(f"cage: {cells_part}:{cage['op']}:{cage['target']}")

    elif variant == "kakuro":
        # Mask header: B for black cell, . for white cell
        black_cells_ex: list = constraints.get("black_cells", []) or []
        black_set_ex = {(int(p[0]), int(p[1])) for p in black_cells_ex}
        mask_rows = [
            "".join("B" if (r, c) in black_set_ex else "." for c in range(size))
            for r in range(size)
        ]
        lines.append("mask: " + "/".join(mask_rows))
        # Clue lines: r,c r,c ...:sum:dir
        for run in (constraints.get("clues") or []):
            cells_part = " ".join(f"{int(p[0])},{int(p[1])}" for p in run["cells"])
            lines.append(f"clue: {cells_part}:{run['sum']}:{run['dir']}")

    elif variant == "codewords":
        codebook: dict[str, int] = constraints.get("codebook", {})
        if codebook:
            lines.append("codebook: " + ",".join(f"{l}={d}" for l, d in sorted(codebook.items())))
        given_mappings: dict[str, int] = constraints.get("given_mappings", {})
        if given_mappings:
            lines.append("given_mappings: " + ",".join(f"{l}={d}" for l, d in sorted(given_mappings.items())))

    elif variant == "1to25":
        pass  # no extra headers; digit rows are space-separated

    # --- digit rows ---
    inv_codebook: dict[int, str] = {}
    if variant == "codewords":
        cb = constraints.get("codebook", {})
        inv_codebook = {v: k for k, v in cb.items()}

    for r in range(size):
        row_vals = board_values[r]
        if variant == "1to25":
            lines.append(" ".join(str(v) if v is not None else "0" for v in row_vals))
        elif variant == "codewords":
            chars = []
            for v in row_vals:
                if v is None:
                    chars.append("0")
                else:
                    chars.append(inv_codebook.get(v, str(v)))
            lines.append("".join(chars))
        elif variant == "kakuro":
            # Black cells → '_', empty white → '0', filled white → digit
            black_set_dr = {(int(p[0]), int(p[1])) for p in (constraints.get("black_cells") or [])}
            chars_k = []
            for c_idx, v in enumerate(row_vals):
                if (r, c_idx) in black_set_dr:
                    chars_k.append("_")
                elif v is None:
                    chars_k.append("0")
                else:
                    chars_k.append(str(v))
            lines.append("".join(chars_k))
        else:
            lines.append("".join(str(v) if v is not None else "0" for v in row_vals))

    return "\n".join(lines) + "\n"


def import_text(text: str) -> tuple[list[list[int | None]], dict[str, Any], int, str]:
    """Parse a text-format puzzle.

    Returns
    -------
    (board_values, meta_dict, seed, difficulty)
        board_values : size×size list of int|None
        meta_dict    : dict suitable for ``VariantMetadata.from_dict``
        seed         : int
        difficulty   : str
    """
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]

    headers: dict[str, list[str]] = {}
    remaining: list[str] = []
    repeating_keys = {"region_layout", "cage", "clue"}

    for line in lines:
        m = re.match(r"^(\w+(?:_\w+)*):\s*(.*)", line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            if key in repeating_keys:
                headers.setdefault(key, []).append(val)
            else:
                headers[key] = [val]
        else:
            remaining.append(line)

    def _req(key: str) -> str:
        if key not in headers:
            raise ValueError(f"Missing required header '{key}:'.")
        return headers[key][0]

    variant = _req("variant")
    size = int(_req("size"))
    seed = int(headers["seed"][0]) if "seed" in headers else 0
    difficulty = headers["difficulty"][0] if "difficulty" in headers else "medium"

    constraints: dict[str, Any] = {}
    region_layout: list[list[int]] = []

    if variant == "jigsaw":
        rows_raw = headers.get("region_layout", [])
        if len(rows_raw) != size:
            raise ValueError(
                f"Jigsaw requires {size} 'region_layout:' lines; got {len(rows_raw)}."
            )
        for raw in rows_raw:
            ids = [int(x) for x in raw.split()]
            if len(ids) != size:
                raise ValueError(
                    f"Jigsaw region_layout row has {len(ids)} values; expected {size}."
                )
            region_layout.append(ids)

    elif variant == "str8ts":
        mask_raw = _req("mask")
        row_strs = mask_raw.split("/")
        if len(row_strs) != size:
            raise ValueError(f"Str8ts mask has {len(row_strs)} rows; expected {size}.")
        black_cells = []
        for r, rs in enumerate(row_strs):
            if len(rs) != size:
                raise ValueError(f"Str8ts mask row {r} has length {len(rs)}; expected {size}.")
            for c, ch in enumerate(rs):
                if ch == "B":
                    black_cells.append([r, c])
                elif ch != ".":
                    raise ValueError(f"Unexpected mask character '{ch}' at row {r} col {c}.")
        constraints["black_cells"] = black_cells
        # Standard 9×9 box layout for Str8ts
        region_layout = [[(rr // 3) * 3 + (cc // 3) for cc in range(size)] for rr in range(size)]
        black_givens_raw = headers.get("black_givens", [])
        if black_givens_raw:
            bg_triples = []
            for triple_str in " ".join(black_givens_raw).split():
                parts = triple_str.split(",")
                if len(parts) != 3:
                    raise ValueError(f"black_givens entry '{triple_str}' is not 'r,c,v'.")
                bg_triples.append([int(p) for p in parts])
            constraints["black_givens"] = bg_triples

    elif variant == "killer":
        cage_lines = headers.get("cage", [])
        if not cage_lines:
            raise ValueError("Killer puzzle requires at least one 'cage:' line.")
        cages = []
        covered: set[tuple[int, int]] = set()
        for i, raw in enumerate(cage_lines):
            if ":" not in raw:
                raise ValueError(f"Cage line {i} missing ':sum' at end: '{raw}'.")
            cells_part, sum_part = raw.rsplit(":", 1)
            cage_sum = int(sum_part.strip())
            cells = []
            for token in cells_part.split():
                rc = token.split(",")
                if len(rc) != 2:
                    raise ValueError(f"Cage {i} cell token '{token}' is not 'r,c'.")
                r, c = int(rc[0]), int(rc[1])
                key = (r, c)
                if key in covered:
                    raise ValueError(f"Killer cage overlap: cell {list(key)} in multiple cages.")
                covered.add(key)
                cells.append([r, c])
            cages.append({"cells": cells, "sum": cage_sum})
        if len(covered) != size * size:
            raise ValueError(
                f"Killer cages cover {len(covered)} cells; expected {size * size}."
            )
        constraints["cages"] = cages
        region_layout = [[(rr // 3) * 3 + (cc // 3) for cc in range(size)] for rr in range(size)]

    elif variant == "kenken":
        cage_lines = headers.get("cage", [])
        if not cage_lines:
            raise ValueError("KenKen puzzle requires at least one 'cage:' line.")
        valid_ops = {"+", "-", "*", "/"}
        kk_cages = []
        kk_covered: set[tuple[int, int]] = set()
        for i, raw in enumerate(cage_lines):
            parts = raw.rsplit(":", 2)
            if len(parts) != 3:
                raise ValueError(
                    f"KenKen cage line {i} must be 'r,c ...:op:target'; got '{raw}'."
                )
            cells_part, op, target_str = parts
            op = op.strip()
            if op not in valid_ops:
                raise ValueError(
                    f"KenKen cage {i} op {op!r} is not one of {sorted(valid_ops)!r}."
                )
            target = int(target_str.strip())
            cells = []
            for token in cells_part.split():
                rc = token.split(",")
                if len(rc) != 2:
                    raise ValueError(f"KenKen cage {i} cell token '{token}' is not 'r,c'.")
                r, c = int(rc[0]), int(rc[1])
                key = (r, c)
                if key in kk_covered:
                    raise ValueError(
                        f"KenKen cage overlap: cell {list(key)} in multiple cages."
                    )
                kk_covered.add(key)
                cells.append([r, c])
            kk_cages.append({"cells": cells, "op": op, "target": target})
        if len(kk_covered) != size * size:
            raise ValueError(
                f"KenKen cages cover {len(kk_covered)} cells; expected {size * size}."
            )
        constraints["cages"] = kk_cages
        constraints["has_box_regions"] = False
        region_layout = [[r * size + c for c in range(size)] for r in range(size)]

    elif variant == "kakuro":
        from richards_sudoku.solver.variant_generators import build_kakuro_clue_positions  # noqa: PLC0415
        mask_raw_k = _req("mask")
        row_strs_k = [r for r in mask_raw_k.split("/") if r]
        if len(row_strs_k) != size:
            raise ValueError(f"Kakuro mask has {len(row_strs_k)} rows; expected {size}.")
        black_cells_k: list = []
        for r_k, rs_k in enumerate(row_strs_k):
            if len(rs_k) != size:
                raise ValueError(f"Kakuro mask row {r_k} has length {len(rs_k)}; expected {size}.")
            for c_k, ch_k in enumerate(rs_k):
                if ch_k == "B":
                    black_cells_k.append([r_k, c_k])
                elif ch_k != ".":
                    raise ValueError(f"Unexpected mask character '{ch_k}' at row {r_k} col {c_k}.")
        constraints["black_cells"] = black_cells_k
        clue_lines = headers.get("clue", [])
        if not clue_lines:
            raise ValueError("Kakuro puzzle requires at least one 'clue' line.")
        valid_dirs_k = {"across", "down"}
        kakuro_clues: list[dict] = []
        across_cov: set[tuple[int, int]] = set()
        down_cov: set[tuple[int, int]] = set()
        for i_k, raw_k in enumerate(clue_lines):
            parts_k = raw_k.rsplit(":", 2)
            if len(parts_k) != 3:
                raise ValueError(
                    f"Kakuro clue line {i_k} must be 'r,c ...:sum:dir'; got '{raw_k}'."
                )
            cells_part_k, sum_str_k, dir_k = parts_k
            dir_k = dir_k.strip()
            if dir_k not in valid_dirs_k:
                raise ValueError(
                    f"Kakuro clue {i_k} dir must be 'across' or 'down'; got {dir_k!r}."
                )
            run_sum_k = int(sum_str_k.strip())
            cells_k: list = []
            cov_k = across_cov if dir_k == "across" else down_cov
            for tok_k in cells_part_k.split():
                rc_k = tok_k.split(",")
                if len(rc_k) != 2:
                    raise ValueError(f"Kakuro clue {i_k} cell token '{tok_k}' is not 'r,c'.")
                rr_k, cc_k = int(rc_k[0]), int(rc_k[1])
                key_k = (rr_k, cc_k)
                if key_k in cov_k:
                    raise ValueError(
                        f"Kakuro clue {i_k} ({dir_k}): cell {list(key_k)} in multiple {dir_k} runs."
                    )
                cov_k.add(key_k)
                cells_k.append([rr_k, cc_k])
            kakuro_clues.append({"cells": cells_k, "sum": run_sum_k, "dir": dir_k})
        constraints["clues"] = kakuro_clues
        constraints["clue_positions"] = build_kakuro_clue_positions(kakuro_clues)
        region_layout = [[(rr // 3) * 3 + (cc // 3) for cc in range(size)] for rr in range(size)]

    elif variant == "codewords":
        codebook_raw = headers.get("codebook", [])
        if not codebook_raw:
            raise ValueError("Codewords puzzle requires a 'codebook:' header.")
        codebook: dict[str, int] = {}
        for token in codebook_raw[0].split(","):
            token = token.strip()
            if "=" not in token:
                raise ValueError(f"codebook token '{token}' is not 'letter=digit'.")
            letter, digit_str = token.split("=", 1)
            codebook[letter.strip()] = int(digit_str.strip())
        valid_letters = set("ABCDEFGHI")
        if set(codebook.keys()) != valid_letters:
            raise ValueError(
                f"Codewords codebook must map exactly letters A–I; got {sorted(codebook.keys())!r}."
            )
        if set(codebook.values()) != set(range(1, 10)):
            raise ValueError(
                "Codewords codebook must map bijectively to digits 1–9."
            )
        constraints["codebook"] = codebook
        given_mappings_raw = headers.get("given_mappings", [])
        if given_mappings_raw:
            given_mappings: dict[str, int] = {}
            for token in given_mappings_raw[0].split(","):
                token = token.strip()
                if "=" not in token:
                    raise ValueError(f"given_mappings token '{token}' is not 'letter=digit'.")
                letter, digit_str = token.split("=", 1)
                l = letter.strip()
                d = int(digit_str.strip())
                if codebook.get(l) != d:
                    raise ValueError(
                        f"given_mappings entry {l}={d} contradicts codebook ({l}={codebook.get(l)})."
                    )
                given_mappings[l] = d
            constraints["given_mappings"] = given_mappings
        # Standard box layout for Codewords (9×9)
        region_layout = [[(rr // 3) * 3 + (cc // 3) for cc in range(size)] for rr in range(size)]

    else:
        # Standard / 1to25: standard box layout
        sq = int(size ** 0.5)
        region_layout = [[(rr // sq) * sq + (cc // sq) for cc in range(size)] for rr in range(size)]

    # --- parse digit rows ---
    if len(remaining) != size:
        raise ValueError(
            f"Expected {size} digit rows; got {len(remaining)}."
        )
    board_values: list[list[int | None]] = []
    for r, row_str in enumerate(remaining):
        if variant == "1to25":
            tokens = row_str.split()
            if len(tokens) != size:
                raise ValueError(
                    f"Row {r} has {len(tokens)} tokens; expected {size}."
                )
            row_vals: list[int | None] = [int(t) if int(t) != 0 else None for t in tokens]
        elif variant == "codewords":
            if len(row_str) != size:
                raise ValueError(
                    f"Row {r} has length {len(row_str)}; expected {size}."
                )
            cb = constraints.get("codebook", {})
            row_vals = []
            for ch in row_str:
                if ch == "0":
                    row_vals.append(None)
                elif ch in cb:
                    row_vals.append(cb[ch])
                else:
                    raise ValueError(
                        f"Codewords row {r}: character '{ch}' not in codebook."
                    )
        elif variant == "kakuro":
            if len(row_str) != size:
                raise ValueError(
                    f"Row {r} has length {len(row_str)}; expected {size}."
                )
            row_vals = []
            for ch in row_str:
                if ch in ("_", "0"):
                    row_vals.append(None)
                else:
                    row_vals.append(int(ch))
        else:
            if len(row_str) != size:
                raise ValueError(
                    f"Row {r} has length {len(row_str)}; expected {size}."
                )
            row_vals = [int(ch) if ch != "0" else None for ch in row_str]
        board_values.append(row_vals)

    # Build symbols
    symbols = list(range(1, size + 1))

    meta_dict: dict[str, Any] = {
        "name": variant,
        "size": size,
        "symbols": symbols,
        "region_layout": region_layout,
        "constraints": constraints,
    }

    return board_values, meta_dict, seed, difficulty
