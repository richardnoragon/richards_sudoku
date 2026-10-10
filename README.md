# Sudoku-inator

A Python + PyQt6 desktop puzzle app with eight registered variants, local saves,
pencil marks, hints, undo/redo, and SE-style difficulty grading.
Formerly known as Richards Sudoku (`richards_sudoku`). The distribution and command
are `sudoku-inator`; the Python package is `sudoku_inator`. See [the rebranding record](REBRANDING.md).

## Current status

Application version: **0.1.0**. Development stage: **pre-alpha; Alpha criteria remain open**.
[alpha.md](alpha.md) defines the developer handoff and end-to-end workflow standard.
Core and extended-variant foundations are implemented.
The workflow fixes have regression coverage; independent handoff and manual
release validation remain open. See
[project status](PROJECT_STATUS.md) for verified behavior and known gaps.

| Variant | Board size |
| --- | --- |
| Standard, Jigsaw, Str8ts, Killer, Codewords, Kakuro | 9×9 |
| KenKen | 4×4, 6×6, 9×9 |
| 1–25 | 25×25; use F4 / Enter Value for values 10–25 |

## Install and run

Requires Python 3.13+ and a desktop environment. PyQt6 >=6.10 is installed as a dependency.

Clone the repository and enter its directory:

```bash
git clone https://github.com/richardnoragon/sudoku-inator.git
cd sudoku-inator
```

Create a virtual environment:

```bash
python -m venv .venv
```

If your Linux Python reports that `ensurepip` is unavailable, install the matching
Python venv package supplied by your distribution, then repeat this command.

Activate with `source .venv/bin/activate` on Linux/macOS, or
`.venv\Scripts\Activate.ps1` in Windows PowerShell. Then run:

```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
sudoku-inator
```

Use `sudoku-inator`; the former command was retired in the full rebrand.
For play without developer tools, install with `python -m pip install -e .`.

## Docker testing

The Dockerfile packages the checked-out source (currently version 0.1.0).
There is no tagged stable release yet, and release validation remains open.
It uses the Python 3.13 line used by CI; `--pull` refreshes its base image.

```bash
docker build --pull -t sudoku-inator:local .
```

### Desktop play on Linux

Requires a local X11 session, or Wayland with XWayland, and a valid Xauthority
file. Run from a terminal in your desktop session:

```bash
mkdir -p docker-saves
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
test -f "$XAUTHORITY" && docker run --rm --init \
  --user "$(id -u):$(id -g)" \
  --hostname "$(hostname)" \
  -e DISPLAY -e XAUTHORITY=/tmp/host.xauth -e HOME=/tmp \
  -e QT_QPA_PLATFORM=xcb -e QT_X11_NO_MITSHM=1 \
  --mount type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix,readonly \
  --mount "type=bind,src=$XAUTHORITY,dst=/tmp/host.xauth,readonly" \
  --mount "type=bind,src=$PWD/docker-saves,dst=/data" \
  sudoku-inator:local
```

Save games under `/data` in the file dialog to keep them in `docker-saves`
after the container closes. If the command does not start because the
Xauthority file is missing, set `XAUTHORITY` to your desktop session's cookie
file. Native desktop forwarding with these commands is Linux-only.

### Automated tests

The separate test target runs without a display server and includes the
development dependencies and test suite:

```bash
docker build --pull --target test -t sudoku-inator:test .
docker run --rm --init sudoku-inator:test
```

Rebuild after source changes. Neither target mounts your source tree.

## Playing

Use **File → New Game** to choose a variant, difficulty, and hint allowance.
Click a cell, enter digits (or **F4** for any value up to 25), and use **P** for
pencil mode or **H** for the selected hint mode.
Use **File → Save** and **File → Open** to save and resume JSON games.
See the [user guide](USER_GUIDE.md) for controls and current limitations.

## Development checks

```bash
python -m ruff check src
python -m mypy
```

On Linux/macOS:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q
```

See [TESTING.md](TESTING.md) for PowerShell commands, current results, and CI scope.

## Documentation

- [Documentation index and authority](DOCUMENTATION.md)
- [Architecture](ARCHITECTURE.md) and [decisions](DECISIONS.md)
- [Requirements](prd.md) and [UX direction](UX_DESIGN_SPEC.md)
- [Roadmap](ROADMAP.md), [implementation issues](IMPLEMENTATION_ISSUES.md), and [tasks](speckit.tasks)
- [Contributing](CONTRIBUTING.md), [release process](RELEASE_PROCESS.md), and [release checklist](RELEASE_CHECKLIST.md)
- [Changelog](CHANGELOG.md), [save migrations](MIGRATIONS.md), and [security policy](SECURITY.md)
