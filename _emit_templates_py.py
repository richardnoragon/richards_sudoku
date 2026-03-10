"""Convert _templates_output.json -> src/richards_sudoku/solver/one_to_25_templates.py"""
import json, textwrap, pathlib

data = json.load(open("_templates_output.json"))
lines = []

lines.append('"""Pre-generated 25x25 puzzle templates for hard/expert difficulty.')
lines.append('')
lines.append('Each template is a (puzzle, solution) pair where puzzle contains int|None.')
lines.append('Generated offline by _gen_templates.py; transforms applied at runtime')
lines.append('via _apply_transform() in new_game_dialog.py so every game looks unique.')
lines.append('"""')
lines.append('from __future__ import annotations')
lines.append('')
lines.append('# fmt: off')
lines.append('_TEMPLATES: dict[str, list[tuple[list, list]]] = {')

for diff in ('hard', 'expert'):
    templates = data[diff]
    lines.append(f'    {diff!r}: [')
    for t in templates:
        puzzle = t['puzzle']
        solution = t['solution']
        givens = t['givens']
        lines.append(f'        # seed={t["seed"]}  givens={givens}  time={t["time"]}s')
        lines.append('        (')
        lines.append('            [  # puzzle')
        for row in puzzle:
            row_str = ', '.join('None' if v is None else str(v) for v in row)
            lines.append(f'                [{row_str}],')
        lines.append('            ],')
        lines.append('            [  # solution')
        for row in solution:
            row_str = ', '.join(str(v) for v in row)
            lines.append(f'                [{row_str}],')
        lines.append('            ],')
        lines.append('        ),')
    lines.append('    ],')

lines.append('}')
lines.append('# fmt: on')
lines.append('')

out = pathlib.Path(r"src\richards_sudoku\solver\one_to_25_templates.py")
out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f"Written to {out}  ({out.stat().st_size//1024} KB)")
