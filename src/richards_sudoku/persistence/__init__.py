"""Public API for the persistence layer."""
from richards_sudoku.persistence.persistence import SaveState, save, load

__all__ = ["SaveState", "save", "load"]
