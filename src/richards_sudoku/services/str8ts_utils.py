"""Str8ts utility: straight (consecutive run) extendability check."""
from __future__ import annotations


def _can_extend_straight(placed: list[int], length: int, v: int) -> bool:
    """Return True if digit *v* can appear in a straight run of *length* cells
    that already contains the digits in *placed*.

    A valid straight is a set of *length* distinct consecutive integers.
    We check whether ``placed + [v]`` is a subset of any window of *length*
    consecutive integers within [1, 9].

    Parameters
    ----------
    placed:
        Values already committed in this run (may include given digits and
        player entries); does NOT include *v*.
    length:
        Total number of cells in the run.
    v:
        Candidate digit to test.

    Returns
    -------
    bool
        True if there exists a window ``[k, k+length-1]`` that contains
        both *v* and all values in *placed*.
    """
    if v in placed:
        return False  # duplicates not allowed in a straight
    all_vals = placed + [v]
    lo = min(all_vals)
    hi = max(all_vals)
    if hi - lo >= length:
        return False  # span already exceeds window size
    # Check every valid window that covers [lo, hi]
    for start in range(max(1, hi - length + 1), lo + 1):
        end = start + length - 1
        if end > 9:
            break
        if all(lo >= start and hi <= end for _ in (1,)):
            return True
    return False
