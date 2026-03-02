"""Entry point for the richards_sudoku application."""
from __future__ import annotations

import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QStatusBar,
    QToolBar,
    QWidget,
)

from richards_sudoku.controller.game_controller import GameController
from richards_sudoku.ui.grid_widget import SudokuGridWidget
from richards_sudoku.ui.theme import DARK, LIGHT, apply_palette, make_font


class MainWindow(QMainWindow):
    """Application shell: menus, toolbar, grid, status bar."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Richards Sudoku")
        self.resize(700, 760)

        self._dark_mode = False

        # --- Central widget: grid ---
        self._grid = SudokuGridWidget()
        self.setCentralWidget(self._grid)

        # --- Controller (subscribes to grid signals internally) ---
        self._ctrl = GameController(self._grid)

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

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sb.addWidget(spacer)

        self._lbl_timer = QLabel("00:00")
        self._lbl_timer.setFont(make_font(9))
        sb.addPermanentWidget(self._lbl_timer)

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
        self._ctrl.new_game()
        self._clock.start()
        self._update_action_states()
        self.statusBar().showMessage("New game started.", 3000)

    def _on_undo(self) -> None:
        if self._ctrl.undo():
            self._update_action_states()

    def _on_redo(self) -> None:
        if self._ctrl.redo():
            self._update_action_states()

    def _on_hint(self) -> None:
        if self._ctrl.hint():
            self._update_action_states()
            if self._ctrl.is_complete:
                self._on_game_complete()

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
        self._update_action_states()
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
        elapsed = self._ctrl.stats.elapsed_seconds
        mins, secs = divmod(int(elapsed), 60)
        QMessageBox.information(
            self,
            "Puzzle Complete!",
            f"Congratulations! Completed in {mins:02d}:{secs:02d}.\n"
            f"Moves: {self._ctrl.stats.moves}   Hints: {self._ctrl.stats.hints_used}",
        )
        self._clock.stop()

    def _refresh_timer_label(self) -> None:
        elapsed = int(self._ctrl.elapsed_seconds)
        mins, secs = divmod(elapsed, 60)
        self._lbl_timer.setText(f"{mins:02d}:{secs:02d}")

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
