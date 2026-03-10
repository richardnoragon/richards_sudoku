"""Offline generation of hard/expert 25x25 templates.

Run once: .\\rsudoku\\Scripts\\python.exe _gen_templates.py
Writes _templates_output.json with puzzle+solution pairs.
"""
import time, sys, random, json, threading

sys.setrecursionlimit(10000)

from richards_sudoku.solver.variant_generators import OneToTwentyFiveGenerator
from richards_sudoku.solver.generator import check_unique
from richards_sudoku.solver.solver import _build_peer_cache, _build_region_units
from richards_sudoku.services.variant_registry import REGISTRY
from richards_sudoku.model.types import Variant

meta = REGISTRY[Variant.ONE_TO_25]["factory"](0, "easy")
pc = _build_peer_cache(meta.size, meta.region_layout)
ru = _build_region_units(meta.size, meta.region_layout)

CHECK_TIMEOUT  = 30.0   # skip cells whose uniqueness check exceeds this
ATTEMPT_TIMEOUT = 300.0  # 5 minutes per seed attempt

# Higher targets → easier to reach, so we can generate more templates faster.
# Hard:   305 givens (320 empty) — clearly harder than medium (315 empty)
# Expert: 298 givens (327 empty) — noticeably harder than hard
TARGETS = {"hard": 305, "expert": 298}
NEED = {"hard": 3, "expert": 3}
SEEDS = [99, 0, 1, 2, 42, 3, 7, 11, 5, 15, 20, 25, 33, 50, 77, 8, 17, 4]

output_path = r"c:\Users\richardi\richards_sudoku\_templates_output.json"
# Load prior results so we can resume without regenerating.
try:
    with open(output_path) as f:
        results: dict[str, list[dict]] = json.load(f)
    print(f"Resuming with {len(results.get('hard',[]))} hard / {len(results.get('expert',[]))} expert templates already saved", flush=True)
except FileNotFoundError:
    results = {"hard": [], "expert": []}


def save_results() -> None:
    with open(output_path, "w") as f:
        json.dump(results, f)


def gen_template(diff: str, seed: int) -> dict | None:
    target = TARGETS[diff]
    cancel_flag: list[bool] = [False]
    gen = OneToTwentyFiveGenerator(size=25, seed=seed)
    solution = gen.generate(cancel_flag=cancel_flag)
    if not solution:
        print(f"  [{diff}] seed={seed}: solution generation failed", flush=True)
        return None

    puzzle = [list(row) for row in solution]
    rng = random.Random(seed)
    cells = [(r, c) for r in range(25) for c in range(25)]
    rng.shuffle(cells)

    filled = 625
    checks = 0
    slow_checks = 0
    timeout_skips = 0
    start = time.perf_counter()

    for r, c in cells:
        if filled <= target:
            break
        elapsed = time.perf_counter() - start
        if elapsed > ATTEMPT_TIMEOUT:
            print(f"  [{diff}] seed={seed}: ATTEMPT TIMEOUT {elapsed:.0f}s  givens={filled}", flush=True)
            break

        saved = puzzle[r][c]
        puzzle[r][c] = None
        checks += 1

        pcc: list[bool] = [False]
        timer = threading.Timer(CHECK_TIMEOUT, pcc.__setitem__, args=(0, True))
        timer.start()
        t0 = time.perf_counter()
        try:
            is_unique = check_unique(meta, puzzle, cancel_flag=pcc, peer_cache=pc, region_units=ru)
        finally:
            timer.cancel()
        dt = time.perf_counter() - t0

        if pcc[0]:
            # Check was cancelled by the timer — keep the cell.
            puzzle[r][c] = saved
            timeout_skips += 1
            elapsed_now = time.perf_counter() - start
            print(
                f"  [{diff}] seed={seed}  check {checks}: TIMEOUT(>{CHECK_TIMEOUT:.0f}s)"
                f"  givens={filled}  total={elapsed_now:.0f}s",
                flush=True,
            )
        elif is_unique:
            filled -= 1
            if dt >= 2.0:
                slow_checks += 1
                elapsed_now = time.perf_counter() - start
                print(
                    f"  [{diff}] seed={seed}  check {checks}: {dt:.1f}s (removed)"
                    f"  givens={filled}  total={elapsed_now:.0f}s",
                    flush=True,
                )
        else:
            puzzle[r][c] = saved

    total = time.perf_counter() - start
    print(
        f"[{diff}] seed={seed}: {total:.0f}s  checks={checks}"
        f"  slow={slow_checks}  skipped={timeout_skips}  givens={filled}",
        flush=True,
    )

    return {
        "seed": seed,
        "givens": filled,
        "time": round(total, 1),
        "puzzle": [row[:] for row in puzzle],
        "solution": [row[:] for row in solution],
    }


for diff in ("hard", "expert"):
    print(f"\n{'='*60}", flush=True)
    print(f"Generating {NEED[diff]} templates for {diff} (target={TARGETS[diff]})", flush=True)
    print(f"{'='*60}", flush=True)

    for seed in SEEDS:
        if len(results[diff]) >= NEED[diff]:
            break
        r = gen_template(diff, seed)
        if r:
            results[diff].append(r)
            save_results()  # persist immediately after each template
            print(f"  -> Template {len(results[diff])} stored (givens={r['givens']})", flush=True)

    print(f"\nGot {len(results[diff])} {diff} templates:", flush=True)
    for t in results[diff]:
        print(f"  seed={t['seed']}  givens={t['givens']}  time={t['time']}s", flush=True)

print(f"\nDone. Results in {output_path}", flush=True)
