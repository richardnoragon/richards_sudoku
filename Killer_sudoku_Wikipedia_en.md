---
created: 2026-03-09T00:31:18 (UTC +01:00)
tags: []
source: https://en.wikipedia.org/wiki/Killer_sudoku
author: Contributors to Wikimedia projects
---

# Killer sudoku - Wikipedia

> ## Excerpt
> Not to be confused with "killer"-level (i.e. very difficult) sudoku.

---
Not to be confused with "killer"-level (i.e. very difficult) [sudoku](https://en.wikipedia.org/wiki/Sudoku "Sudoku").

[![](https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Killersudoku_color.svg/250px-Killersudoku_color.svg.png)](https://en.wikipedia.org/wiki/File:Killersudoku_color.svg)

Example of a Killer Sudoku problem

[![](https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Killersudoku_color_solution.svg/250px-Killersudoku_color_solution.svg.png)](https://en.wikipedia.org/wiki/File:Killersudoku_color_solution.svg)

Solution to the example above

[![](https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Killersudoku_bw.svg/250px-Killersudoku_bw.svg.png)](https://en.wikipedia.org/wiki/File:Killersudoku_bw.svg)

The same example problem, as it would be printed in black and white

**Killer sudoku** (also **killer su doku**, **sumdoku**, **sum doku**, **sumoku**, **addoku**, or **samunanpure** サムナンプレ _sum-num(ber) pla(ce)_) is a [puzzle](https://en.wikipedia.org/wiki/Puzzle "Puzzle") that combines elements of [sudoku](https://en.wikipedia.org/wiki/Sudoku "Sudoku") and [kakuro](https://en.wikipedia.org/wiki/Kakuro "Kakuro"). Despite the name, the simpler killer sudokus can be easier to solve than regular sudokus, depending on the solver's skill at [mental arithmetic](https://en.wikipedia.org/wiki/Mental_arithmetic "Mental arithmetic"); the hardest ones, however, can take hours to solve.

A typical problem is shown on the right, using colors to define the groups of cells. More often, puzzles are printed in black and white, with thin dotted lines used to outline the "cages" (see below for terminology).

Killer sudoku puzzles were already an established variant of sudoku in Japan by the mid-1990s, where they were known as "samunamupure." The name stemmed from a [Nipponised](https://en.wikipedia.org/wiki/Japanese_language "Japanese language") form of the [English](https://en.wikipedia.org/wiki/English_language "English language") words "sum number place." Killer sudokus were introduced to most of the English-speaking world by _[The Times](https://en.wikipedia.org/wiki/The_Times "The Times")_ in 2005.

Traditionally, as with regular sudoku puzzles, the grid layout is symmetrical around a diagonal, horizontal or vertical axis, or a quarter or half turn about the centre. This is a matter of aesthetics, though, rather than obligatory: many Japanese puzzle-makers will make small deviations from perfect symmetry for the sake of improving the puzzle. Other puzzle-makers may produce entirely asymmetrical puzzles.

Cell

A single square that contains one number in the grid

Row

A horizontal line of 9 cells

Column

A vertical line of 9 cells

Nonet

A 3×3 grid of cells, as outlined by the bolder lines in the diagram above; also called a box

Cage

The grouping of cells denoted by a dotted line or by individual colours.

House

Any nonrepeating set of 9 cells: can be used as a general term for "row, column, or nonet" (or, in Killer X variants, "long diagonal")

The objective is to fill the grid with numbers from 1 to 9 in a way that the following conditions are met:

-   Each row, column, and nonet contains each number exactly once.
-   The sum of all numbers in a cage must match the small number printed in its corner.
-   No number appears more than once in a cage. (This is the standard rule for killer sudokus, and implies that no cage can include more than 9 cells.)

In 'Killer X', an additional rule is that each of the long diagonals contains each number once.

## Duplicate cell ambiguity

\[[edit](https://en.wikipedia.org/w/index.php?title=Killer_sudoku&action=edit&section=4 "Edit section: Duplicate cell ambiguity")\]

By convention in Japan, killer sudoku cages do not include duplicate numbers. However, when _[The Times](https://en.wikipedia.org/wiki/The_Times "The Times")_ first introduced the killer sudoku on 31 August 2005, the newspaper did not make this rule explicit. Even though the vast majority of killer sudoku puzzles followed the rule anyway, English-speaking solvers were confused about appropriate solving strategies given the ambiguity. On September 16, 2005, _The Times_ added a new ruling that “Within each dotted-line shape, a digit CAN be repeated if the normal row, column and 3x3 box rules are not broken”. But on September 19 the rule changed to “Within each dotted-line shape, a digit CANNOT be repeated if the normal row, column and 3x3 box rules are not broken” - causing even more confusion. This revised rule stuck and the world standard<sup>[<i><a href="https://en.wikipedia.org/wiki/Wikipedia:Citation_needed" title="Wikipedia:Citation needed"><span title="This claim needs references to reliable sources. (September 2008)">citation needed</span></a></i>]</sup> is no duplicates within cages.

### Fewest possible combinations

\[[edit](https://en.wikipedia.org/w/index.php?title=Killer_sudoku&action=edit&section=6 "Edit section: Fewest possible combinations")\]

Generally the problem is best tackled starting from the extreme sums—cages with the largest or the smallest sums. This is because these have the fewest possible combinations. For example, 5 cells within the same cage totalling 34 can only be 4, 6, 7, 8, and 9. Yet, 5 cells within the same cage totaling 25 has twelve possible combinations.

In the early stages of the game, the most common way to begin filling in numbers is to look at such low-sum or high-sum cages that form a 'straight line'. As the solver can infer from these that certain numbers are in a certain row or column, they can begin 'cross-hatching' across from them.

A further technique can be derived from the knowledge that the numbers in all houses (rows, columns and nonets) add up to 45. By adding up the cages and single numbers in a particular house, the user can deduce the result of a single cell. If the cell calculated is within the house itself, it is referred to as an 'innie'; conversely if the cell is outside it, it is called an 'outie'. Even if this is not possible, advanced players may find it useful to derive the sum of two or three cells, then use other elimination techniques (see below for an example of this). This '45' technique can also be extended to calculate the innies or outies of N adjacent houses, as the difference between the cage-sums and N\*45.

A short-cut to calculating or checking the value of a single 'innie' or 'outie' on a large number of cages is to add up the cages using 'clock' arithmetic (formally, [Modular Arithmetic](https://en.wikipedia.org/wiki/Modular_Arithmetic "Modular Arithmetic") modulo 10), in which all digits other than the last in any number are ignored.

When two numbers are added together, the last digit of the total is not affected by anything other than the last digits of the two original numbers. Adding together a number ending in 7 and a number ending in 8 always results in a number ending in 5, for example. So, for example, 1**7** + 1**8** = 3**5** becomes, in clock arithmetic, 7 + 8 = 5. The biggest number an 'innie' or 'outie' can hold is 9, so adding or subtracting that value will change the last digit of the total in a way that no other value would - allowing the 'innie' or 'outie' to be directly calculated. Clock arithmetic has the advantage that you are only ever dealing with single-digit sums, rather than sums like, say, 58+27 - and even if the concept is initially unfamiliar, it rapidly becomes trivial.

Example: A set of cages form a complete nonet with an 'outie'. The cages have values 8, 1**0**, 1**4**, 7, 1**4**.

-   Using normal arithmetic, those add up to 53. A single nonet totals 45, so the 'outie' must contain an 8.
-   Checking that, using clock arithmetic on those values in turn: 8+0=8; 8+4=2; 2+7=9; 9+4=3. So the clock total is 3, meaning that the actual total also ends in 3 (which we've seen that it does). Any odd number of houses (in this case, 1 nonet) always have an arithmetic total ending in 5 - so, the only 'outie' we could add to change that 5 to a 3 is, again, 8.

Clock arithmetic has the additional bonus that, when the final digits of two cage totals add up to 10 (1**3** and 2**7**, for example), the pair will make no difference to the overall clock total, and can simply be skipped.

Clock arithmetic should at most be used with caution for houses with more than one 'innie' or 'outie', when more than one set of values may result in the same final number, but may still be useful as a quick arithmetic check.

### Consistent numbers within combinations

\[[edit](https://en.wikipedia.org/w/index.php?title=Killer_sudoku&action=edit&section=9 "Edit section: Consistent numbers within combinations")\]

Even though some cages can have multiple combinations of numbers available, there can often be one or more numbers that are consistent within all available solutions. For example: a 4 cell cage totaling 13 has the possible combinations of (1, 2, 3, 7), (1, 2, 4, 6), or (1, 3, 4, 5). Even though, initially, there is no way to tell which combination of numbers is correct, every solution available has a 1 in it. The player then knows for certain that one of the numbers within that cage is 1 (no matter which is the final solution). This can be useful if, for example, they have already deduced another cell within a nonet the cage resides in as having the number 1 as its solution. They then know that the 1 can only reside in cells that are outside of this nonet. If there is only one cell available, it is a 1.

### Initial analysis of the sample problem

\[[edit](https://en.wikipedia.org/w/index.php?title=Killer_sudoku&action=edit&section=10 "Edit section: Initial analysis of the sample problem")\]

[![](https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Killersudoku_color.svg/250px-Killersudoku_color.svg.png)](https://en.wikipedia.org/wiki/File:Killersudoku_color.svg)

The sample problem

#### Fewest possible combinations

\[[edit](https://en.wikipedia.org/w/index.php?title=Killer_sudoku&action=edit&section=11 "Edit section: Fewest possible combinations")\]

The two cells in the top left must be 1+2. The 3 cells to the right totaling 15 cannot therefore have either a 1 or a 2, so they must be either 3+4+8, 3+5+7, or 4+5+6.

The two vertical cells in the top left of the top right nonet cannot be 2+2 as that would mean duplicates, so they must be 1+3. The 1 cannot be in the top line as that conflicts with our first 2 cells therefore the top cell of this pair is 3 and the lower cell 1. This also means the 3 cell cage 15 to the left cannot contain a 3 and so is 4+5+6.

Similarly the neighbouring 16 must be 9+7.

The four cells in the top right cage (totaling 15) can only include one of 1, 3, 7, or 9 (if at all) because of the presence of 1, 3, 7, and 9 in the top right hand nonet. If any one of 1, 3, 7, or 9 is present then this must be the lone square in the nonet below. Therefore, these 4 cells are one of 1+2+4+8 or 2+3+4+6.

The 2 cells in the middle of the left edge must be either 1+5 or 2+4; and so on.

Looking at the nonet on the left hand side in the middle, we can see that there are three cages which do not cross over into another nonet; these add up to 33, meaning that the sum of the remaining two cells must be 12. This does not seem particularly useful, but consider that the cell in the bottom right of the nonet is part of a 3-cage of 6; it can therefore only contain 1, 2 or 3. If it contained 1 or 2, the other cell would have to contain 11 or 10 respectively; this is impossible. It must, therefore, contain 3, and the other cell 9.

With 6-cell, 7-cell or 8-cell cages, correlating the combinations with their 3-cell, 2-cell, or 1-cell [complements](https://en.wikipedia.org/wiki/Complement_(set_theory)#Absolute_complement "Complement (set theory)") usually simplifies things. The table for _6 cell_ cages is the complement of the _3 cell_ table adding up to 45 minus the listed value; similarly, the _7 cell_ table complements the _2 cell_ table. An 8-cell cage is of course missing only one digit (45 minus the sum of the cage).

For example, the complement of a 7-cell cage totalling 41 is a 2-cell cage totalling 4 (because 9–7=2 and 45–41=4). As a 2-cell cage totalling 4 can contain _only_ 1 and 3, we deduce that a 7-cell cage totalling 41 contains _neither_ 1 nor 3.

The following tables list the possible combinations for various sums.

1 cell

```
 1: 1
 2: 2
 3: 3
 4: 4
 5: 5
 6: 6
 7: 7
 8: 8
 9: 9
```

2 cells

```
 3: 12
 4: 13
 5: 14 23
 6: 15 24
 7: 16 25 34
 8: 17 26 35
 9: 18 27 36 45
10: 19 28 37 46
11: 29 38 47 56
12: 39 48 57
13: 49 58 67
14: 59 68 
15: 69 78
16: 79
17: 89
```

3 cells

```
 6: 123
 7: 124
 8: 125 134
 9: 126 135 234
10: 127 136 145 235
11: 128 137 146 236 245
12: 129 138 147 156 237 246 345
13: 139 148 157 238 247 256 346
14: 149 158 167 239 248 257 347 356
15: 159 168 249 258 267 348 357 456
16: 169 178 259 268 349 358 367 457
17: 179 269 278 359 368 458 467
18: 189 279 369 378 459 468 567
19: 289 379 469 478 568
20: 389 479 569 578
21: 489 579 678
22: 589 679
23: 689
24: 789
```

4 cells

```
10: 1234
11: 1235
12: 1236 1245
13: 1237 1246 1345
14: 1238 1247 1256 1346 2345
15: 1239 1248 1257 1347 1356 2346
16: 1249 1258 1267 1348 1357 1456 2347 2356
17: 1259 1268 1349 1358 1367 1457 2348 2357 2456
18: 1269 1278 1359 1368 1458 1467 2349 2358 2367 2457 3456
19: 1279 1369 1378 1459 1468 1567 2359 2368 2458 2467 3457
20: 1289 1379 1469 1478 1568 2369 2378 2459 2468 2567 3458 3467
21: 1389 1479 1569 1578 2379 2469 2478 2568 3459 3468 3567
22: 1489 1579 1678 2389 2479 2569 2578 3469 3478 3568 4567
23: 1589 1679 2489 2579 2678 3479 3569 3578 4568
24: 1689 2589 2679 3489 3579 3678 4569 4578
25: 1789 2689 3589 3679 4579 4678
26: 2789 3689 4589 4679 5678
27: 3789 4689 5679
28: 4789 5689
29: 5789
30: 6789
```

5 cells

```
15: 12345
16: 12346
17: 12347 12356
18: 12348 12357 12456
19: 12349 12358 12367 12457 13456
20: 12359 12368 12458 12467 13457 23456
21: 12369 12378 12459 12468 12567 13458 13467 23457
22: 12379 12469 12478 12568 13459 13468 13567 23458 23467
23: 12389 12479 12569 12578 13469 13478 13568 14567 23459 23468 23567
24: 12489 12579 12678 13479 13569 13578 14568 23469 23478 23568 24567
25: 12589 12679 13489 13579 13678 14569 14578 23479 23569 23578 24568 34567
26: 12689 13589 13679 14579 14678 23489 23579 23678 24569 24578 34568
27: 12789 13689 14589 14679 15678 23589 23679 24579 24678 34569 34578
28: 13789 14689 15679 23689 24589 24679 25678 34579 34678
29: 14789 15689 23789 24689 25679 34589 34679 35678
30: 15789 24789 25689 34689 35679 45678
31: 16789 25789 34789 35689 45679
32: 26789 35789 45689
33: 36789 45789
34: 46789
35: 56789
```

6 cells

```
21: 123456
22: 123457
23: 123458 123467
24: 123459 123468 123567
25: 123469 123478 123568 124567
26: 123479 123569 123578 124568 134567
27: 123489 123579 123678 124569 124578 134568 234567
28: 123589 123679 124579 124678 134569 134578 234568
29: 123689 124589 124679 125678 134579 134678 234569 234578
30: 123789 124689 125679 134589 134679 135678 234579 234678
31: 124789 125689 134689 135679 145678 234589 234679 235678
32: 125789 134789 135689 145679 234689 235679 245678
33: 126789 135789 145689 234789 235689 245679 345678
34: 136789 145789 235789 245689 345679
35: 146789 236789 245789 345689
36: 156789 246789 345789
37: 256789 346789
38: 356789
39: 456789
```

7 cells

```
28: 1234567
29: 1234568
30: 1234569 1234578
31: 1234579 1234678
32: 1234589 1234679 1235678
33: 1234689 1235679 1245678
34: 1234789 1235689 1245679 1345678
35: 1235789 1245689 1345679 2345678
36: 1236789 1245789 1345689 2345679
37: 1246789 1345789 2345689
38: 1256789 1346789 2345789
39: 1356789 2346789
40: 1456789 2356789
41: 2456789
42: 3456789
```

8 cells

```
36: 12345678
37: 12345679
38: 12345689
39: 12345789
40: 12346789
41: 12356789
42: 12456789
43: 13456789
44: 23456789
```

9 cells

```
45: 123456789
```

-   [Kakuro](https://en.wikipedia.org/wiki/Kakuro "Kakuro")
-   [Sudoku](https://en.wikipedia.org/wiki/Sudoku "Sudoku")
-   [KenKen](https://en.wikipedia.org/wiki/KenKen "KenKen")

-   [Too good for Fiendish? Then try Killer Su Doku](https://archive.today/20200226140152/http://www.thetimes.co.uk/tto/life/article1723021.ece) - article in _[The Times](https://en.wikipedia.org/wiki/The_Times "The Times")_
