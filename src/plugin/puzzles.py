from __future__ import annotations

import re
from pathlib import Path

from contract import CellOptions, GridInput, GridReportOutput, PuzzleInput, PuzzleOutput

# Fixed puzzles, 81 cells row by row (. empty), generated once from seeded full grids by removing clues
# while the solution stayed unique: 40, 32, 27 and 25 clues. sudoku-05 is sudoku-02 with one given
# changed so that no row, column or box repeats a digit, yet the puzzle has no solution.
PUZZLES = {
    "sudoku-01": ".79.6.5.8.6..917.2....5.......4.6.21.8.9.3....24.159.65....7683..75.219.418.39..7",
    "sudoku-02": "7..8..4...92..65..1.4735..92.5........95.38.738........37.....6..86.71..4.6..9...",
    "sudoku-03": "4.2.13.786.7.....3.3...72.........9..4.72.81.....64.5..7.59..3..8.............1..",
    "sudoku-04": "...8536.....4.......17...3..9..3..7..4..6...5.5.27.1..........8..6...3594.....7..",
    "sudoku-05": "5..8..4...92..65..1.4735..92.5........95.38.738........37.....6..86.71..4.6..9...",
}
ROW = re.compile(r"^[1-9.]{9}$")


def _rows(puzzle_id: str) -> list[str]:
    if puzzle_id not in PUZZLES:
        raise ValueError(f"unknown puzzle {puzzle_id!r}: the puzzles are {', '.join(PUZZLES)}")
    text = PUZZLES[puzzle_id]
    return [text[i : i + 9] for i in range(0, 81, 9)]


def get_puzzle(given: PuzzleInput, workspace: Path) -> PuzzleOutput:
    rows = _rows(given.puzzle_id)
    return PuzzleOutput(puzzle_id=given.puzzle_id, rows=rows, givens=sum(char != "." for row in rows for char in row))


def puzzle_record(given: PuzzleInput, workspace: Path) -> PuzzleOutput:
    return get_puzzle(given, workspace)


def units(rows: list[str]) -> list[tuple[str, list[str]]]:
    """Each row, column and 3x3 box with its name, e.g. ("box 4", [...nine cells])."""
    named = [(f"row {r}", list(rows[r])) for r in range(9)]
    named += [(f"column {c}", [rows[r][c] for r in range(9)]) for c in range(9)]
    named += [
        (f"box {b}", [rows[3 * (b // 3) + i][3 * (b % 3) + j] for i in range(3) for j in range(3)]) for b in range(9)
    ]
    return named


def analyze_grid(given: GridInput, workspace: Path) -> GridReportOutput:
    rows = given.rows
    if len(rows) != 9 or any(not ROW.fullmatch(row) for row in rows):
        raise ValueError("rows must be 9 rows of 9 characters, each a digit 1 to 9 or .")
    conflicts = [
        f"{name} repeats {digit}" for name, cells in units(rows) for digit in "123456789" if cells.count(digit) > 1
    ]
    empty = []
    for r in range(9):
        for c in range(9):
            if rows[r][c] != ".":
                continue
            box = [rows[3 * (r // 3) + i][3 * (c // 3) + j] for i in range(3) for j in range(3)]
            used = set(rows[r]) | {rows[i][c] for i in range(9)} | set(box)
            empty.append(CellOptions(row=r, col=c, options="".join(d for d in "123456789" if d not in used)))
    return GridReportOutput(empty_cells=empty, conflicts=conflicts, filled=81 - len(empty))
