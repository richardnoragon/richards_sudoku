> Manual acceptance template; no test completion or release approval is implied.
> Application baseline: 0.1.0. Checklist revision 1.0 is a document revision.
> Begin with [PROJECT_STATUS.md](PROJECT_STATUS.md) and record DOC-01 through DOC-10
> as open or resolved with evidence. Release authority remains
> [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md); automated evidence is in [TESTING.md](TESTING.md).

# **📘 Sudoku-inator — FULL‑SYSTEM BETA TEST PACKAGE (PDF EDITION)**

## Alpha alignment

The filename is historical. This is an uncompleted acceptance package, and the
project remains **pre-alpha** under [alpha.md](alpha.md). Use its scenarios as
evidence when executed, add the DOC-09 handoff, and meet all Alpha criteria before
claiming Beta ordinary-user reliability.
### *Checklist revision 1.0 — Full-system acceptance*
### *Includes Casual + Technical Tester Tracks (Two‑Column Layout)*

---

# **COVER PAGE**

---

<div style="text-align:center; font-size: 28px; font-weight: bold; margin-top: 80px;">
Sudoku-inator
FULL‑SYSTEM BETA TEST PACKAGE  
</div>

<div style="text-align:center; font-size: 18px; margin-top: 20px;">
Checklist revision 1.0 — application baseline 0.1.0
</div>

<div style="text-align:center; font-size: 16px; margin-top: 40px;">
Generator • Solver • Difficulty Engine • UI/UX • Persistence • Variants • Performance  
</div>

<div style="text-align:center; font-size: 14px; margin-top: 120px;">
Prepared for Beta Testers  
<br>  
Sudoku-inator Project
</div>

<div style="text-align:center; font-size: 12px; margin-top: 80px;">
© 2026 Richard — All Rights Reserved  
</div>

---

# **TABLE OF CONTENTS**

1. **Tester Information**  
2. **Pre‑Test Setup**  
3. **Core Functional Testing**  
   - 3.1 Generator  
   - 3.2 Solver  
4. **User Interface & UX**  
   - 4.1 Layout & Controls  
   - 4.2 Visual Consistency  
   - 4.3 Accessibility  
5. **Persistence & Serialization**  
6. **Difficulty Engine (SE Techniques)**  
7. **Variant Testing**  
8. **Performance & Stability**  
9. **Error Handling & Resilience**  
10. **Governance Alignment (CLEAR)**  
11. **Bug Report Form**  
12. **Beta Exit Criteria**  

---

# **TWO‑COLUMN LAYOUT (CASUAL vs TECHNICAL)**  
### *All sections combined into a single unified layout*

---

# **1. TESTER INFORMATION**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| Name: ____________ | Name: ____________ |
| Device: __________ | Device/Specs: __________________ |
| OS: ______________ | OS + Kernel/Build: ______________ |
| Screen Size: ______ | Resolution + DPI: ______________ |
| Build Version: ____ | Build Hash / Commit: ___________ |

---

# **2. PRE‑TEST SETUP**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ Installed the beta | □ Installed clean build (no cached assets) |
| □ No old saves | □ Verified no legacy save artifacts |
| □ Logging on (if easy) | □ Logging enabled + log path confirmed |
| □ Internet off | □ Network isolation validated |
| □ Device ready | □ Hardware specs recorded |

---

# **3. CORE FUNCTIONAL TESTING**

## **3.1 Generator**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ Puzzles feel fair | □ 20 puzzles per difficulty generated |
| □ Difficulty feels right | □ All puzzles have exactly one solution |
| □ No puzzle feels impossible | □ No invalid givens or contradictions |
| □ Variety feels good | □ No repeated patterns across tiers |
| □ Generation feels fast | □ Generation time < 500 ms |

---

## **3.2 Solver**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ Solver works | □ Solve 20 known puzzles → verify correctness |
| □ Solver never cheats | □ Solver respects variant constraints |
| □ Explanations make sense | □ Solver rejects malformed puzzles |
| □ No crashes | □ Solve time < 200 ms |

---

# **4. USER INTERFACE & UX**

## **4.1 Layout & Controls**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ Grid readable | □ UI scales without distortion |
| □ Input intuitive | □ Keyboard navigation validated |
| □ Undo/redo works | □ Undo/redo stack integrity verified |
| □ Pencil marks clear | □ Pencil mark logic deterministic |
| □ Highlighting helpful | □ Hit‑testing accurate |

---

## **4.2 Visual Consistency**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ Colors pleasant | □ Fonts, spacing, alignment consistent |
| □ Dark mode readable | □ No flicker or redraw artifacts |
| □ Errors clear | □ Animations within frame budget |

---

## **4.3 Accessibility**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ High contrast helps | □ Screen reader labels validated |
| □ Colorblind safe | □ Keyboard‑only playthrough possible |
| □ Easy to see | □ Focus order correct |

---

# **5. PERSISTENCE & SERIALIZATION**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ Save/load works | □ Save → quit → reload → identical state |
| □ No confusion | □ Multi‑slot save integrity validated |
| □ No lost progress | □ Corrupt save → safe error |
| | □ Version metadata correct |
| | □ Backward compatibility validated |

---

# **6. DIFFICULTY ENGINE (SE TECHNIQUES)**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ Difficulty feels right | □ Technique detection correct |
| □ Hard puzzles feel hard | □ No Easy puzzle requires advanced techniques |
| □ Hints make sense | □ Difficulty grading consistent across samples |

---

# **7. VARIANT TESTING**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ Rules easy to understand | □ Jigsaw: region shapes validated |
| □ Visuals clear | □ Killer: cage sums correct |
| □ No confusion | □ Str8ts: run logic enforced |
| | □ Large grids: performance acceptable |

---

# **8. PERFORMANCE & STABILITY**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ App feels smooth | □ Startup < 3 seconds |
| □ No lag | □ No frame drops |
| □ No freezes | □ 100× generate → no memory leak |
| | □ 100× solve → stable |
| | □ Resize stress test passes |

---

# **9. ERROR HANDLING & RESILIENCE**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ Errors understandable | □ All invalid states handled safely |
| □ No crashes | □ No silent failures |
| □ No lost progress | □ Generator retries correct |
| | □ Save corruption isolated |

---

# **10. GOVERNANCE ALIGNMENT (CLEAR)**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ App feels consistent | □ Naming conventions consistent |
| □ App feels predictable | □ UI patterns consistent |
| □ App feels stable | □ All actions explicit & reversible |
| | □ Logs capture major events |

---

# **11. BUG REPORT FORM**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| Simple form | Full reproducibility form |
| Title | Title |
| Steps | Steps (precise) |
| Expected | Expected |
| Actual | Actual |
| Severity | Severity (S1–S5) |
| Screenshot | Screenshot + logs + save file |

---

# **12. BETA EXIT CRITERIA**

| **Casual Tester** | **Technical Tester** |
|-------------------|----------------------|
| □ No major issues | □ No S1/S2 bugs |
| □ Game feels stable | □ ≤ 5 S3 bugs |
| □ Puzzles feel good | □ ≤ 10 S4 bugs |
| □ UI feels good | □ Performance budgets met |
| | □ Difficulty engine validated |
| | □ Save/load stable |

---
