"""Game Complete dialog — shown when the player finishes a puzzle."""
from __future__ import annotations

from enum import IntEnum

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from richards_sudoku.ui.theme import make_font


class GameCompleteDialog(QDialog):
    """Dialog presented on puzzle completion.

    Shows SE score/label, time, move count and hints used.
    Offers three choices: OK (dismiss), New Game, or Restart.
    """

    class Result(IntEnum):
        OK = 0
        NEW_GAME = 1
        RESTART = 2

    def __init__(
        self,
        parent=None,
        *,
        se_score: float = 0.0,
        se_label: str = "Unknown",
        elapsed_seconds: float = 0.0,
        moves: int = 0,
        hints_used: int = 0,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Puzzle Complete!")
        self.setModal(True)
        self._result_choice = GameCompleteDialog.Result.OK

        mins, secs = divmod(int(elapsed_seconds), 60)
        time_str = f"{mins:02d}:{secs:02d}"

        if se_score > 0.0:
            difficulty_text = f"{se_label} ({se_score:.1f})"
        else:
            difficulty_text = se_label or "Unknown"

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title_lbl = QLabel("🎉 Congratulations!")
        title_font = make_font(16)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        stats_lbl = QLabel(
            f"Difficulty: {difficulty_text}\n"
            f"Time:       {time_str}\n"
            f"Moves:      {moves}\n"
            f"Hints:      {hints_used}"
        )
        stats_lbl.setFont(make_font(10))
        stats_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(stats_lbl)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_new = QPushButton("New Game")
        btn_restart = QPushButton("Restart")
        btn_ok.setFont(make_font(9))
        btn_new.setFont(make_font(9))
        btn_restart.setFont(make_font(9))
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_restart)
        layout.addLayout(btn_layout)

        btn_ok.clicked.connect(self._on_ok)
        btn_new.clicked.connect(self._on_new_game)
        btn_restart.clicked.connect(self._on_restart)

        self.setMinimumWidth(300)

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------

    @property
    def result_choice(self) -> "GameCompleteDialog.Result":
        return self._result_choice

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_ok(self) -> None:
        self._result_choice = GameCompleteDialog.Result.OK
        self.accept()

    def _on_new_game(self) -> None:
        self._result_choice = GameCompleteDialog.Result.NEW_GAME
        self.accept()

    def _on_restart(self) -> None:
        self._result_choice = GameCompleteDialog.Result.RESTART
        self.accept()
