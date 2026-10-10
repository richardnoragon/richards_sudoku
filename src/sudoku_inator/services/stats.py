"""Game statistics tracking service."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GameStats:
    """Aggregate statistics for a single game session.

    Attributes:
        moves:           Total number of value/pencil-mark moves made.
        hints_used:      Number of hint actions requested by the player.
        elapsed_seconds: Final elapsed time when the game was completed
                          (set by the caller on completion; 0.0 while in-play).
    """

    moves: int = 0
    hints_used: int = 0
    elapsed_seconds: float = 0.0

    # ------------------------------------------------------------------
    # Counters
    # ------------------------------------------------------------------

    def record_move(self) -> None:
        """Increment the move counter by one."""
        self.moves += 1

    def record_hint(self) -> None:
        """Increment the hints-used counter by one."""
        self.hints_used += 1

    def set_completion_time(self, seconds: float) -> None:
        """Record the final elapsed time on puzzle completion."""
        self.elapsed_seconds = seconds

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "moves": self.moves,
            "hints_used": self.hints_used,
            "elapsed_seconds": self.elapsed_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameStats:
        return cls(
            moves=int(data["moves"]),
            hints_used=int(data["hints_used"]),
            elapsed_seconds=float(data["elapsed_seconds"]),
        )
