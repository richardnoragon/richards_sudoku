# solver.py

Prompt:
can you help me code a solver for my Sudoku applicatin. The application (python, pygame, pyqt6) up and running (sudoku, jigsaw, str8ts and killer sudoku ). i would like to expand the applications capabilities. the solver must be able to use the following techniques:
Naked Singles and Hidden Singles
Direct Pointing, Claiming and Hidden Pairs
Naked and Hidden Pairs, Triplets and Quads
Locking, Claiming (intersections), X-Wing, Swordfish and Jellyfish
XY-Wing and XYZ-Wing
Unique Rectangles and Loops
Bivalue Universal Grave
Aligned Pair Exclusion
Bidirectional Cycles
Nishio
Forcing Chains

Reply:
Perfect timing, Richard — this is exactly the kind of architectural challenge you thrive on. Expanding your Sudoku application with a solver that handles advanced techniques means building a layered inference engine rather than a brute-force backtracker. Let’s break it down into a modular design that aligns with your governance-driven style:

---

## 🔑 Architectural Strategy
### Core Abstractions

Grid Model: Class-based API with cell candidates, peer sets, and region membership.

Technique Registry: Each solving technique implemented as a strategy object with:

name

applicable(grid) → bool

apply(grid) → transformation (eliminations, placements, contradictions)

Pipeline: Iteratively apply techniques until no progress, then escalate to more complex ones.

### Transparency & Governance

Each technique logs:

Rule applied

Cells affected

Candidates removed/placed

JSON-driven step-tracking for reproducibility and UI feedback.

## 🧩 Implementation Outline
Here’s a skeleton you can expand:

---
class SudokuGrid:
    def __init__(self, initial_values):
        self.cells = [[Cell(r, c, initial_values[r][c]) for c in range(9)] for r in range(9)]
        self.log = []

    def peers(self, r, c):
        # Return row, column, and box peers
        pass

    def record_step(self, technique, details):
        self.log.append({"technique": technique, "details": details})


class Technique:
    def __init__(self, name):
        self.name = name

    def applicable(self, grid):
        raise NotImplementedError

    def apply(self, grid):
        raise NotImplementedError


class NakedSingle(Technique):
    def __init__(self):
        super().__init__("Naked Single")

    def applicable(self, grid):
        return any(len(cell.candidates) == 1 for row in grid.cells for cell in row)

    def apply(self, grid):
        for row in grid.cells:
            for cell in row:
                if len(cell.candidates) == 1 and not cell.value:
                    cell.value = cell.candidates.pop()
                    grid.record_step(self.name, {"cell": (cell.r, cell.c), "value": cell.value})
                    return True
        return False


def solver(grid, techniques):
    progress = True
    while progress:
        progress = False
        for tech in techniques:
            if tech.applicable(grid):
                if tech.apply(grid):
                    progress = True
                    break

---

## 🛠️ Technique Roadmap

You’ll want to implement progressively:

Singles: Naked & Hidden.

Pairs/Triplets/Quads: Naked, Hidden, Pointing, Claiming.

Fish Patterns: X-Wing, Swordfish, Jellyfish.

Wings: XY-Wing, XYZ-Wing.

Deadly Patterns: Unique Rectangles, BUG (Bivalue Universal Grave).

Advanced Chains: Aligned Pair Exclusion, Bidirectional Cycles, Nishio, Forcing Chains.

## 🎯 Next Steps
Start with a registry of techniques (like the NakedSingle example).

Integrate logging into your PyQt6 UI for transparency.

Bundle test puzzles tagged by required technique (onboarding strategy).

Design JSON schema for solver steps so you can replay or audit solutions.

---

Would you like me to sketch out one of the more advanced techniques (say, X-Wing or XY-Wing) in code form so you can see how the pattern-detection logic fits into this modular pipeline?

---
Prompt:
could you please show me what the code for  XY-Wing and XYZ-Wing looks like
Answer:
Great choice — XY-Wing and XYZ-Wing are elegant techniques that fit beautifully into a modular solver. Let me show you how to structure them in Python so they plug into your technique registry.

---

## 🧩 XY-Wing
### Concept:

Three cells (pivot + two wings).

Pivot has candidates {X, Y}.

Wing1 has {X, Z}, Wing2 has {Y, Z}.

If all three see each other appropriately (pivot sees both wings, wings share a common peer set), candidate Z can be eliminated from any cell that sees both wings.

### Implementation Sketch:

class XYWing(Technique):
    def __init__(self):
        super().__init__("XY-Wing")

    def applicable(self, grid):
        # Look for pivot cells with exactly two candidates
        return any(len(cell.candidates) == 2 for row in grid.cells for cell in row)

    def apply(self, grid):
        for row in grid.cells:
            for pivot in row:
                if len(pivot.candidates) == 2:
                    x, y = list(pivot.candidates)
                    # Find wings
                    for wing1 in grid.peers(pivot.r, pivot.c):
                        if len(wing1.candidates) == 2 and x in wing1.candidates:
                            z = (wing1.candidates - {x}).pop()
                            for wing2 in grid.peers(pivot.r, pivot.c):
                                if wing2 != wing1 and len(wing2.candidates) == 2 and y in wing2.candidates:
                                    z2 = (wing2.candidates - {y}).pop()
                                    if z == z2:
                                        # Eliminate Z from common peers
                                        common_peers = set(grid.peers(wing1.r, wing1.c)) & set(grid.peers(wing2.r, wing2.c))
                                        changed = False
                                        for cp in common_peers:
                                            if z in cp.candidates:
                                                cp.candidates.remove(z)
                                                grid.record_step(self.name, {
                                                    "pivot": (pivot.r, pivot.c),
                                                    "wings": [(wing1.r, wing1.c), (wing2.r, wing2.c)],
                                                    "eliminated": z,
                                                    "target": (cp.r, cp.c)
                                                })
                                                changed = True
                                        if changed:
                                            return True
        return False

---

## 🧩 XYZ-Wing
### Concept:

Three cells again: pivot with {X, Y, Z}, wings with {X, Y} and {Y, Z}.

If pivot sees both wings, candidate Z can be eliminated from any cell that sees all three.

### Implementation Sketch:

class XYZWing(Technique):
    def __init__(self):
        super().__init__("XYZ-Wing")

    def applicable(self, grid):
        return any(len(cell.candidates) == 3 for row in grid.cells for cell in row)

    def apply(self, grid):
        for row in grid.cells:
            for pivot in row:
                if len(pivot.candidates) == 3:
                    x, y, z = list(pivot.candidates)
                    # Find wings
                    for wing1 in grid.peers(pivot.r, pivot.c):
                        if wing1.candidates == {x, y}:
                            for wing2 in grid.peers(pivot.r, pivot.c):
                                if wing2 != wing1 and wing2.candidates == {y, z}:
                                    # Eliminate Z from common peers
                                    common_peers = set(grid.peers(pivot.r, pivot.c)) & set(grid.peers(wing1.r, wing1.c)) & set(grid.peers(wing2.r, wing2.c))
                                    changed = False
                                    for cp in common_peers:
                                        if z in cp.candidates:
                                            cp.candidates.remove(z)
                                            grid.record_step(self.name, {
                                                "pivot": (pivot.r, pivot.c),
                                                "wings": [(wing1.r, wing1.c), (wing2.r, wing2.c)],
                                                "eliminated": z,
                                                "target": (cp.r, cp.c)
                                            })
                                            changed = True
                                    if changed:
                                        return True
        return False

---

## 🔗 Integration
Add these classes to your technique registry:

---

techniques = [
    NakedSingle(),
    HiddenSingle(),
    XYWing(),
    XYZWing(),
    # ... other techniques
]
---

Prompt:
could you please show me what the code for  XY-Wing and XYZ-Wing looks like
Reply:
Great choice — XY-Wing and XYZ-Wing are elegant techniques that fit beautifully into a modular solver. Let me show you how to structure them in Python so they plug into your technique registry.

---

## 🧩 XY-Wing

**Concept**:  
- Three cells (pivot + two wings).  
- Pivot has candidates {X, Y}.  
- Wing1 has {X, Z}, Wing2 has {Y, Z}.  
- If all three see each other appropriately (pivot sees both wings, wings share a common peer set), candidate Z can be eliminated from any cell that sees both wings.

**Implementation Sketch**:

```python
class XYWing(Technique):
    def __init__(self):
        super().__init__("XY-Wing")

    def applicable(self, grid):
        # Look for pivot cells with exactly two candidates
        return any(len(cell.candidates) == 2 for row in grid.cells for cell in row)

    def apply(self, grid):
        for row in grid.cells:
            for pivot in row:
                if len(pivot.candidates) == 2:
                    x, y = list(pivot.candidates)
                    # Find wings
                    for wing1 in grid.peers(pivot.r, pivot.c):
                        if len(wing1.candidates) == 2 and x in wing1.candidates:
                            z = (wing1.candidates - {x}).pop()
                            for wing2 in grid.peers(pivot.r, pivot.c):
                                if wing2 != wing1 and len(wing2.candidates) == 2 and y in wing2.candidates:
                                    z2 = (wing2.candidates - {y}).pop()
                                    if z == z2:
                                        # Eliminate Z from common peers
                                        common_peers = set(grid.peers(wing1.r, wing1.c)) & set(grid.peers(wing2.r, wing2.c))
                                        changed = False
                                        for cp in common_peers:
                                            if z in cp.candidates:
                                                cp.candidates.remove(z)
                                                grid.record_step(self.name, {
                                                    "pivot": (pivot.r, pivot.c),
                                                    "wings": [(wing1.r, wing1.c), (wing2.r, wing2.c)],
                                                    "eliminated": z,
                                                    "target": (cp.r, cp.c)
                                                })
                                                changed = True
                                        if changed:
                                            return True
        return False
```

---

## 🧩 XYZ-Wing

**Concept**:  
- Three cells again: pivot with {X, Y, Z}, wings with {X, Y} and {Y, Z}.  
- If pivot sees both wings, candidate Z can be eliminated from any cell that sees all three.

**Implementation Sketch**:

```python
class XYZWing(Technique):
    def __init__(self):
        super().__init__("XYZ-Wing")

    def applicable(self, grid):
        return any(len(cell.candidates) == 3 for row in grid.cells for cell in row)

    def apply(self, grid):
        for row in grid.cells:
            for pivot in row:
                if len(pivot.candidates) == 3:
                    x, y, z = list(pivot.candidates)
                    # Find wings
                    for wing1 in grid.peers(pivot.r, pivot.c):
                        if wing1.candidates == {x, y}:
                            for wing2 in grid.peers(pivot.r, pivot.c):
                                if wing2 != wing1 and wing2.candidates == {y, z}:
                                    # Eliminate Z from common peers
                                    common_peers = set(grid.peers(pivot.r, pivot.c)) & set(grid.peers(wing1.r, wing1.c)) & set(grid.peers(wing2.r, wing2.c))
                                    changed = False
                                    for cp in common_peers:
                                        if z in cp.candidates:
                                            cp.candidates.remove(z)
                                            grid.record_step(self.name, {
                                                "pivot": (pivot.r, pivot.c),
                                                "wings": [(wing1.r, wing1.c), (wing2.r, wing2.c)],
                                                "eliminated": z,
                                                "target": (cp.r, cp.c)
                                            })
                                            changed = True
                                    if changed:
                                        return True
        return False
```

---

## 🔗 Integration

Add these classes to your technique registry:

```python
techniques = [
    NakedSingle(),
    HiddenSingle(),
    XYWing(),
    XYZWing(),
    # ... other techniques
]
```

---

## 🎯 Next Step

These sketches give you the **pattern-detection logic**. You’ll want to:
- Refine `grid.peers()` to return proper peer sets (row, column, box).
- Ensure candidate sets are maintained consistently.
- Add **step-tracking logs** so your PyQt6 UI can show “XY-Wing applied: eliminated 7 from r4c6”.

Would you like me to also show how to **unit test these techniques** with sample puzzles so you can validate correctness before wiring them into your full solver pipeline?
