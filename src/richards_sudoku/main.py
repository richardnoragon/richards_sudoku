"""Entry point for the richards_sudoku application."""
from __future__ import annotations

import random
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence
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

from richards_sudoku.controller.game_controller import GameController
from richards_sudoku.ui.game_complete_dialog import GameCompleteDialog
from richards_sudoku.ui.grid_widget import SudokuGridWidget
from richards_sudoku.ui.new_game_dialog import NewGameDialog
from richards_sudoku.ui.theme import DARK, LIGHT, apply_palette, make_font


class MainWindow(QMainWindow):
    """Application shell: menus, toolbar, grid, status bar."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Richards Sudoku")
        self.resize(700, 760)

        self._dark_mode = False

        # --- Central widget: scrollable grid (K3) ---
        from PyQt6.QtWidgets import QScrollArea
        self._grid = SudokuGridWidget()
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
            field.setReadOnly(True)  # locked/given slots — player cannot edit in the panel
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

        # --- Timer display refresh ---
        self._clock = QTimer(self)
        self._clock.setInterval(1000)
        self._clock.timeout.connect(self._refresh_timer_label)

        self._update_action_states()

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
        self._act_restart.triggered.connect(lambda: self._ctrl.restart_game(reset_timer=False))
        self._act_restart_timer.triggered.connect(lambda: self._ctrl.restart_game(reset_timer=True))

    def _action(self, label: str, shortcut: str, tip: str) -> QAction:
        act = QAction(label, self)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
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
        sb.addWidget(self._lbl_mode)

        # Hint mode radio buttons
        self._hint_mode_group = QButtonGroup(self)
        _hint_modes = [
            ("Auto", "auto_fill"),
            ("Reveal", "reveal_cell"),
            ("Elim.", "eliminate"),
            ("Naked", "naked_single"),
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
        sb.addPermanentWidget(self._lbl_timer)

        self._lbl_difficulty = QLabel("SE: ---")
        self._lbl_difficulty.setFont(make_font(9))
        sb.addPermanentWidget(self._lbl_difficulty)

        self._lbl_cell = QLabel("")
        self._lbl_cell.setFont(make_font(9))
        sb.addPermanentWidget(self._lbl_cell)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_pencil_mode_toggled(self, checked: bool) -> None:
        self._grid.set_pencil_mode(checked)
        self._lbl_mode.setText("Mode: Pencil" if checked else "Mode: Normal")

    def _on_dark_mode_toggled(self, checked: bool) -> None:
        self._dark_mode = checked
        self._grid.set_dark_mode(checked)
        apply_palette(QApplication.instance(), DARK if checked else LIGHT)  # type: ignore[arg-type]

    def _on_cell_selected(self, row: int, col: int) -> None:
        self._lbl_cell.setText(f"R{row + 1}C{col + 1}")

    def _on_edit_made(self, *_args) -> None:
        """Called after any value or pencil-mark change; refresh action states."""
        self._update_action_states()

    def _on_new_game(self) -> None:
        initial_seed = random.randrange(2 ** 31)
        dlg = NewGameDialog(self, initial_seed=initial_seed)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        meta = dlg.meta
        difficulty = dlg.difficulty
        hint_limit = dlg.hint_limit
        self._ctrl.new_game(
            meta=meta,
            difficulty=difficulty,
            seed=initial_seed,
            hint_limit=hint_limit,
        )
        self._clock.start()
        self._refresh_difficulty_label()
        self._update_action_states()
        self._refresh_codebook_panel(meta)
        self.statusBar().showMessage("New game started.", 3000)

    def _on_undo(self) -> None:
        if self._ctrl.undo():
            self._update_action_states()

    def _on_redo(self) -> None:
        if self._ctrl.redo():
            self._update_action_states()

    def _on_hint(self) -> None:
        if self._ctrl.hint(mode=self._hint_mode):
            self._update_action_states()

    def _on_open(self) -> None:
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
        self._update_action_states()
        self._refresh_codebook_panel(self._ctrl.variant_meta)
        self.statusBar().showMessage(f"Loaded: {path}", 3000)

    def _on_save(self) -> None:
        if self._ctrl.save_path is not None:
            try:
                self._ctrl.save_game()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "Save failed", str(exc))
                return
            self.statusBar().showMessage(f"Saved: {self._ctrl.save_path}", 3000)
        else:
            self._on_save_as()

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Game As", "", "Sudoku saves (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            self._ctrl.save_game(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        self.statusBar().showMessage(f"Saved: {path}", 3000)

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
            self._ctrl.restart_game()
            self._clock.start()
            self._update_action_states()

    def _refresh_timer_label(self) -> None:
        elapsed = int(self._ctrl.elapsed_seconds)
        mins, secs = divmod(elapsed, 60)
        self._lbl_timer.setText(f"{mins:02d}:{secs:02d}")

    def _refresh_codebook_panel(self, meta) -> None:
        """Show/update the Codebook Panel for Codewords; hide it for all other variants."""
        if meta is None or meta.name.value != "codewords":
            self._codebook_dock.hide()
            return

        codebook: dict[str, int] = meta.constraints.get("codebook") or {}
        given_mappings: dict[str, int] = meta.constraints.get("given_mappings") or {}
        letters = list("ABCDEFGHI")
        for i, letter in enumerate(letters):
            field = self._codebook_fields[i]
            digit = codebook.get(letter)
            if digit is not None:
                field.setText(str(digit))
            else:
                field.clear()
            # Bold and read-only for given mappings
            bold = letter in given_mappings
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
