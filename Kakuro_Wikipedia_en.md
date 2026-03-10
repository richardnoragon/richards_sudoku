---
created: 2026-03-09T00:41:31 (UTC +01:00)
tags: []
source: https://en.wikipedia.org/wiki/Kakuro
author: Contributors to Wikimedia projects
---

# Kakuro - Wikipedia

> ## Excerpt
> From Wikipedia, the free encyclopedia

---
From Wikipedia, the free encyclopedia

Not to be confused with [Kokoro](https://en.wikipedia.org/wiki/Kokoro "Kokoro").

[![](https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Kakuro_black_box.svg/250px-Kakuro_black_box.svg.png)](https://en.wikipedia.org/wiki/File:Kakuro_black_box.svg)

An easy Kakuro puzzle

[![](https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Kakuro_black_box_solution.svg/250px-Kakuro_black_box_solution.svg.png)](https://en.wikipedia.org/wiki/File:Kakuro_black_box_solution.svg)

Solution for the above puzzle

**Kakuro** or **Kakkuro or Kakoro** ([Japanese](https://en.wikipedia.org/wiki/Japanese_language "Japanese language"): カックロ) is a kind of [logic puzzle](https://en.wikipedia.org/wiki/Logic_puzzle "Logic puzzle") that is often referred to as a [mathematical](https://en.wikipedia.org/wiki/Mathematics "Mathematics") [transliteration](https://en.wikipedia.org/wiki/Transliteration "Transliteration") of the [crossword](https://en.wikipedia.org/wiki/Crossword "Crossword"). Kakuro puzzles are regular features in many math-and-logic puzzle publications across the world. In 1966,<sup id="cite_ref-1"><a href="https://en.wikipedia.org/wiki/Kakuro#cite_note-1"><span>[</span>1<span>]</span></a></sup> [Canadian](https://en.wikipedia.org/wiki/Canadians "Canadians") Jacob E. Funk, an employee of [Dell Magazines](https://en.wikipedia.org/wiki/Dell_Magazines "Dell Magazines"), came up with the original English name _Cross Sums_ <sup id="cite_ref-KakuroHistory_2-0"><a href="https://en.wikipedia.org/wiki/Kakuro#cite_note-KakuroHistory-2"><span>[</span>2<span>]</span></a></sup> and other names such as _Cross Addition_ have also been used, but the Japanese name _Kakuro,_ abbreviation of Japanese _kasan kurosu_ (加算クロス, "addition cross"), seems to have gained general acceptance and the puzzles appear to be titled this way now in most publications. The popularity of Kakuro in Japan is immense, second only to [Sudoku](https://en.wikipedia.org/wiki/Sudoku "Sudoku") among [Nikoli](https://en.wikipedia.org/wiki/Nikoli_(publisher) "Nikoli (publisher)")'s famed logic-puzzle offerings.<sup id="cite_ref-KakuroHistory_2-1"><a href="https://en.wikipedia.org/wiki/Kakuro#cite_note-KakuroHistory-2"><span>[</span>2<span>]</span></a></sup>

The canonical Kakuro puzzle is played in a grid of filled and barred cells, "black" and "white" respectively. Puzzles are usually 16×16 in size, although these dimensions can vary widely. Apart from the top row and leftmost column which are entirely black, the grid is divided into "entries"—lines of white cells—by the black cells. The black cells contain a diagonal slash from upper-left to lower-right and a number in one or both halves, such that each horizontal entry has a number in the half-cell to its immediate left and each vertical entry has a number in the half-cell immediately above it. These numbers, borrowing crossword terminology, are commonly called "clues".

The objective of the puzzle is to insert a digit from 1 to 9 inclusive into each white cell so that the sum of the numbers in each entry matches the clue associated with it and that no digit is duplicated in any entry. It is that lack of duplication that makes creating Kakuro puzzles with unique solutions possible. Like Sudoku, solving a Kakuro puzzle involves investigating [combinations](https://en.wikipedia.org/wiki/Combination "Combination") and [permutations](https://en.wikipedia.org/wiki/Permutation "Permutation"). There is an unwritten rule for making Kakuro puzzles that each clue must have at least two numbers that add up to it, since including only one number is mathematically trivial when solving Kakuro puzzles.

At least one publisher<sup id="cite_ref-3"><a href="https://en.wikipedia.org/wiki/Kakuro#cite_note-3"><span>[</span>3<span>]</span></a></sup> includes the constraint that a given combination of numbers can only be used once in each grid, but still markets the puzzles as plain Kakuro.

Some publishers prefer to print their Kakuro grids exactly like crossword grids, with no labeling in the black cells and instead numbering the entries, providing a separate list of the clues akin to a list of crossword clues. (This eliminates the row and column that are entirely black.) This is purely an issue of image and does not affect either the solution nor the logic required for solving.

In discussing Kakuro puzzles and tactics, the typical shorthand for referring to an entry is "(clue, in numerals)-in-(number of cells in entry, spelled out)", such as "16-in-two" and "25-in-five". The exception is what would otherwise be called the "45-in-nine"—simply "45" is used, since the "-in-nine" is mathematically implied (nine cells is the longest possible entry, and since it cannot duplicate a digit it must consist of all the digits from 1 to 9 once). Both "43-in-eight" and "44-in-eight" are still frequently called as such, despite the "-in-eight" suffix being equally implied.

### Combinatoric techniques

\[[edit](https://en.wikipedia.org/w/index.php?title=Kakuro&action=edit&section=2 "Edit section: Combinatoric techniques")\]

Although brute-force guessing is possible, a more efficient approach is the understanding of the various combinatorial forms that entries can take for various pairings of clues and entry lengths. The solution space can be reduced by resolving allowable intersections of horizontal and vertical sums, or by considering necessary or missing values.

Those entries with sufficiently large or small clues for their length will have fewer possible combinations to consider, and by comparing them with entries that cross them, the proper permutation—or part of it—can be derived. The simplest example is where a 3-in-two crosses a 4-in-two: the 3-in-two must consist of "1" and "2" in some order; the 4-in-two (since "2" cannot be duplicated) must consist of "1" and "3" in some order. Therefore, their intersection must be "1", the only digit they have in common.

When solving longer sums there are additional ways to find clues to locating the correct digits. One such method would be to note where a few squares together share possible values thereby eliminating the possibility that other squares in that sum could have those values. For instance, if two 4-in-two clues cross with a longer sum, then the 1 and 3 in the solution must be in those two squares and those digits cannot be used elsewhere in that sum.<sup id="cite_ref-4"><a href="https://en.wikipedia.org/wiki/Kakuro#cite_note-4"><span>[</span>4<span>]</span></a></sup>

When solving sums that have a limited number of solution sets then that can lead to useful clues. For instance, a 30-in-seven sum only has two solution sets: {1,2,3,4,5,6,9} and {1,2,3,4,5,7,8}. If one of the squares in that sum can only take on the values of {8,9} (if the crossing clue is a 17-in-two sum, for example) then that not only becomes an indicator of which solution set fits this sum, it eliminates the possibility of any other digit in the sum being either of those two values, even before determining which of the two values fits in that square.

Another useful approach in more complex puzzles is to identify which square a digit goes in by eliminating other locations within the sum. If all of the crossing clues of a sum have many possible values, but it can be determined that there is only one square that could have a particular value which the sum in question must have, then whatever other possible values the crossing sum would allow, that intersection must be the isolated value. For example, a 36-in-eight sum must contain all digits except 9. If only one of the squares could take on the value of 2 then that must be the answer for that square.

A "box technique" can also be applied on occasion, when the geometry of the unfilled white cells at any given stage of solving lends itself to it: by summing the clues for a series of horizontal entries (subtracting out the values of any digits already added to those entries) and subtracting the clues for a mostly overlapping series of vertical entries, the difference can reveal the value of a partial entry, often a single cell. This technique works because addition is both [associative](https://en.wikipedia.org/wiki/Associative "Associative") and [commutative](https://en.wikipedia.org/wiki/Commutative "Commutative").

It is common practice to mark potential values for cells in the cell corners until all but one have been proven impossible; for particularly challenging puzzles, sometimes entire ranges of values for cells are noted by solvers in the hope of eventually finding sufficient constraints to those ranges from crossing entries to be able to narrow the ranges to single values. Because of space constraints, instead of digits, some solvers use a positional notation, where a potential numerical value is represented by a mark in a particular part of the cell, which makes it easy to place several potential values into a single cell. This also makes it easier to distinguish potential values from solution values.

Some solvers also use [graph paper](https://en.wikipedia.org/wiki/Graph_paper "Graph paper") to try various digit combinations before writing them into the puzzle grids.

As in the Sudoku case, only relatively easy Kakuro puzzles can be solved with the above-mentioned techniques. Harder ones require the use of various types of chain patterns, the same kinds as appear in Sudoku (see _Pattern-Based Constraint Satisfaction and Logic Puzzles_<sup id="cite_ref-Pattern-Based_Constraint_Satisfaction_and_Logic_Puzzles_5-0"><a href="https://en.wikipedia.org/wiki/Kakuro#cite_note-Pattern-Based_Constraint_Satisfaction_and_Logic_Puzzles-5"><span>[</span>5<span>]</span></a></sup>).

## Mathematics of Kakuro

\[[edit](https://en.wikipedia.org/w/index.php?title=Kakuro&action=edit&section=4 "Edit section: Mathematics of Kakuro")\]

Mathematically, Kakuro puzzles can be represented as [integer programming](https://en.wikipedia.org/wiki/Integer_programming "Integer programming") problems, and are [NP-complete](https://en.wikipedia.org/wiki/NP-complete "NP-complete").<sup id="cite_ref-6"><a href="https://en.wikipedia.org/wiki/Kakuro#cite_note-6"><span>[</span>6<span>]</span></a></sup> See also Yato and Seta, 2004.<sup id="cite_ref-7"><a href="https://en.wikipedia.org/wiki/Kakuro#cite_note-7"><span>[</span>7<span>]</span></a></sup>

There are two kinds of mathematical symmetry readily identifiable in Kakuro puzzles: minimum and maximum constraints are duals, as are missing and required values.

All sum combinations can be represented using a bitmapped representation. This representation is useful for determining missing and required values using [bitwise logic operations](https://en.wikipedia.org/wiki/Bitwise_operation "Bitwise operation").

Kakuro puzzles appear in nearly 100 Japanese magazines and newspapers. Kakuro remained the most popular logic puzzle in Japanese printed press until 1992, when Sudoku took the top spot.<sup id="cite_ref-8"><a href="https://en.wikipedia.org/wiki/Kakuro#cite_note-8"><span>[</span>8<span>]</span></a></sup> In the UK, they first appeared in _[The Guardian](https://en.wikipedia.org/wiki/The_Guardian "The Guardian")_, with _[The Telegraph](https://en.wikipedia.org/wiki/The_Daily_Telegraph "The Daily Telegraph")_ and the _[Daily Mail](https://en.wikipedia.org/wiki/Daily_Mail "Daily Mail")_ following.<sup id="cite_ref-9"><a href="https://en.wikipedia.org/wiki/Kakuro#cite_note-9"><span>[</span>9<span>]</span></a></sup>

-   [Killer Sudoku](https://en.wikipedia.org/wiki/Killer_Sudoku "Killer Sudoku"), a variant of Sudoku which is solved using similar techniques.

1.  **[^](https://en.wikipedia.org/wiki/Kakuro#cite_ref-1 "Jump up")** Timmerman, Charles (2006). [_The Everything Kakuro Challenge Book_](https://books.google.com/books?id=A7d5XQaQAJoC). Adams Media. p. ix. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier) "ISBN (identifier)") [9781598690576](https://en.wikipedia.org/wiki/Special:BookSources/9781598690576 "Special:BookSources/9781598690576"). Retrieved November 18, 2018.
2.  ^ [Jump up to: <sup><i><b>a</b></i></sup>](https://en.wikipedia.org/wiki/Kakuro#cite_ref-KakuroHistory_2-0) [<sup><i><b>b</b></i></sup>](https://en.wikipedia.org/wiki/Kakuro#cite_ref-KakuroHistory_2-1) ["Kakuro history"](https://www.conceptispuzzles.com/index.aspx?uri=puzzle/kakuro/history). Retrieved November 18, 2018.
3.  **[^](https://en.wikipedia.org/wiki/Kakuro#cite_ref-3 "Jump up")** ["Sudoku From Denksport"](https://www.denksport.nl/sudoku-info). Keesing Group B.V. Retrieved November 18, 2018.
4.  **[^](https://en.wikipedia.org/wiki/Kakuro#cite_ref-4 "Jump up")** ["Kakuro rules"](https://www.daily-sudoku.com/kakurorules/). Retrieved November 18, 2018.
5.  **[^](https://en.wikipedia.org/wiki/Kakuro#cite_ref-Pattern-Based_Constraint_Satisfaction_and_Logic_Puzzles_5-0 "Jump up")** Berthier, Denis (April 5, 2013). "Pattern-Based Constraint Satisfaction and Logic Puzzles". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier) "ArXiv (identifier)"):[1304.1628](https://arxiv.org/abs/1304.1628) \[[cs.AI](https://arxiv.org/archive/cs.AI)\].
6.  **[^](https://en.wikipedia.org/wiki/Kakuro#cite_ref-6 "Jump up")** Takahiro, Seta (February 5, 2002). ["The complexities of puzzles, cross sum and their another solution problems (ASP)"](https://web.archive.org/web/20221007013910/https://www-imai.is.s.u-tokyo.ac.jp/~seta/paper/senior_thesis/seniorthesis.pdf) (PDF). Archived from [the original](http://www-imai.is.s.u-tokyo.ac.jp/~seta/paper/senior_thesis/seniorthesis.pdf) (PDF) on October 7, 2022. Retrieved November 18, 2018.
7.  **[^](https://en.wikipedia.org/wiki/Kakuro#cite_ref-7 "Jump up")** Yato, Takayuki; Seta, Takahiro (2003). ["Complexity and Completeness of Finding Another Solution and Its Application to Puzzles"](https://search.ieice.org/bin/summary.php?id=e86-a_5_1052). _IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences_. E86-A (5): 1052–1060.
8.  **[^](https://en.wikipedia.org/wiki/Kakuro#cite_ref-8 "Jump up")** ["What is Kakuro"](https://www.kakurolive.com/about-kakuro.php). Retrieved November 18, 2018.
9.  **[^](https://en.wikipedia.org/wiki/Kakuro#cite_ref-9 "Jump up")** ["Kakuro History"](http://www.saidwhat.co.uk/games/kakuro/aboutkakuro.php). Retrieved November 18, 2018.

[![](https://upload.wikimedia.org/wikipedia/en/thumb/4/4a/Commons-logo.svg/40px-Commons-logo.svg.png)](https://en.wikipedia.org/wiki/File:Commons-logo.svg)

Wikimedia Commons has media related to [Kakuro](https://commons.wikimedia.org/wiki/Category:Kakuro "commons:Category:Kakuro").

-   [The New Grid on the Block](https://www.theguardian.com/g2/story/0,,1569223,00.html): _[The Guardian](https://en.wikipedia.org/wiki/The_Guardian "The Guardian")_ newspaper's introduction to Kakuro
-   [IAENG report on Kakuro](http://www.iaeng.org/IJCS/issues_v37/issue_2/IJCS_37_2_01.pdf)
-   [Solve Kakuro puzzles online](https://www.kakurogame.com/)
