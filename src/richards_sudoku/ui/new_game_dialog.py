"""New Game dialog — lets the player choose variant, difficulty, and hint limit.

Also hosts the background generation workers for Jigsaw, Str8ts, and Killer
variants.  Standard puzzles are generated synchronously (fast enough for the
UI thread).
"""
from __future__ import annotations

import random
import threading
import time
from typing import Any

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from richards_sudoku.model.types import Variant, VariantMetadata
from richards_sudoku.ui.theme import make_font


_MAX_GENERATION_RETRIES = 50
# Maximum seconds allowed for a single uniqueness check during 25×25 clue
# removal.  Checks that exceed this budget treat the cell as "keep" (the
# result is conservatively False), so a puzzle may end up with a few extra
# givens but will always be correct and valid.
_ONE_TO_25_CHECK_TIMEOUT = 2.0
# If a single generation attempt has not finished after this many seconds,
# emit the best puzzle built so far (may have a few more givens than the
# target, but will be valid and uniquely solvable).
_ONE_TO_25_ATTEMPT_TIMEOUT = 25.0


# ---------------------------------------------------------------------------
# Background workers (F3)
# ---------------------------------------------------------------------------

class _GenerationWorker(QObject):
    """Base worker: runs in a QThread; emits finished(meta, puzzle, solution) or error(msg)."""

    finished = pyqtSignal(object, object, object)  # (meta, puzzle, solution)
    error = pyqtSignal(str)
    failed = pyqtSignal(str)  # emitted when generation exhausts retries

    def __init__(
        self,
        seed: int,
        difficulty: str,
        cancel_flag: list[bool],
    ) -> None:
        super().__init__()
        self._seed = seed
        self._difficulty = difficulty
        self._cancel_flag = cancel_flag
        self._stop = threading.Event()

    def stop(self) -> None:
        self._cancel_flag[0] = True
        self._stop.set()

    def run(self) -> None:  # override in subclasses
        raise NotImplementedError


class JigsawWorker(_GenerationWorker):
    """Generate a Jigsaw puzzle in a background thread."""

    def run(self) -> None:
        try:
            from richards_sudoku.services.variant_registry import REGISTRY
            from richards_sudoku.solver.generator import generate_puzzle, GenerationCancelled

            cancel_flag = [False]
            self._cancel_flag = cancel_flag  # fresh per attempt

            meta = REGISTRY[Variant.JIGSAW]["factory"](
                seed=self._seed, difficulty=self._difficulty
            )
            constraint_ok = REGISTRY[Variant.JIGSAW].get("constraint_ok")

            for attempt in range(_MAX_GENERATION_RETRIES):
                if cancel_flag[0] or self._stop.is_set():
                    return
                cancel_flag = [False]
                try:
                    puzzle, solution = generate_puzzle(
                        size=meta.size,
                        region_layout=meta.region_layout,
                        symbols=meta.symbols,
                        seed=self._seed + attempt,
                        difficulty=self._difficulty,
                        meta=meta,
                        constraint_ok=constraint_ok,
                        cancel_flag=cancel_flag,
                    )
                    self.finished.emit(meta, puzzle, solution)
                    return
                except GenerationCancelled:
                    if self._stop.is_set():
                        return
            self.error.emit("Generation failed — please try again")
        except Exception as exc:
            self.error.emit(str(exc))


class Str8tsWorker(_GenerationWorker):
    """Generate a Str8ts puzzle in a background thread."""

    def run(self) -> None:
        try:
            from richards_sudoku.services.variant_registry import REGISTRY
            from richards_sudoku.solver.generator import generate_puzzle, GenerationCancelled

            for attempt in range(_MAX_GENERATION_RETRIES):
                if self._stop.is_set():
                    return
                cancel_flag: list[bool] = [False]
                self._cancel_flag = cancel_flag
                try:
                    meta = REGISTRY[Variant.STR8TS]["factory"](
                        seed=self._seed + attempt, difficulty=self._difficulty
                    )
                    constraint_ok = REGISTRY[Variant.STR8TS].get("constraint_ok")
                    puzzle, solution = generate_puzzle(
                        size=meta.size,
                        region_layout=meta.region_layout,
                        symbols=meta.symbols,
                        seed=self._seed + attempt,
                        difficulty=self._difficulty,
                        meta=meta,
                        constraint_ok=constraint_ok,
                        cancel_flag=cancel_flag,
                    )
                    self.finished.emit(meta, puzzle, solution)
                    return
                except GenerationCancelled:
                    if self._stop.is_set():
                        return
            self.error.emit("Generation failed — please try again")
        except Exception as exc:
            self.error.emit(str(exc))


class KillerWorker(_GenerationWorker):
    """Generate a Killer Sudoku puzzle in a background thread."""

    def run(self) -> None:
        try:
            from richards_sudoku.services.variant_registry import REGISTRY
            from richards_sudoku.solver.generator import generate_solution, GenerationCancelled
            from richards_sudoku.solver.variant_generators import CagePartitioner, _PartitionCancelled

            for attempt in range(_MAX_GENERATION_RETRIES):
                if self._stop.is_set():
                    return
                cancel_flag: list[bool] = [False]
                self._cancel_flag = cancel_flag
                try:
                    meta = REGISTRY[Variant.KILLER]["factory"](
                        seed=self._seed + attempt, difficulty=self._difficulty
                    )
                    solution = generate_solution(
                        size=meta.size,
                        region_layout=meta.region_layout,
                        symbols=meta.symbols,
                        seed=self._seed + attempt,
                    )
                    partitioner = CagePartitioner(
                        size=meta.size,
                        seed=self._seed + attempt,
                        difficulty=self._difficulty,
                    )
                    cages = partitioner.partition(solution, cancel_flag=cancel_flag)
                    # Inject cages into meta
                    meta.constraints["cages"] = cages
                    # Build constraint_ok from cages
                    from richards_sudoku.services.variant_registry import _killer_constraint_ok
                    constraint_ok = _killer_constraint_ok(cages)
                    # Puzzle is all-empty; solution provides hints
                    puzzle = [[None] * meta.size for _ in range(meta.size)]
                    self.finished.emit(meta, puzzle, solution)
                    return
                except (_PartitionCancelled, GenerationCancelled):
                    if self._stop.is_set():
                        return
            self.error.emit("Generation failed — please try again")
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# ONE_TO_25 worker (K2)
# ---------------------------------------------------------------------------

# Target givens for 25×25 puzzles (easy/medium only; hard/expert use templates).
# Calibrated to stay above the ~320-given "hard uniqueness zone" where
# backtracking depth explodes for runtime generation.
_ONE_TO_25_GIVENS: dict[str, int] = {
    "easy": 325,    # fill 300 cells
    "medium": 310,  # fill 315 cells
}


def _apply_template_transform(
    puzzle: list[list],
    solution: list[list],
    rng: random.Random,
) -> tuple[list[list], list[list]]:
    """Apply a random isomorphic transformation so each game looks unique.

    The transform (identical set of shuffles as OneToTwentyFiveGenerator) is:
      1. Shuffle row-bands (swap which 5-row block appears first)
      2. Shuffle rows within each band
      3. Shuffle column-bands
      4. Shuffle columns within each column-band
      5. Relabel symbols (1-25 permutation)
    All operations preserve sudoku correctness.
    """
    size = 25
    box = 5

    def _apply_row_col_perm(grid, row_perm, col_perm):
        return [[grid[r][col_perm[c]] for c in range(size)] for r in row_perm]

    # Build row permutation
    band_order = list(range(box))
    rng.shuffle(band_order)
    row_perm: list[int] = []
    for bnd in band_order:
        rows_in_band = list(range(bnd * box, bnd * box + box))
        rng.shuffle(rows_in_band)
        row_perm.extend(rows_in_band)

    # Build column permutation
    col_band_order = list(range(box))
    rng.shuffle(col_band_order)
    col_perm: list[int] = []
    for cb in col_band_order:
        cols_in_band = list(range(cb * box, cb * box + box))
        rng.shuffle(cols_in_band)
        col_perm.extend(cols_in_band)

    # Apply row/col permutation to both grids
    new_puzzle = _apply_row_col_perm(puzzle, row_perm, col_perm)
    new_solution = _apply_row_col_perm(solution, row_perm, col_perm)

    # Relabel symbols
    syms = list(range(1, size + 1))
    rng.shuffle(syms)
    sym_map = {i + 1: syms[i] for i in range(size)}
    new_solution = [[sym_map[v] for v in row] for row in new_solution]
    new_puzzle = [
        [sym_map[v] if v is not None else None for v in row]
        for row in new_puzzle
    ]

    return new_puzzle, new_solution


class OneToTwentyFiveWorker(_GenerationWorker):
    """Generate a 25×25 (1–25) puzzle in a background thread.

    Hard/expert difficulties use pre-generated templates (fast path, ~1 s).
    Easy/medium are generated at runtime (3–20 s).
    """

    def run(self) -> None:
        try:
            import sys
            from richards_sudoku.services.variant_registry import REGISTRY

            sys.setrecursionlimit(max(sys.getrecursionlimit(), 5000))

            cancel_flag: list[bool] = [False]
            self._cancel_flag = cancel_flag

            if self._stop.is_set():
                return

            import random as _random
            rng = _random.Random(self._seed)

            meta = REGISTRY[Variant.ONE_TO_25]["factory"](
                seed=self._seed, difficulty=self._difficulty
            )

            # ── Fast path: hard/expert use pre-generated templates ──────────
            if self._difficulty in ("hard", "expert"):
                from richards_sudoku.solver.one_to_25_templates import _TEMPLATES
                templates = _TEMPLATES[self._difficulty]
                # Pick template based on seed so different seeds → different bases
                tmpl_puzzle_raw, tmpl_solution_raw = templates[self._seed % len(templates)]
                # Apply random isomorphic transform for visual variety
                puzzle, solution = _apply_template_transform(
                    [row[:] for row in tmpl_puzzle_raw],
                    [row[:] for row in tmpl_solution_raw],
                    rng,
                )
                if not self._stop.is_set():
                    self.finished.emit(meta, puzzle, solution)
                return

            # ── Runtime path: easy/medium ───────────────────────────────────
            from richards_sudoku.solver.variant_generators import OneToTwentyFiveGenerator
            from richards_sudoku.solver.generator import check_unique
            from richards_sudoku.solver.solver import _build_peer_cache, _build_region_units

            for attempt in range(_MAX_GENERATION_RETRIES):
                if self._stop.is_set():
                    return
                cancel_flag = [False]
                self._cancel_flag = cancel_flag
                try:
                    attempt_meta = REGISTRY[Variant.ONE_TO_25]["factory"](
                        seed=self._seed + attempt, difficulty=self._difficulty
                    )
                    attempt_peer_cache = _build_peer_cache(attempt_meta.size, attempt_meta.region_layout)
                    attempt_region_units = _build_region_units(attempt_meta.size, attempt_meta.region_layout)

                    gen = OneToTwentyFiveGenerator(
                        size=25, seed=self._seed + attempt, difficulty=self._difficulty, rng=rng
                    )
                    solution = gen.generate(cancel_flag=cancel_flag)
                    if not solution or cancel_flag[0]:
                        if self._stop.is_set():
                            return
                        continue

                    target_givens = _ONE_TO_25_GIVENS[self._difficulty]
                    size = attempt_meta.size
                    puzzle = [row[:] for row in solution]
                    all_cells = [(r, c) for r in range(size) for c in range(size)]
                    rng.shuffle(all_cells)

                    filled = size * size
                    attempt_start = time.perf_counter()
                    for row, col in all_cells:
                        if cancel_flag[0] or self._stop.is_set():
                            break
                        if filled <= target_givens:
                            break
                        if time.perf_counter() - attempt_start > _ONE_TO_25_ATTEMPT_TIMEOUT:
                            break
                        saved = puzzle[row][col]
                        puzzle[row][col] = None
                        per_check_cancel: list[bool] = [False]
                        timer = threading.Timer(
                            _ONE_TO_25_CHECK_TIMEOUT,
                            per_check_cancel.__setitem__,
                            args=(0, True),
                        )
                        timer.start()
                        try:
                            is_unique = check_unique(
                                attempt_meta, puzzle,
                                cancel_flag=per_check_cancel,
                                peer_cache=attempt_peer_cache,
                                region_units=attempt_region_units,
                            )
                        finally:
                            timer.cancel()
                        if is_unique and not per_check_cancel[0]:
                            filled -= 1
                        else:
                            puzzle[row][col] = saved

                    if self._stop.is_set():
                        return
                    if cancel_flag[0]:
                        continue

                    self.finished.emit(attempt_meta, puzzle, solution)
                    return
                except Exception:
                    if self._stop.is_set():
                        return
            self.error.emit("Generation failed — please try again")
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Codewords worker (L2)
# ---------------------------------------------------------------------------

class CodewordsWorker(_GenerationWorker):
    """Generate a Codewords Sudoku puzzle in a background thread.

    ``CodewordsGenerator`` encapsulates all five pipeline steps.  This worker
    is the thread/cancel shell that calls it and maps the result to the
    ``(meta, puzzle, solution)`` tuple expected by ``NewGameDialog``.
    """

    def run(self) -> None:
        try:
            from richards_sudoku.solver.variant_generators import CodewordsGenerator
            from richards_sudoku.services.variant_registry import REGISTRY

            cancel_flag: list[bool] = [False]
            self._cancel_flag = cancel_flag

            if self._stop.is_set():
                return

            import random as _random
            rng = _random.Random(self._seed)

            gen = CodewordsGenerator(
                size=9,
                seed=self._seed,
                difficulty=self._difficulty,
                rng=rng,
            )
            try:
                result = gen.generate(cancel_flag=cancel_flag)
            except RuntimeError:
                # Cancelled during generation
                return

            if self._stop.is_set():
                return

            meta = REGISTRY[Variant.CODEWORDS]["factory"](
                seed=self._seed, difficulty=self._difficulty
            )
            # Inject codebook/given_mappings into meta constraints
            meta.constraints["codebook"] = result["codebook"]
            meta.constraints["given_mappings"] = result["given_mappings"]

            self.finished.emit(meta, result["puzzle"], result["solution"])
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# KenKen worker (M3)
# ---------------------------------------------------------------------------

class KenKenWorker(_GenerationWorker):
    """Generate a KenKen puzzle in a background thread.

    Pipeline (per attempt):
    1. Generate an N×N Latin square via ``generate_solution``.
    2. Partition it into cages via ``KenKenCagePartitioner``.
    3. Use all single-cell cages as givens; all other cells stay blank.
    4. Emit ``finished`` on success or ``failed`` after exhausting retries.
    """

    def __init__(
        self,
        seed: int,
        difficulty: str,
        cancel_flag: list[bool],
        size: int = 9,
    ) -> None:
        super().__init__(seed, difficulty, cancel_flag)
        self._size = size

    def run(self) -> None:
        try:
            from richards_sudoku.services.variant_registry import REGISTRY
            from richards_sudoku.solver.generator import generate_solution
            from richards_sudoku.solver.variant_generators import KenKenCagePartitioner
            import math

            size = self._size
            symbols = list(range(1, size + 1))
            region_layout = [[r * size + c for c in range(size)] for r in range(size)]

            for attempt in range(_MAX_GENERATION_RETRIES):
                if self._stop.is_set():
                    return
                cancel_flag: list[bool] = [False]
                self._cancel_flag = cancel_flag

                try:
                    # Phase 1 — Latin square
                    solution = generate_solution(
                        size=size,
                        region_layout=region_layout,
                        symbols=symbols,
                        seed=self._seed + attempt,
                    )

                    if cancel_flag[0] or self._stop.is_set():
                        return

                    # Phase 2 — cage partition
                    partitioner = KenKenCagePartitioner(
                        size=size,
                        seed=self._seed + attempt,
                        difficulty=self._difficulty,
                    )
                    cages = partitioner.partition(solution, cancel_flag=cancel_flag)

                    if cancel_flag[0] or self._stop.is_set():
                        return

                    # Phase 3 — build puzzle (single-cell cages become givens)
                    puzzle: list[list[int | None]] = [
                        [None] * size for _ in range(size)
                    ]
                    for cage in cages:
                        if len(cage["cells"]) == 1:
                            r, c = cage["cells"][0]
                            puzzle[r][c] = solution[r][c]

                    # Phase 4 — assemble meta and emit
                    meta = REGISTRY[Variant.KENKEN]["factory"](
                        seed=self._seed + attempt,
                        difficulty=self._difficulty,
                        size=size,
                    )
                    meta.constraints["cages"] = cages

                    self.finished.emit(meta, puzzle, solution)
                    return

                except RuntimeError:
                    # Cancelled during partition
                    if self._stop.is_set():
                        return

            self.failed.emit("Generation failed — please try again")
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Kakuro worker (N2)
# ---------------------------------------------------------------------------

class KakuroWorker(_GenerationWorker):
    """Generate a Kakuro puzzle in a background thread.

    Pipeline (per attempt):
    1. Generate a random Kakuro layout via ``KakuroTemplateLibrary``.
    2. Fill the template with valid digits via ``KakuroFillGenerator``.
    3. Derive run sums from the filled grid to build the clue list.
    4. Verify solution uniqueness, then emit ``finished``.
    """

    def __init__(self, seed: int, difficulty: str, cancel_flag: list[bool]) -> None:
        super().__init__(seed, difficulty, cancel_flag)
        self._size = 9  # Kakuro is always 9×9

    def run(self) -> None:
        try:
            from richards_sudoku.services.variant_registry import REGISTRY
            from richards_sudoku.solver.generator import check_unique
            from richards_sudoku.solver.variant_generators import (
                KakuroFillGenerator,
                KakuroTemplateLibrary,
                build_kakuro_clue_positions,
            )

            size = self._size

            for attempt in range(_MAX_GENERATION_RETRIES):
                if self._stop.is_set():
                    return
                cancel_flag: list[bool] = [False]
                self._cancel_flag = cancel_flag

                try:
                    seed_a = self._seed + attempt

                    # Phase 1 — layout template
                    library = KakuroTemplateLibrary(size, seed_a, self._difficulty)
                    template = library.generate(cancel_flag=cancel_flag)
                    if template is None or cancel_flag[0] or self._stop.is_set():
                        continue

                    # Phase 2 — fill with digits
                    filler = KakuroFillGenerator(template, seed=seed_a)
                    filled = filler.fill(cancel_flag=cancel_flag)
                    if filled is None or cancel_flag[0] or self._stop.is_set():
                        continue

                    # Phase 3 — derive clues from filled solution
                    clues = []
                    for run in template["runs"]:
                        cells = [(int(p[0]), int(p[1])) for p in run["cells"]]
                        run_sum = sum(filled[r][c] for r, c in cells)
                        clues.append({"cells": cells, "sum": run_sum, "dir": run["dir"]})

                    black_cells = [[int(r), int(c)] for r, c in template["black_cells"]]
                    clue_positions = build_kakuro_clue_positions(clues)

                    # Phase 4 — assemble meta
                    meta = REGISTRY[Variant.KAKURO]["factory"](
                        seed=seed_a, difficulty=self._difficulty
                    )
                    meta.constraints["clues"] = clues
                    meta.constraints["black_cells"] = black_cells
                    meta.constraints["clue_positions"] = clue_positions

                    # Apply black cells to region_layout and cell map
                    black_set = {(int(r), int(c)) for r, c in black_cells}
                    for r, c in black_set:
                        meta.region_layout[r][c] = -1  # sentinel for black

                    # Phase 5 — uniqueness check (run-sum + no-repeat)
                    def _constraint_ok(g: list[list]) -> bool:
                        for clue in clues:
                            cells_c = [(int(p[0]), int(p[1])) for p in clue["cells"]]
                            vals = [g[r][c] for r, c in cells_c]
                            if None in vals:
                                continue
                            if sum(vals) != int(clue["sum"]):
                                return False
                            if len(set(vals)) != len(vals):
                                return False
                        return True

                    white_sets = {(int(r), int(c)) for r, c in meta.constraints["clues"][0]["cells"]}
                    # Build run-based peer_cache for uniqueness solver
                    from richards_sudoku.solver.solver import _build_peer_cache
                    white_cells_all = [
                        (r, c) for r in range(size) for c in range(size)
                        if (r, c) not in black_set
                    ]
                    peers_map: dict = {wc: set() for wc in white_cells_all}
                    for clue in clues:
                        clue_cells = [(int(p[0]), int(p[1])) for p in clue["cells"]]
                        for cell in clue_cells:
                            peers_map[cell].update(d for d in clue_cells if d != cell)
                    peer_cache = {cell: frozenset(p) for cell, p in peers_map.items()}

                    puzzle: list[list] = [[None] * size for _ in range(size)]

                    unique = check_unique(
                        puzzle=puzzle,
                        solution=filled,
                        size=size,
                        symbols=list(range(1, 10)),
                        peer_cache=peer_cache,
                        region_units=[],
                        constraint_ok=_constraint_ok,
                    )
                    if not unique or cancel_flag[0] or self._stop.is_set():
                        continue

                    self.finished.emit(meta, puzzle, filled)
                    return

                except RuntimeError:
                    if self._stop.is_set():
                        return

            self.failed.emit("Generation failed — please try again")
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

class NewGameDialog(QDialog):
    """Dialog for starting a new game.

    Parameters
    ----------
    initial_seed:
        RNG seed computed by the caller before the dialog opens, ensuring
        reproducibility when the same seed is reused.
    """

    _VARIANTS = [
        ("Standard", Variant.STANDARD, True),
        ("Jigsaw", Variant.JIGSAW, True),
        ("Str8ts", Variant.STR8TS, True),
        ("Killer", Variant.KILLER, True),
        ("1 to 25", Variant.ONE_TO_25, True),
        ("Codewords", Variant.CODEWORDS, True),
        ("KenKen", Variant.KENKEN, True),          # enabled in M3
        ("Kakuro", Variant.KAKURO, True),          # enabled in N2
    ]
    _DIFFICULTIES = ["easy", "medium", "hard", "expert"]

    def __init__(self, parent=None, initial_seed: int = 0) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Game")
        self.setModal(True)
        self._seed = initial_seed
        self._meta: VariantMetadata | None = None
        self._difficulty_str: str = "medium"
        self._hint_limit: int | None = 3
        self._puzzle: Any = None
        self._solution: Any = None
        self._worker: _GenerationWorker | None = None
        self._thread: QThread | None = None

        self._build_ui()
        self._update_hint_limit_state()

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def meta(self) -> VariantMetadata | None:
        return self._meta

    @property
    def difficulty(self) -> str:
        return self._difficulty_str

    @property
    def hint_limit(self) -> int | None:
        return self._hint_limit

    @property
    def puzzle(self) -> Any:
        return self._puzzle

    @property
    def solution(self) -> Any:
        return self._solution

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()

        self._variant_combo = QComboBox()
        for label, _variant, enabled in self._VARIANTS:
            self._variant_combo.addItem(label)
            if not enabled:
                # Grey-out items that have no worker yet
                idx = self._variant_combo.count() - 1
                model = self._variant_combo.model()
                from PyQt6.QtGui import QStandardItem
                item: QStandardItem = model.item(idx)  # type: ignore[assignment]
                item.setEnabled(False)
        self._variant_combo.setFont(make_font(9))
        self._variant_combo.currentIndexChanged.connect(self._on_variant_changed)
        form.addRow("Variant:", self._variant_combo)

        self._size_combo = QComboBox()
        self._size_combo.addItem("9×9")
        self._size_combo.setEnabled(False)  # fixed for most variants
        self._size_combo.setFont(make_font(9))
        form.addRow("Size:", self._size_combo)

        self._diff_combo = QComboBox()
        for d in self._DIFFICULTIES:
            self._diff_combo.addItem(d.capitalize(), d)
        self._diff_combo.setCurrentIndex(1)  # medium
        self._diff_combo.setFont(make_font(9))
        form.addRow("Difficulty:", self._diff_combo)

        self._hint_spin = QSpinBox()
        self._hint_spin.setRange(1, 99)
        self._hint_spin.setValue(3)
        self._hint_spin.setFont(make_font(9))
        self._hint_unlimited = QCheckBox("Unlimited")
        self._hint_unlimited.setFont(make_font(9))
        self._hint_unlimited.toggled.connect(self._update_hint_limit_state)

        hint_widget = QWidget()
        from PyQt6.QtWidgets import QHBoxLayout
        hl = QHBoxLayout(hint_widget)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self._hint_spin)
        hl.addWidget(self._hint_unlimited)
        form.addRow("Hints:", hint_widget)

        layout.addLayout(form)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status_lbl = QLabel("")
        self._status_lbl.setFont(make_font(8))
        layout.addWidget(self._status_lbl)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self._on_cancel)
        layout.addWidget(buttons)
        self._btn_ok = buttons.button(QDialogButtonBox.StandardButton.Ok)

    def _update_hint_limit_state(self) -> None:
        unlimited = self._hint_unlimited.isChecked()
        self._hint_spin.setEnabled(not unlimited)

    def _on_variant_changed(self, idx: int) -> None:
        _label, variant, _enabled = self._VARIANTS[idx]
        self._size_combo.blockSignals(True)
        self._size_combo.clear()
        if variant == Variant.ONE_TO_25:
            self._size_combo.addItem("25×25")
            self._size_combo.setEnabled(False)
        elif variant == Variant.KENKEN:
            for s in ("4×4", "6×6", "9×9"):
                self._size_combo.addItem(s)
            self._size_combo.setCurrentText("9×9")
            self._size_combo.setEnabled(True)  # enabled fully in M3
        else:
            self._size_combo.addItem("9×9")
            self._size_combo.setEnabled(False)
        self._size_combo.blockSignals(False)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_ok(self) -> None:
        label, variant, _enabled = self._VARIANTS[self._variant_combo.currentIndex()]
        self._difficulty_str = self._diff_combo.currentData()
        if self._hint_unlimited.isChecked():
            self._hint_limit = None
        else:
            self._hint_limit = self._hint_spin.value()

        if variant == Variant.STANDARD:
            self._generate_standard(variant)
        elif variant == Variant.JIGSAW:
            self._start_worker(JigsawWorker(self._seed, self._difficulty_str, [False]))
        elif variant == Variant.STR8TS:
            self._start_worker(Str8tsWorker(self._seed, self._difficulty_str, [False]))
        elif variant == Variant.KILLER:
            self._start_worker(KillerWorker(self._seed, self._difficulty_str, [False]))
        elif variant == Variant.ONE_TO_25:
            self._start_worker(OneToTwentyFiveWorker(self._seed, self._difficulty_str, [False]))
        elif variant == Variant.CODEWORDS:
            self._start_worker(CodewordsWorker(self._seed, self._difficulty_str, [False]))
        elif variant == Variant.KENKEN:
            size_label = self._size_combo.currentText()
            n = int(size_label.split("×")[0])
            self._start_worker(KenKenWorker(self._seed, self._difficulty_str, [False], n))
        elif variant == Variant.KAKURO:
            self._start_worker(KakuroWorker(self._seed, self._difficulty_str, [False]))

    def _generate_standard(self, variant: Variant) -> None:
        from richards_sudoku.services.variant_registry import REGISTRY
        from richards_sudoku.solver.generator import generate_puzzle
        meta = REGISTRY[Variant.STANDARD]["factory"](seed=self._seed, difficulty=self._difficulty_str)
        puzzle, solution = generate_puzzle(
            size=meta.size,
            region_layout=meta.region_layout,
            symbols=meta.symbols,
            seed=self._seed,
            difficulty=self._difficulty_str,
        )
        self._meta = meta
        self._puzzle = puzzle
        self._solution = solution
        self.accept()

    def _start_worker(self, worker: _GenerationWorker) -> None:
        self._worker = worker
        self._thread = QThread()
        worker.moveToThread(self._thread)
        worker.finished.connect(self._on_worker_finished)
        worker.error.connect(self._on_worker_error)
        worker.failed.connect(self._on_worker_failed)
        self._thread.started.connect(worker.run)
        self._progress.setVisible(True)
        self._btn_ok.setEnabled(False)
        self._status_lbl.setText("Generating puzzle…")
        self._thread.start()

    def _on_worker_finished(self, meta: Any, puzzle: Any, solution: Any) -> None:
        self._meta = meta
        self._puzzle = puzzle
        self._solution = solution
        self._cleanup_worker()
        self.accept()

    def _on_worker_error(self, msg: str) -> None:
        self._cleanup_worker()
        self._status_lbl.setText(f"Error: {msg}")
        self._btn_ok.setEnabled(True)
        self._progress.setVisible(False)

    def _on_worker_failed(self, reason: str) -> None:
        self._cleanup_worker()
        self._status_lbl.setText(f"Generation failed — please try again ({reason})")
        self._btn_ok.setEnabled(True)
        self._progress.setVisible(False)

    def _on_cancel(self) -> None:
        self._stop_worker()
        self.reject()

    def _stop_worker(self) -> None:
        if self._worker is not None:
            self._worker.stop()
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(2000)

    def _cleanup_worker(self) -> None:
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(2000)
        self._worker = None
        self._thread = None
        self._progress.setVisible(False)
        self._btn_ok.setEnabled(True)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._stop_worker()
        super().closeEvent(event)
