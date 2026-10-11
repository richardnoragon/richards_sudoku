"""Game timer service.

Measures elapsed wall-clock seconds across pause/resume cycles.
Uses time.monotonic() for accuracy.
"""
from __future__ import annotations

import time
from typing import Any


class GameTimer:
    """Tracks elapsed time for a Sudoku game session.

    Lifecycle:
        start() → running
        pause() → paused (elapsed accumulates)
        resume() → running again
        reset() → back to initial state
    """

    def __init__(self) -> None:
        self._accumulated: float = 0.0
        self._start: float | None = None  # monotonic timestamp when last started/resumed

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._start is not None

    def elapsed_seconds(self) -> float:
        """Return total elapsed seconds, including any currently running segment."""
        if self._start is not None:
            return self._accumulated + (time.monotonic() - self._start)
        return self._accumulated

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start timing from zero.  No-op if already running."""
        if self._start is None:
            self._accumulated = 0.0
            self._start = time.monotonic()

    def pause(self) -> None:
        """Pause timing and accumulate elapsed time.  No-op if already paused."""
        if self._start is not None:
            self._accumulated += time.monotonic() - self._start
            self._start = None

    def resume(self) -> None:
        """Resume a paused timer.  No-op if already running."""
        if self._start is None:
            self._start = time.monotonic()

    def reset(self) -> None:
        """Stop and zero the timer."""
        self._accumulated = 0.0
        self._start = None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise state for persistence.  Always saved in paused form."""
        return {
            "elapsed_seconds": self.elapsed_seconds(),
            "is_running": self.is_running,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameTimer:
        """Restore a timer from a previously serialised dict.

        The restored timer is always paused; callers should call resume()
        if they want it to be running immediately after load.
        """
        timer = cls()
        timer._accumulated = float(data["elapsed_seconds"])
        # Never restore in running state — caller decides when to resume.
        return timer
