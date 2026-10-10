"""Entry point for the sudoku_inator application."""
from __future__ import annotations

import random
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QIntValidator, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QDockWidget,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QRadioButton,
    QSizePolicy,
    QStatusBar,
    QToolBar,
    QWidget,
)

from sudoku_inator.controller.game_controller import GameController
from sudoku_inator.model.types import VariantMetadata
from sudoku_inator.ui.game_complete_dialog import GameCompleteDialog
from sudoku_inator.ui.grid_widget import SudokuGridWidget
from sudoku_inator.ui.new_game_dialog import NewGameDialog
from sudoku_inator.ui.theme import DARK, LIGHT, apply_palette, make_font


class MainWindow(QMainWindow):
    """Application shell: menus, toolbar, grid, status bar."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("sudoku-inator")
        self.resize(700, 760)
        self.setAccessibleName("sudoku-inator main window")

        self._dark_mode = False

        # --- Central widget: scrollable grid (K3) ---
        from PyQt6.QtWidgets import QScrollArea
        self._grid = SudokuGridWidget()
        self._grid.setAccessibleName("Sudoku board")
        scroll = QScrollArea()
        scroll.setWidget(self._grid)
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(scroll)

        # --- Codebook Panel (L4) — QDockWidget, bottom, hidden by default ---
        self._codebook_dock = QDockWidget("Codebook", self)
        self._codebook_dock.setObjectName("codebook_dock")
        self._codebook_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self._codebook_widget = QWidget()
        self._codebook_layout = QGridLayout(self._codebook_widget)
        self._codebook_layout.setContentsMargins(4, 4, 4, 4)
        self._codebook_layout.setSpacing(4)
        # 9 slots: A–I labels + digit fields
        self._codebook_fields: list[QLineEdit] = []
        letters = list("ABCDEFGHI")
        for i, letter in enumerate(letters):
            lbl = QLabel(f"{letter}:")
            field = QLineEdit()
            field.setMaximumWidth(32)
            field.setReadOnly(True)
            field.setValidator(QIntValidator(1, 9, field))
            field.setMaxLength(1)
            field.setAccessibleName(f"Codeword {letter} digit hypothesis")
            field.editingFinished.connect(lambda l=letter, f=field: self._on_codebook_edit(l, f))
            self._codebook_layout.addWidget(lbl, 0, i * 2)
            self._codebook_layout.addWidget(field, 0, i * 2 + 1)
            self._codebook_fields.append(field)
        self._codebook_dock.setWidget(self._codebook_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._codebook_dock)
        self._codebook_dock.hide()

        # --- Controller (subscribes to grid signals internally) ---
        self._ctrl = GameController(self._grid)
        self._ctrl.set_complete_callback(self._on_game_complete)

        # Hint mode (for status bar radio buttons)
        self._hint_mode: str = "auto_fill"

        # --- Connect grid signals ---
        self._grid.cell_selected.connect(self._on_cell_selected)
        # value_entered and pencil_toggled are handled by the controller;
        # we additionally hook them to refresh action states.
        self._grid.value_entered.connect(self._on_edit_made)
        self._grid.pencil_toggled.connect(self._on_edit_made)

        # --- Build chrome ---
        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._build_status_bar()

        self._ctrl.new_game(
            meta=VariantMetadata.standard_9x9(),
            difficulty="medium",
            seed=random.randrange(2 ** 31),
            hint_limit=3,
        )
        self._refresh_progress_label()
        self._clock = QTimer(self)
        self._clock.setInterval(1000)
        self._clock.timeout.connect(self._refresh_timer_label)
        self._clock.start()

        self._refresh_difficulty_label()
        self._refresh_board_context("New game started.")
        self._update_action_states()

    def _refresh_board_context(self, message: str | None = None) -> None:
        """Reset shell labels after a new board is bound or restarted."""
        self._grid.clear_selection()
        self._lbl_cell.clear()
        self._refresh_timer_label()
        self._refresh_progress_label()
        self._update_action_states()
        if message is not None:
            self.statusBar().showMessage(message, 3000)

    # ------------------------------------------------------------------
    # Action construction
    # ------------------------------------------------------------------

    def _build_actions(self) -> None:
        # File
        self._act_new = self._action("&New Game", "Ctrl+N", "Start a new standard game")
        self._act_open = self._action("&Open…", "Ctrl+O", "Open a saved game")
        self._act_save = self._action("&Save", "Ctrl+S", "Save current game")
        self._act_save_as = self._action("Save &As…", "Ctrl+Shift+S", "Save to a new file")
        self._act_import = self._action("&Import Puzzle…", "", "Import from JSON or text")
        self._act_export = self._action("&Export Puzzle…", "", "Export to JSON or text")
        self._act_quit = self._action("&Quit", "Ctrl+Q", "Exit the application")
        self._act_quit.triggered.connect(self.close)

        # Edit
        self._act_enter = self._action("Enter &Value…", "F4", "Enter any value, including 10–25; also works in pencil mode")
        self._act_enter.triggered.connect(self._grid.enter_value)
        self._act_undo = self._action("&Undo", "Ctrl+Z", "Undo last move")
        self._act_redo = self._action("&Redo", "Ctrl+Y", "Redo last undone move")
        self._act_pencil = self._action("&Pencil Mode", "P", "Toggle pencil/candidate entry")
        self._act_pencil.setCheckable(True)
        self._act_pencil.triggered.connect(self._on_pencil_mode_toggled)

        # Game
        self._act_hint = self._action("&Hint", "H", "Show a hint")
        self._act_check = self._action("&Check Board", "F5", "Check for conflicts")
        self._act_restart = self._action("&Restart", "F9", "Restart (keep timer)")
        self._act_restart_timer = self._action("Restart && Reset &Timer", "Shift+F9",
                                               "Restart and reset timer")

        # View
        self._act_dark = self._action("&Dark Mode", "F2", "Toggle dark/light theme")
        self._act_dark.setCheckable(True)
        self._act_dark.triggered.connect(self._on_dark_mode_toggled)

        # Wire triggered signals (all actions defined above)
        self._act_new.triggered.connect(self._on_new_game)
        self._act_open.triggered.connect(self._on_open)
        self._act_save.triggered.connect(self._on_save)
        self._act_save_as.triggered.connect(self._on_save_as)
        self._act_undo.triggered.connect(self._on_undo)
        self._act_redo.triggered.connect(self._on_redo)
        self._act_hint.triggered.connect(self._on_hint)
        self._act_restart.triggered.connect(lambda: self._on_restart(False))
        self._act_restart_timer.triggered.connect(lambda: self._on_restart(True))
        self._act_import.triggered.connect(self._on_import)
        self._act_export.triggered.connect(self._on_export)
        self._act_check.triggered.connect(self._on_check)

    def _action(self, label: str, shortcut: str, tip: str) -> QAction:
        act = QAction(label, self)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        act.setToolTip(tip)
        act.setStatusTip(tip)
        act.setWhatsThis(tip)
        act.setStatusTip(tip)
        return act

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------

    def _build_menus(self) -> None:
        mb = self.menuBar()

        file_menu = mb.addMenu("&File")
        file_menu.addAction(self._act_new)
        file_menu.addSeparator()
        file_menu.addAction(self._act_open)
        file_menu.addAction(self._act_save)
        file_menu.addAction(self._act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self._act_import)
        file_menu.addAction(self._act_export)
        file_menu.addSeparator()
        file_menu.addAction(self._act_quit)

        edit_menu = mb.addMenu("&Edit")
        edit_menu.addAction(self._act_undo)
        edit_menu.addAction(self._act_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self._act_pencil)
        edit_menu.addAction(self._act_enter)

        game_menu = mb.addMenu("&Game")
        game_menu.addAction(self._act_hint)
        game_menu.addAction(self._act_check)
        game_menu.addSeparator()
        restart_menu = game_menu.addMenu("&Restart")
        restart_menu.addAction(self._act_restart)
        restart_menu.addAction(self._act_restart_timer)

        view_menu = mb.addMenu("&View")
        view_menu.addAction(self._act_dark)

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main Toolbar", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        tb.addAction(self._act_new)
        tb.addSeparator()
        tb.addAction(self._act_open)
        tb.addAction(self._act_save)
        tb.addSeparator()
        tb.addAction(self._act_undo)
        tb.addAction(self._act_redo)
        tb.addSeparator()
        tb.addAction(self._act_pencil)
        tb.addAction(self._act_enter)
        tb.addAction(self._act_hint)
        tb.addSeparator()
        tb.addAction(self._act_dark)

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    def _build_status_bar(self) -> None:
        sb = QStatusBar(self)
        self.setStatusBar(sb)

        self._lbl_mode = QLabel("Mode: Normal")
        self._lbl_mode.setFont(make_font(9))
        self._lbl_mode.setAccessibleName("Current input mode")
        sb.addWidget(self._lbl_mode)

        # Hint mode radio buttons
        self._hint_mode_group = QButtonGroup(self)
        _hint_modes = [
            ("Auto", "auto_fill"),
            ("Reveal", "reveal_cell"),
            ("Elim.", "eliminate"),
            ("Naked", "naked_single"),
            ("Candidate", "show_candidate"),
        ]
        for label, mode in _hint_modes:
            rb = QRadioButton(label)
            rb.setFont(make_font(8))
            rb.setChecked(mode == "auto_fill")
            rb.toggled.connect(
                lambda checked, m=mode: setattr(self, "_hint_mode", m) if checked else None
            )
            self._hint_mode_group.addButton(rb)
            sb.addWidget(rb)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sb.addWidget(spacer)

        self._lbl_timer = QLabel("00:00")
        self._lbl_timer.setFont(make_font(9))
        self._lbl_timer.setAccessibleName("Elapsed game time")
        sb.addPermanentWidget(self._lbl_timer)

        self._lbl_progress = QLabel("Progress 0% • 0 singles")
        self._lbl_progress.setFont(make_font(9))
        self._lbl_progress.setAccessibleName("Board progress and guidance summary")
        sb.addPermanentWidget(self._lbl_progress)

        self._lbl_difficulty = QLabel("SE: ---")
        self._lbl_difficulty.setFont(make_font(9))
        self._lbl_difficulty.setAccessibleName("Puzzle difficulty rating")
        sb.addPermanentWidget(self._lbl_difficulty)

        self._lbl_cell = QLabel("")
        self._lbl_cell.setFont(make_font(9))
        self._lbl_cell.setAccessibleName("Selected cell")
        sb.addPermanentWidget(self._lbl_cell)

        self.statusBar().showMessage(
            "Keyboard: arrows move, digits enter, F4 enters any value, Delete clears, P toggles pencil.",
            0,
        )

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_pencil_mode_toggled(self, checked: bool) -> None:
        self._grid.set_pencil_mode(checked)
        self._lbl_mode.setText("Mode: Pencil" if checked else "Mode: Normal")
        self.statusBar().showMessage(
            "Pencil mode on — type a digit to add or remove a candidate." if checked
            else "Pencil mode off — digits enter values directly.",
            3000,
        )

    def _on_dark_mode_toggled(self, checked: bool) -> None:
        self._dark_mode = checked
        self._grid.set_dark_mode(checked)
        apply_palette(QApplication.instance(), DARK if checked else LIGHT)  # type: ignore[arg-type]

    def _on_cell_selected(self, row: int, col: int) -> None:
        self._lbl_cell.setText(f"Selected: R{row + 1}C{col + 1}")
        self._refresh_progress_label()
        self.statusBar().showMessage(
            f"Selected R{row + 1}C{col + 1}. Use arrows or Tab to navigate.",
            2000,
        )

    def _on_edit_made(self, *_args) -> None:
        """Called after any value or pencil-mark change; refresh action states."""
        if self._ctrl._timer.is_running:
            self._clock.start()
        else:
            self._clock.stop()
        self._update_action_states()
        self._refresh_progress_label()

    def _on_new_game(self) -> None:
        if not self._confirm_discard():
            return
        initial_seed = random.randrange(2 ** 31)
        dlg = NewGameDialog(self, initial_seed=initial_seed)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        meta = dlg.meta
        difficulty = dlg.difficulty
        hint_limit = dlg.hint_limit
        try:
            self._ctrl.new_game(
                meta=meta,
                difficulty=difficulty,
                seed=initial_seed,
                hint_limit=hint_limit,
                puzzle=dlg.puzzle,
                solution=dlg.solution,
            )
        except Exception as exc:
            QMessageBox.critical(self, "New game failed", str(exc))
            return
        self._clock.start()
        self._refresh_difficulty_label()
        self._refresh_board_context("New game started.")
        self._refresh_codebook_panel(meta)

    def _on_undo(self) -> None:
        if self._ctrl.undo():
            self._on_edit_made()
            self._refresh_codebook_panel(self._ctrl.variant_meta)

    def _on_redo(self) -> None:
        if self._ctrl.redo():
            self._on_edit_made()
            self._refresh_codebook_panel(self._ctrl.variant_meta)

    def _on_hint(self) -> None:
        if self._ctrl.hint(mode=self._hint_mode):
            self._on_edit_made()
            self._refresh_codebook_panel(self._ctrl.variant_meta)
        else:
            self.statusBar().showMessage("No hint available: check selection, allowance, and solution availability.", 5000)

    def _confirm_discard(self) -> bool:
        if not self._ctrl.is_dirty:
            return True
        answer = QMessageBox.warning(
            self, "Unsaved progress", "Save your progress before continuing?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self._on_save()
        return answer == QMessageBox.StandardButton.Discard

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()

    def _on_restart(self, reset_timer: bool = True) -> None:
        if not self._confirm_discard():
            return
        self._ctrl.restart_game(reset_timer=reset_timer)
        self._clock.start()
        self._refresh_board_context("Game restarted.")
        self._refresh_codebook_panel(self._ctrl.variant_meta)

    def _on_import(self) -> None:
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Puzzle", "", "Puzzles (*.json *.txt);;All files (*)")
        if not path:
            return
        try:
            self._ctrl.import_puzzle(path)
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", str(exc))
            return
        self._clock.start()
        self._refresh_difficulty_label()
        self._refresh_board_context(f"Imported: {path}")
        self._refresh_codebook_panel(self._ctrl.variant_meta)

    def _on_export(self) -> None:
        path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export Puzzle", "", "Puzzle text (*.txt);;Sudoku session (*.json)")
        if not path:
            return
        as_text = Path(path).suffix.lower() != ".json"
        if not Path(path).suffix:
            as_text = "*.json" not in selected_filter
            path += ".txt" if as_text else ".json"
        # Exporting over a live JSON save as text would destroy its session format.
        if self._ctrl.save_path and Path(path).resolve() == self._ctrl.save_path.resolve() and as_text:
            QMessageBox.critical(self, "Export failed", "Choose a different file from the current JSON save.")
            return
        try:
            self._ctrl.export_puzzle(path, as_text=as_text)
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self.statusBar().showMessage(f"Exported: {path}", 5000)

    def _on_check(self) -> None:
        from sudoku_inator.services.validation import conflict_cells
        board, meta = self._ctrl._board, self._ctrl.variant_meta
        if board is None or meta is None:
            return
        conflicts = conflict_cells(board, meta)
        message = (f"Conflicts found in {len(conflicts)} cells." if conflicts else
                   "Board complete and valid." if self._ctrl.is_complete else
                   "No conflicts found. The puzzle is not yet complete.")
        self._grid.refresh()
        self.statusBar().showMessage(message, 10000)

    def _on_codebook_edit(self, letter, field) -> None:
        text = field.text()
        value = int(text) if text.isdigit() else None
        if not self._ctrl.set_codebook_hypothesis(letter, value):
            self.statusBar().showMessage("Use a distinct digit 1–9 for each editable mapping.", 3000)
        self._refresh_codebook_panel(self._ctrl.variant_meta)
        self._on_edit_made()

    def _on_open(self) -> None:
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Game", "", "Sudoku saves (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            self._ctrl.load_game(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Load failed", str(exc))
            return
        self._clock.start()
        self._refresh_difficulty_label()
        self._refresh_board_context(f"Loaded: {path}")
        self._refresh_codebook_panel(self._ctrl.variant_meta)

    def _on_save(self) -> bool:
        if self._ctrl.save_path is not None:
            try:
                self._ctrl.save_game()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "Save failed", str(exc))
                return False
            self.statusBar().showMessage(f"Saved: {self._ctrl.save_path}", 3000)
            return True
        else:
            return self._on_save_as()

    def _on_save_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Game As", "", "Sudoku saves (*.json);;All files (*)"
        )
        if not path:
            return False
        try:
            self._ctrl.save_game(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save failed", str(exc))
            return False
        self.statusBar().showMessage(f"Saved: {path}", 3000)
        return True

    def _on_game_complete(self) -> None:
        self._clock.stop()
        score, label = self._ctrl.se_rating
        dlg = GameCompleteDialog(
            self,
            se_score=score,
            se_label=label,
            elapsed_seconds=self._ctrl.elapsed_seconds,
            moves=self._ctrl.stats.moves,
            hints_used=self._ctrl.stats.hints_used,
        )
        dlg.exec()
        choice = dlg.result_choice
        if choice == GameCompleteDialog.Result.NEW_GAME:
            self._on_new_game()
        elif choice == GameCompleteDialog.Result.RESTART:
            self._on_restart(True)

    def _refresh_timer_label(self) -> None:
        elapsed = int(self._ctrl.elapsed_seconds)
        mins, secs = divmod(elapsed, 60)
        self._lbl_timer.setText(f"{mins:02d}:{secs:02d}")

    def _refresh_progress_label(self) -> None:
        self._lbl_progress.setText(self._ctrl.progress_text)

    def _refresh_codebook_panel(self, meta) -> None:
        """Show/update the Codebook Panel for Codewords; hide it for all other variants."""
        if meta is None or meta.name.value != "codewords":
            self._codebook_dock.hide()
            return

        given_mappings: dict[str, int] = meta.constraints.get("given_mappings") or {}
        letters = list("ABCDEFGHI")
        for i, letter in enumerate(letters):
            field = self._codebook_fields[i]
            hypotheses = self._ctrl._board.codebook_hypotheses if self._ctrl._board else {}
            digit = given_mappings.get(letter, hypotheses.get(letter))
            if digit is not None:
                field.setText(str(digit))
            else:
                field.clear()
            # Bold and read-only for given mappings
            bold = letter in given_mappings
            field.setReadOnly(bold)
            field.setToolTip("Given mapping" if bold else "Hypothesis: enter an unused digit 1–9, or clear")
            font = field.font()
            font.setBold(bold)
            field.setFont(font)

        self._codebook_dock.show()

    def _refresh_difficulty_label(self) -> None:
        score, label = self._ctrl.se_rating
        if label == "Invalid":
            self._lbl_difficulty.setText("SE: Invalid")
        elif score > 0.0:
            self._lbl_difficulty.setText(f"SE: {label} ({score:.1f})")
        else:
            self._lbl_difficulty.setText("SE: ---")

    def _update_action_states(self) -> None:
        """Enable/disable actions based on current state."""
        has_board = self._grid._board is not None
        self._act_save.setEnabled(has_board)
        self._act_save_as.setEnabled(has_board)
        self._act_export.setEnabled(has_board)
        self._act_undo.setEnabled(self._ctrl.can_undo)
        self._act_redo.setEnabled(self._ctrl.can_redo)
        self._act_hint.setEnabled(has_board)
        self._act_check.setEnabled(has_board)

    # ------------------------------------------------------------------
    # Keyboard passthrough
    # ------------------------------------------------------------------

    def keyPressEvent(self, event) -> None:  # noqa: N802
        # Forward unhandled keys to the grid so keyboard-only users do not
        # need to click the grid first.
        if self._grid._board is not None and not self._grid.hasFocus():
            self._grid.setFocus()
            self._grid.keyPressEvent(event)
        else:
            super().keyPressEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setFont(make_font(11))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
