# difficulty_se.py
---

can you help me code the SukakuExplainer Algorithm (for grading difficulty) for my Sudoku applicatin. The application (python, pygame, pyqt6) up and running (sudoku, jigsaw, str8ts and killer sudoku ). i would like to expand the applications capabilities
Great project expansion idea, Richard! SukakuExplainer is essentially a difficulty grading algorithm for Sudoku variants, inspired by Sudoku Explainer. It works by simulating human-style solving techniques and assigning weights to each step until the puzzle is solved. Let’s break down how you could integrate this into your Python/PyQt6/Pygame application.

---

🔑 Core Concepts of SukakuExplainer
Step-based solving simulation  
Each solving technique (e.g., Naked Single, Hidden Pair, X-Wing) is assigned a difficulty weight.

Grading metric  
The puzzle’s difficulty is the maximum weight encountered during solving, or sometimes a cumulative score.

Extensibility  
You can add techniques for Jigsaw, Killer Sudoku, Str8ts, etc., by defining their logical rules and weights.

---

🧩 Suggested Architecture
Since your app already supports multiple puzzle types, you’ll want a modular solver framework:

1. Puzzle Representation

Use a unified grid object (e.g., PuzzleGrid) with metadata for variant rules.

Store candidates for each cell.

2. Technique Registry

Define techniques as classes or functions with:

---

class NakedSingle:
    name = "Naked Single"
    weight = 1.0
    def apply(self, grid):
        # return True if applied, False otherwise


3.Solver Loop

Iterate through techniques in order of increasing difficulty.

Apply until puzzle is solved or no progress can be made.

Track the highest weight used.

def grade_puzzle(grid, techniques):
    max_difficulty = 0
    while not grid.is_solved():
        progress = False
        for tech in techniques:
            if tech.apply(grid):
                max_difficulty = max(max_difficulty, tech.weight)
                progress = True
                break
        if not progress:
            break  # unsolvable with current techniques
    return max_difficulty

---

Difficulty Categories

Map numeric scores to categories:

1–2 → Easy

3–4 → Medium

5–6 → Hard

7+ → Extreme

---

⚙️ Integration Strategy
Backend (Python): Implement the grading engine as a standalone module (difficulty.py).

Frontend (PyQt6/Pygame):

Add a “Grade Puzzle” button.

Display difficulty score + category in the UI.

Optionally show the solving path (step-by-step techniques applied).

---

🚀 Next Steps
1. Start with classic Sudoku techniques (Naked Single, Hidden Single, Naked Pair, Hidden Pair).

2. Add variant-specific techniques:

	Killer Sudoku → cage sum checks.

	Jigsaw → irregular region constraints.

	Str8ts → consecutive run logic.

3. Benchmark against known puzzles to calibrate weights.

Would you like me to draft a starter Python module with a few basic techniques (Naked Single, Hidden Single, Naked Pair) so you can plug it directly into your app and expand from there? That way you’ll have a working skeleton to build on.

---

Sure, please draft a starter Python module with a few basic techniques (Naked Single, Hidden Single, Naked Pair and then we will expand from there
Here’s a clean starter module you can drop into your Sudoku application. It sets up the difficulty grading framework and implements three basic techniques: Naked Single, Hidden Single, and Naked Pair. You can expand it later with more advanced strategies.

---

difficulty.py

--

from collections import defaultdict

class PuzzleGrid:
    def __init__(self, size=9):
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.candidates = [[set(range(1, size+1)) for _ in range(size)] for _ in range(size)]

    def is_solved(self):
        return all(self.grid[r][c] != 0 for r in range(self.size) for c in range(self.size))

    def set_value(self, r, c, val):
        self.grid[r][c] = val
        self.candidates[r][c] = {val}
        # eliminate from row, col, box
        for i in range(self.size):
            if val in self.candidates[r][i] and i != c:
                self.candidates[r][i].discard(val)
            if val in self.candidates[i][c] and i != r:
                self.candidates[i][c].discard(val)
        # box elimination
        box_r, box_c = (r//3)*3, (c//3)*3
        for i in range(box_r, box_r+3):
            for j in range(box_c, box_c+3):
                if val in self.candidates[i][j] and (i,j) != (r,c):
                    self.candidates[i][j].discard(val)


# --- Techniques ---

class NakedSingle:
    name = "Naked Single"
    weight = 1.0

    def apply(self, grid: PuzzleGrid):
        for r in range(grid.size):
            for c in range(grid.size):
                if grid.grid[r][c] == 0 and len(grid.candidates[r][c]) == 1:
                    val = next(iter(grid.candidates[r][c]))
                    grid.set_value(r, c, val)
                    return True
        return False


class HiddenSingle:
    name = "Hidden Single"
    weight = 2.0

    def apply(self, grid: PuzzleGrid):
        # check rows
        for r in range(grid.size):
            counts = defaultdict(list)
            for c in range(grid.size):
                for val in grid.candidates[r][c]:
                    counts[val].append((r,c))
            for val, cells in counts.items():
                if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                    grid.set_value(cells[0][0], cells[0][1], val)
                    return True
        # check columns
        for c in range(grid.size):
            counts = defaultdict(list)
            for r in range(grid.size):
                for val in grid.candidates[r][c]:
                    counts[val].append((r,c))
            for val, cells in counts.items():
                if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                    grid.set_value(cells[0][0], cells[0][1], val)
                    return True
        # check boxes
        for br in range(0, grid.size, 3):
            for bc in range(0, grid.size, 3):
                counts = defaultdict(list)
                for r in range(br, br+3):
                    for c in range(bc, bc+3):
                        for val in grid.candidates[r][c]:
                            counts[val].append((r,c))
                for val, cells in counts.items():
                    if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                        grid.set_value(cells[0][0], cells[0][1], val)
                        return True
        return False


class NakedPair:
    name = "Naked Pair"
    weight = 3.0

    def apply(self, grid: PuzzleGrid):
        # check rows
        for r in range(grid.size):
            pairs = [(c, grid.candidates[r][c]) for c in range(grid.size) if len(grid.candidates[r][c]) == 2]
            seen = {}
            for c, cand in pairs:
                cand_tuple = tuple(sorted(cand))
                if cand_tuple in seen:
                    # eliminate from row
                    for cc in range(grid.size):
                        if cc not in (c, seen[cand_tuple]):
                            grid.candidates[r][cc] -= set(cand_tuple)
                    return True
                else:
                    seen[cand_tuple] = c
        # check columns
        for c in range(grid.size):
            pairs = [(r, grid.candidates[r][c]) for r in range(grid.size) if len(grid.candidates[r][c]) == 2]
            seen = {}
            for r, cand in pairs:
                cand_tuple = tuple(sorted(cand))
                if cand_tuple in seen:
                    for rr in range(grid.size):
                        if rr not in (r, seen[cand_tuple]):
                            grid.candidates[rr][c] -= set(cand_tuple)
                    return True
                else:
                    seen[cand_tuple] = r
        return False


# --- Grader ---

def grade_puzzle(grid: PuzzleGrid, techniques):
    max_difficulty = 0
    while not grid.is_solved():
        progress = False
        for tech in techniques:
            if tech.apply(grid):
                max_difficulty = max(max_difficulty, tech.weight)
                progress = True
                break
        if not progress:
            break
    return max_difficulty


if __name__ == "__main__":
    # Example usage
    grid = PuzzleGrid()
    # Fill grid with starting puzzle values here...
    techniques = [NakedSingle(), HiddenSingle(), NakedPair()]
    difficulty = grade_puzzle(grid, techniques)
    print("Puzzle difficulty:", difficulty)

---

Here’s a clean starter module you can drop into your Sudoku application. It sets up the **difficulty grading framework** and implements three basic techniques: **Naked Single, Hidden Single, and Naked Pair**. You can expand it later with more advanced strategies.

---

## `difficulty.py`

```python
from collections import defaultdict

class PuzzleGrid:
    def __init__(self, size=9):
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.candidates = [[set(range(1, size+1)) for _ in range(size)] for _ in range(size)]

    def is_solved(self):
        return all(self.grid[r][c] != 0 for r in range(self.size) for c in range(self.size))

    def set_value(self, r, c, val):
        self.grid[r][c] = val
        self.candidates[r][c] = {val}
        # eliminate from row, col, box
        for i in range(self.size):
            if val in self.candidates[r][i] and i != c:
                self.candidates[r][i].discard(val)
            if val in self.candidates[i][c] and i != r:
                self.candidates[i][c].discard(val)
        # box elimination
        box_r, box_c = (r//3)*3, (c//3)*3
        for i in range(box_r, box_r+3):
            for j in range(box_c, box_c+3):
                if val in self.candidates[i][j] and (i,j) != (r,c):
                    self.candidates[i][j].discard(val)


# --- Techniques ---

class NakedSingle:
    name = "Naked Single"
    weight = 1.0

    def apply(self, grid: PuzzleGrid):
        for r in range(grid.size):
            for c in range(grid.size):
                if grid.grid[r][c] == 0 and len(grid.candidates[r][c]) == 1:
                    val = next(iter(grid.candidates[r][c]))
                    grid.set_value(r, c, val)
                    return True
        return False


class HiddenSingle:
    name = "Hidden Single"
    weight = 2.0

    def apply(self, grid: PuzzleGrid):
        # check rows
        for r in range(grid.size):
            counts = defaultdict(list)
            for c in range(grid.size):
                for val in grid.candidates[r][c]:
                    counts[val].append((r,c))
            for val, cells in counts.items():
                if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                    grid.set_value(cells[0][0], cells[0][1], val)
                    return True
        # check columns
        for c in range(grid.size):
            counts = defaultdict(list)
            for r in range(grid.size):
                for val in grid.candidates[r][c]:
                    counts[val].append((r,c))
            for val, cells in counts.items():
                if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                    grid.set_value(cells[0][0], cells[0][1], val)
                    return True
        # check boxes
        for br in range(0, grid.size, 3):
            for bc in range(0, grid.size, 3):
                counts = defaultdict(list)
                for r in range(br, br+3):
                    for c in range(bc, bc+3):
                        for val in grid.candidates[r][c]:
                            counts[val].append((r,c))
                for val, cells in counts.items():
                    if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                        grid.set_value(cells[0][0], cells[0][1], val)
                        return True
        return False


class NakedPair:
    name = "Naked Pair"
    weight = 3.0

    def apply(self, grid: PuzzleGrid):
        # check rows
        for r in range(grid.size):
            pairs = [(c, grid.candidates[r][c]) for c in range(grid.size) if len(grid.candidates[r][c]) == 2]
            seen = {}
            for c, cand in pairs:
                cand_tuple = tuple(sorted(cand))
                if cand_tuple in seen:
                    # eliminate from row
                    for cc in range(grid.size):
                        if cc not in (c, seen[cand_tuple]):
                            grid.candidates[r][cc] -= set(cand_tuple)
                    return True
                else:
                    seen[cand_tuple] = c
        # check columns
        for c in range(grid.size):
            pairs = [(r, grid.candidates[r][c]) for r in range(grid.size) if len(grid.candidates[r][c]) == 2]
            seen = {}
            for r, cand in pairs:
                cand_tuple = tuple(sorted(cand))
                if cand_tuple in seen:
                    for rr in range(grid.size):
                        if rr not in (r, seen[cand_tuple]):
                            grid.candidates[rr][c] -= set(cand_tuple)
                    return True
                else:
                    seen[cand_tuple] = r
        return False


# --- Grader ---

def grade_puzzle(grid: PuzzleGrid, techniques):
    max_difficulty = 0
    while not grid.is_solved():
        progress = False
        for tech in techniques:
            if tech.apply(grid):
                max_difficulty = max(max_difficulty, tech.weight)
                progress = True
                break
        if not progress:
            break
    return max_difficulty


if __name__ == "__main__":
    # Example usage
    grid = PuzzleGrid()
    # Fill grid with starting puzzle values here...
    techniques = [NakedSingle(), HiddenSingle(), NakedPair()]
    difficulty = grade_puzzle(grid, techniques)
    print("Puzzle difficulty:", difficulty)
```

---

## How to Use
1. Drop this into your app as `difficulty.py`.
2. Import and call `grade_puzzle(grid, techniques)` after loading a puzzle.
3. Extend by adding more technique classes with `.name`, `.weight`, and `.apply()`.

---

Would you like me to also **draft a simple candidate initialization function** (to populate candidates from a given puzzle state) so you can immediately test this with real Sudoku puzzles? That way you won’t have to manually set candidates before grading.

---

yes, please draft a simple candidate initialization function (to populate candidates from a given puzzle state) so I can immediately test this with real Sudoku puzzles?
Perfect, let’s add a candidate initialization function so you can feed in a puzzle (with given digits and blanks) and automatically populate candidates for all empty cells. This way you can immediately test grading on real Sudoku puzzles.

---

Updated difficulty.py (with candidate initialization)

from collections import defaultdict

class PuzzleGrid:
    def __init__(self, size=9):
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.candidates = [[set(range(1, size+1)) for _ in range(size)] for _ in range(size)]

    def is_solved(self):
        return all(self.grid[r][c] != 0 for r in range(self.size) for c in range(self.size))

    def set_value(self, r, c, val):
        self.grid[r][c] = val
        self.candidates[r][c] = {val}
        # eliminate from row, col, box
        for i in range(self.size):
            if val in self.candidates[r][i] and i != c:
                self.candidates[r][i].discard(val)
            if val in self.candidates[i][c] and i != r:
                self.candidates[i][c].discard(val)
        # box elimination
        box_r, box_c = (r//3)*3, (c//3)*3
        for i in range(box_r, box_r+3):
            for j in range(box_c, box_c+3):
                if val in self.candidates[i][j] and (i,j) != (r,c):
                    self.candidates[i][j].discard(val)


# --- Candidate Initialization ---

def initialize_candidates(grid: PuzzleGrid):
    """Populate candidates for all empty cells based on current grid values."""
    size = grid.size
    digits = set(range(1, size+1))

    for r in range(size):
        for c in range(size):
            if grid.grid[r][c] == 0:
                # start with all digits
                possible = digits.copy()

                # remove row values
                possible -= {grid.grid[r][cc] for cc in range(size) if grid.grid[r][cc] != 0}

                # remove column values
                possible -= {grid.grid[rr][c] for rr in range(size) if grid.grid[rr][c] != 0}

                # remove box values
                box_r, box_c = (r//3)*3, (c//3)*3
                for rr in range(box_r, box_r+3):
                    for cc in range(box_c, box_c+3):
                        if grid.grid[rr][cc] != 0:
                            possible.discard(grid.grid[rr][cc])

                grid.candidates[r][c] = possible
            else:
                grid.candidates[r][c] = {grid.grid[r][c]}

---

Example Usage

---

if __name__ == "__main__":
    puzzle = [
        [5,3,0, 0,7,0, 0,0,0],
        [6,0,0, 1,9,5, 0,0,0],
        [0,9,8, 0,0,0, 0,6,0],

        [8,0,0, 0,6,0, 0,0,3],
        [4,0,0, 8,0,3, 0,0,1],
        [7,0,0, 0,2,0, 0,0,6],

        [0,6,0, 0,0,0, 2,8,0],
        [0,0,0, 4,1,9, 0,0,5],
        [0,0,0, 0,8,0, 0,7,9],
    ]

    grid = PuzzleGrid()
    grid.grid = puzzle
    initialize_candidates(grid)

    techniques = [NakedSingle(), HiddenSingle(), NakedPair()]
    difficulty = grade_puzzle(grid, techniques)
    print("Puzzle difficulty:", difficulty)

---

Perfect, let’s add a **candidate initialization function** so you can feed in a puzzle (with given digits and blanks) and automatically populate candidates for all empty cells. This way you can immediately test grading on real Sudoku puzzles.

---

## Updated `difficulty.py` (with candidate initialization)

```python
from collections import defaultdict

class PuzzleGrid:
    def __init__(self, size=9):
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.candidates = [[set(range(1, size+1)) for _ in range(size)] for _ in range(size)]

    def is_solved(self):
        return all(self.grid[r][c] != 0 for r in range(self.size) for c in range(self.size))

    def set_value(self, r, c, val):
        self.grid[r][c] = val
        self.candidates[r][c] = {val}
        # eliminate from row, col, box
        for i in range(self.size):
            if val in self.candidates[r][i] and i != c:
                self.candidates[r][i].discard(val)
            if val in self.candidates[i][c] and i != r:
                self.candidates[i][c].discard(val)
        # box elimination
        box_r, box_c = (r//3)*3, (c//3)*3
        for i in range(box_r, box_r+3):
            for j in range(box_c, box_c+3):
                if val in self.candidates[i][j] and (i,j) != (r,c):
                    self.candidates[i][j].discard(val)


# --- Candidate Initialization ---

def initialize_candidates(grid: PuzzleGrid):
    """Populate candidates for all empty cells based on current grid values."""
    size = grid.size
    digits = set(range(1, size+1))

    for r in range(size):
        for c in range(size):
            if grid.grid[r][c] == 0:
                # start with all digits
                possible = digits.copy()

                # remove row values
                possible -= {grid.grid[r][cc] for cc in range(size) if grid.grid[r][cc] != 0}

                # remove column values
                possible -= {grid.grid[rr][c] for rr in range(size) if grid.grid[rr][c] != 0}

                # remove box values
                box_r, box_c = (r//3)*3, (c//3)*3
                for rr in range(box_r, box_r+3):
                    for cc in range(box_c, box_c+3):
                        if grid.grid[rr][cc] != 0:
                            possible.discard(grid.grid[rr][cc])

                grid.candidates[r][c] = possible
            else:
                grid.candidates[r][c] = {grid.grid[r][c]}
```

---

## Example Usage

```python
if __name__ == "__main__":
    puzzle = [
        [5,3,0, 0,7,0, 0,0,0],
        [6,0,0, 1,9,5, 0,0,0],
        [0,9,8, 0,0,0, 0,6,0],

        [8,0,0, 0,6,0, 0,0,3],
        [4,0,0, 8,0,3, 0,0,1],
        [7,0,0, 0,2,0, 0,0,6],

        [0,6,0, 0,0,0, 2,8,0],
        [0,0,0, 4,1,9, 0,0,5],
        [0,0,0, 0,8,0, 0,7,9],
    ]

    grid = PuzzleGrid()
    grid.grid = puzzle
    initialize_candidates(grid)

    techniques = [NakedSingle(), HiddenSingle(), NakedPair()]
    difficulty = grade_puzzle(grid, techniques)
    print("Puzzle difficulty:", difficulty)
```

---

## ✅ What This Gives You
- You can now load a puzzle directly into `grid.grid`.
- Call `initialize_candidates(grid)` to set up candidates.
- Run `grade_puzzle(grid, techniques)` to get a difficulty score.

---

Would you like me to also **add a step-tracking log** (recording which technique was applied at each stage) so you can display the solving path in your PyQt6 UI? That would make the grading more transparent and user-friendly.

---

yes, please also add a step-tracking log (recording which technique was applied at each stage) so I can display the solving path in your PyQt6 UI. That would make the grading more transparent and user-friendly.
Here’s the enhanced module with step-tracking built in. Each time a technique is applied, we record the step (technique name, weight, and affected cell/value). This gives you a solving path you can display in your PyQt6 UI.

Updated difficulty.py

---

from collections import defaultdict

class PuzzleGrid:
    def __init__(self, size=9):
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.candidates = [[set(range(1, size+1)) for _ in range(size)] for _ in range(size)]

    def is_solved(self):
        return all(self.grid[r][c] != 0 for r in range(self.size) for c in range(self.size))

    def set_value(self, r, c, val):
        self.grid[r][c] = val
        self.candidates[r][c] = {val}
        # eliminate from row, col, box
        for i in range(self.size):
            if val in self.candidates[r][i] and i != c:
                self.candidates[r][i].discard(val)
            if val in self.candidates[i][c] and i != r:
                self.candidates[i][c].discard(val)
        # box elimination
        box_r, box_c = (r//3)*3, (c//3)*3
        for i in range(box_r, box_r+3):
            for j in range(box_c, box_c+3):
                if val in self.candidates[i][j] and (i,j) != (r,c):
                    self.candidates[i][j].discard(val)


# --- Candidate Initialization ---

def initialize_candidates(grid: PuzzleGrid):
    """Populate candidates for all empty cells based on current grid values."""
    size = grid.size
    digits = set(range(1, size+1))

    for r in range(size):
        for c in range(size):
            if grid.grid[r][c] == 0:
                possible = digits.copy()
                possible -= {grid.grid[r][cc] for cc in range(size) if grid.grid[r][cc] != 0}
                possible -= {grid.grid[rr][c] for rr in range(size) if grid.grid[rr][c] != 0}
                box_r, box_c = (r//3)*3, (c//3)*3
                for rr in range(box_r, box_r+3):
                    for cc in range(box_c, box_c+3):
                        if grid.grid[rr][cc] != 0:
                            possible.discard(grid.grid[rr][cc])
                grid.candidates[r][c] = possible
            else:
                grid.candidates[r][c] = {grid.grid[r][c]}


# --- Techniques ---

class NakedSingle:
    name = "Naked Single"
    weight = 1.0

    def apply(self, grid: PuzzleGrid):
        for r in range(grid.size):
            for c in range(grid.size):
                if grid.grid[r][c] == 0 and len(grid.candidates[r][c]) == 1:
                    val = next(iter(grid.candidates[r][c]))
                    grid.set_value(r, c, val)
                    return {"technique": self.name, "weight": self.weight, "cell": (r,c), "value": val}
        return None


class HiddenSingle:
    name = "Hidden Single"
    weight = 2.0

    def apply(self, grid: PuzzleGrid):
        # check rows
        for r in range(grid.size):
            counts = defaultdict(list)
            for c in range(grid.size):
                for val in grid.candidates[r][c]:
                    counts[val].append((r,c))
            for val, cells in counts.items():
                if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                    grid.set_value(cells[0][0], cells[0][1], val)
                    return {"technique": self.name, "weight": self.weight, "cell": cells[0], "value": val}
        # check columns
        for c in range(grid.size):
            counts = defaultdict(list)
            for r in range(grid.size):
                for val in grid.candidates[r][c]:
                    counts[val].append((r,c))
            for val, cells in counts.items():
                if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                    grid.set_value(cells[0][0], cells[0][1], val)
                    return {"technique": self.name, "weight": self.weight, "cell": cells[0], "value": val}
        # check boxes
        for br in range(0, grid.size, 3):
            for bc in range(0, grid.size, 3):
                counts = defaultdict(list)
                for r in range(br, br+3):
                    for c in range(bc, bc+3):
                        for val in grid.candidates[r][c]:
                            counts[val].append((r,c))
                for val, cells in counts.items():
                    if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                        grid.set_value(cells[0][0], cells[0][1], val)
                        return {"technique": self.name, "weight": self.weight, "cell": cells[0], "value": val}
        return None


class NakedPair:
    name = "Naked Pair"
    weight = 3.0

    def apply(self, grid: PuzzleGrid):
        # check rows
        for r in range(grid.size):
            pairs = [(c, grid.candidates[r][c]) for c in range(grid.size) if len(grid.candidates[r][c]) == 2]
            seen = {}
            for c, cand in pairs:
                cand_tuple = tuple(sorted(cand))
                if cand_tuple in seen:
                    for cc in range(grid.size):
                        if cc not in (c, seen[cand_tuple]):
                            grid.candidates[r][cc] -= set(cand_tuple)
                    return {"technique": self.name, "weight": self.weight, "cell": None, "value": cand_tuple}
                else:
                    seen[cand_tuple] = c
        # check columns
        for c in range(grid.size):
            pairs = [(r, grid.candidates[r][c]) for r in range(grid.size) if len(grid.candidates[r][c]) == 2]
            seen = {}
            for r, cand in pairs:
                cand_tuple = tuple(sorted(cand))
                if cand_tuple in seen:
                    for rr in range(grid.size):
                        if rr not in (r, seen[cand_tuple]):
                            grid.candidates[rr][c] -= set(cand_tuple)
                    return {"technique": self.name, "weight": self.weight, "cell": None, "value": cand_tuple}
                else:
                    seen[cand_tuple] = r
        return None


# --- Grader with Step Log ---

def grade_puzzle(grid: PuzzleGrid, techniques):
    max_difficulty = 0
    steps = []
    while not grid.is_solved():
        progress = False
        for tech in techniques:
            result = tech.apply(grid)
            if result:
                max_difficulty = max(max_difficulty, tech.weight)
                steps.append(result)
                progress = True
                break
        if not progress:
            break
    return max_difficulty, steps


if __name__ == "__main__":
    puzzle = [
        [5,3,0, 0,7,0, 0,0,0],
        [6,0,0, 1,9,5, 0,0,0],
        [0,9,8, 0,0,0, 0,6,0],

        [8,0,0, 0,6,0, 0,0,3],
        [4,0,0, 8,0,3, 0,0,1],
        [7,0,0, 0,2,0, 0,0,6],

        [0,6,0, 0,0,0, 2,8,0],
        [0,0,0, 4,1,9, 0,0,5],
        [0,0,0, 0,8,0, 0,7,9],
    ]

    grid = PuzzleGrid()
    grid.grid = puzzle
    initialize_candidates(grid)

    techniques = [NakedSingle(), HiddenSingle(), NakedPair()]
    difficulty, steps = grade_puzzle(grid, techniques)

    print("Puzzle difficulty:", difficulty)
    print("Solving path:")
    for step in steps:
        print(step)

---

Here’s the enhanced module with **step-tracking** built in. Each time a technique is applied, we record the step (technique name, weight, and affected cell/value). This gives you a solving path you can display in your PyQt6 UI.

---

## Updated `difficulty.py`

```python
from collections import defaultdict

class PuzzleGrid:
    def __init__(self, size=9):
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.candidates = [[set(range(1, size+1)) for _ in range(size)] for _ in range(size)]

    def is_solved(self):
        return all(self.grid[r][c] != 0 for r in range(self.size) for c in range(self.size))

    def set_value(self, r, c, val):
        self.grid[r][c] = val
        self.candidates[r][c] = {val}
        # eliminate from row, col, box
        for i in range(self.size):
            if val in self.candidates[r][i] and i != c:
                self.candidates[r][i].discard(val)
            if val in self.candidates[i][c] and i != r:
                self.candidates[i][c].discard(val)
        # box elimination
        box_r, box_c = (r//3)*3, (c//3)*3
        for i in range(box_r, box_r+3):
            for j in range(box_c, box_c+3):
                if val in self.candidates[i][j] and (i,j) != (r,c):
                    self.candidates[i][j].discard(val)


# --- Candidate Initialization ---

def initialize_candidates(grid: PuzzleGrid):
    """Populate candidates for all empty cells based on current grid values."""
    size = grid.size
    digits = set(range(1, size+1))

    for r in range(size):
        for c in range(size):
            if grid.grid[r][c] == 0:
                possible = digits.copy()
                possible -= {grid.grid[r][cc] for cc in range(size) if grid.grid[r][cc] != 0}
                possible -= {grid.grid[rr][c] for rr in range(size) if grid.grid[rr][c] != 0}
                box_r, box_c = (r//3)*3, (c//3)*3
                for rr in range(box_r, box_r+3):
                    for cc in range(box_c, box_c+3):
                        if grid.grid[rr][cc] != 0:
                            possible.discard(grid.grid[rr][cc])
                grid.candidates[r][c] = possible
            else:
                grid.candidates[r][c] = {grid.grid[r][c]}


# --- Techniques ---

class NakedSingle:
    name = "Naked Single"
    weight = 1.0

    def apply(self, grid: PuzzleGrid):
        for r in range(grid.size):
            for c in range(grid.size):
                if grid.grid[r][c] == 0 and len(grid.candidates[r][c]) == 1:
                    val = next(iter(grid.candidates[r][c]))
                    grid.set_value(r, c, val)
                    return {"technique": self.name, "weight": self.weight, "cell": (r,c), "value": val}
        return None


class HiddenSingle:
    name = "Hidden Single"
    weight = 2.0

    def apply(self, grid: PuzzleGrid):
        # check rows
        for r in range(grid.size):
            counts = defaultdict(list)
            for c in range(grid.size):
                for val in grid.candidates[r][c]:
                    counts[val].append((r,c))
            for val, cells in counts.items():
                if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                    grid.set_value(cells[0][0], cells[0][1], val)
                    return {"technique": self.name, "weight": self.weight, "cell": cells[0], "value": val}
        # check columns
        for c in range(grid.size):
            counts = defaultdict(list)
            for r in range(grid.size):
                for val in grid.candidates[r][c]:
                    counts[val].append((r,c))
            for val, cells in counts.items():
                if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                    grid.set_value(cells[0][0], cells[0][1], val)
                    return {"technique": self.name, "weight": self.weight, "cell": cells[0], "value": val}
        # check boxes
        for br in range(0, grid.size, 3):
            for bc in range(0, grid.size, 3):
                counts = defaultdict(list)
                for r in range(br, br+3):
                    for c in range(bc, bc+3):
                        for val in grid.candidates[r][c]:
                            counts[val].append((r,c))
                for val, cells in counts.items():
                    if len(cells) == 1 and grid.grid[cells[0][0]][cells[0][1]] == 0:
                        grid.set_value(cells[0][0], cells[0][1], val)
                        return {"technique": self.name, "weight": self.weight, "cell": cells[0], "value": val}
        return None


class NakedPair:
    name = "Naked Pair"
    weight = 3.0

    def apply(self, grid: PuzzleGrid):
        # check rows
        for r in range(grid.size):
            pairs = [(c, grid.candidates[r][c]) for c in range(grid.size) if len(grid.candidates[r][c]) == 2]
            seen = {}
            for c, cand in pairs:
                cand_tuple = tuple(sorted(cand))
                if cand_tuple in seen:
                    for cc in range(grid.size):
                        if cc not in (c, seen[cand_tuple]):
                            grid.candidates[r][cc] -= set(cand_tuple)
                    return {"technique": self.name, "weight": self.weight, "cell": None, "value": cand_tuple}
                else:
                    seen[cand_tuple] = c
        # check columns
        for c in range(grid.size):
            pairs = [(r, grid.candidates[r][c]) for r in range(grid.size) if len(grid.candidates[r][c]) == 2]
            seen = {}
            for r, cand in pairs:
                cand_tuple = tuple(sorted(cand))
                if cand_tuple in seen:
                    for rr in range(grid.size):
                        if rr not in (r, seen[cand_tuple]):
                            grid.candidates[rr][c] -= set(cand_tuple)
                    return {"technique": self.name, "weight": self.weight, "cell": None, "value": cand_tuple}
                else:
                    seen[cand_tuple] = r
        return None


# --- Grader with Step Log ---

def grade_puzzle(grid: PuzzleGrid, techniques):
    max_difficulty = 0
    steps = []
    while not grid.is_solved():
        progress = False
        for tech in techniques:
            result = tech.apply(grid)
            if result:
                max_difficulty = max(max_difficulty, tech.weight)
                steps.append(result)
                progress = True
                break
        if not progress:
            break
    return max_difficulty, steps


if __name__ == "__main__":
    puzzle = [
        [5,3,0, 0,7,0, 0,0,0],
        [6,0,0, 1,9,5, 0,0,0],
        [0,9,8, 0,0,0, 0,6,0],

        [8,0,0, 0,6,0, 0,0,3],
        [4,0,0, 8,0,3, 0,0,1],
        [7,0,0, 0,2,0, 0,0,6],

        [0,6,0, 0,0,0, 2,8,0],
        [0,0,0, 4,1,9, 0,0,5],
        [0,0,0, 0,8,0, 0,7,9],
    ]

    grid = PuzzleGrid()
    grid.grid = puzzle
    initialize_candidates(grid)

    techniques = [NakedSingle(), HiddenSingle(), NakedPair()]
    difficulty, steps = grade_puzzle(grid, techniques)

    print("Puzzle difficulty:", difficulty)
    print("Solving path:")
    for step in steps:
        print(step)
```

---

## 🔎 What’s New
- **Step log**: Each applied technique returns a dictionary with:
  - `technique` → name of the solving method
  - `weight` → difficulty weight
  - `cell` → coordinates of affected cell (or `None` for eliminations like Naked Pair)
  - `value` → value placed or candidates eliminated
- **Grader returns `(difficulty, steps)`** so you can both display the difficulty and show the solving path in your PyQt6 UI.

---

Would you like me to also **format the step log into a human-readable string** (e.g., “Step 1: Naked Single at (0,2) → placed 4”) so you

---

Step log: Each applied technique returns a dictionary with:

technique → name of the solving method

weight → difficulty weight

cell → coordinates of affected cell (or None for eliminations like Naked Pair)

value → value placed or candidates eliminated

Grader returns (difficulty, steps) so you can both display the difficulty and show the solving path in your PyQt6 UI.

Would you like me to also format the step log into a human-readable string (e.g., “Step 1: Naked Single at (0,2) → placed 4”) so you