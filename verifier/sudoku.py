"""Checks for each tool's calls and for the solve-sudoku submission, against the pinned puzzle."""

import re

from .checks import gave_up_verdict, result

PUZZLE_ID = re.compile(r"^sudoku-\d{2}$")
ROW = re.compile(r"^[1-9.]{9}$")
FULL_ROW = re.compile(r"^[1-9]{9}$")
DIGITS = "123456789"


def grid_problem(rows, full):
    pattern = FULL_ROW if full else ROW
    if len(rows) != 9 or any(not pattern.fullmatch(row) for row in rows):
        kind = "digits 1 to 9" if full else "digits 1 to 9 or ."
        return f"the grid must be 9 rows of 9 {kind}"
    return None


def units(rows):
    named = [(f"row {r}", list(rows[r])) for r in range(9)]
    named += [(f"column {c}", [rows[r][c] for r in range(9)]) for c in range(9)]
    named += [
        (f"box {b}", [rows[3 * (b // 3) + i][3 * (b % 3) + j] for i in range(3) for j in range(3)]) for b in range(9)
    ]
    return named


def repeats(rows):
    return [f"{name} repeats {d}" for name, cells in units(rows) for d in DIGITS if cells.count(d) > 1]


def options(cells, i):
    r, c = divmod(i, 9)
    used = set(cells[r * 9 : r * 9 + 9]) | set(cells[c::9])
    br, bc = 3 * (r // 3), 3 * (c // 3)
    used |= {cells[(br + a) * 9 + bc + b] for a in range(3) for b in range(3)}
    return [d for d in DIGITS if d not in used]


def solve(cells):
    """One solution of the puzzle (a list of 81 cells) by backtracking on the fewest options, or None."""
    best, best_options = None, None
    for i in range(81):
        if cells[i] == ".":
            found = options(cells, i)
            if best is None or len(found) < len(best_options):
                best, best_options = i, found
                if not found:
                    return None
    if best is None:
        return list(cells)
    for digit in best_options:
        cells[best] = digit
        solved = solve(cells)
        if solved is not None:
            cells[best] = "."
            return solved
    cells[best] = "."
    return None


def _puzzle_input(value):
    if not PUZZLE_ID.fullmatch(value.puzzle_id):
        return result(False, f"puzzle_id {value.puzzle_id!r} is not of the form sudoku-NN")
    return result(True, "input is valid")


class GetPuzzle:
    verify_input = staticmethod(_puzzle_input)

    @staticmethod
    def verify_output(input_value, output_value, workspace):
        if output_value.puzzle_id != input_value.puzzle_id:
            return result(False, "the puzzle is for a different id")
        problem = grid_problem(output_value.rows, full=False)
        if problem:
            return result(False, problem)
        if output_value.givens != sum(char != "." for row in output_value.rows for char in row):
            return result(False, "givens does not match the filled cells")
        return result(True, "puzzle returned")


class AnalyzeGrid:
    @staticmethod
    def verify_input(value):
        problem = grid_problem(value.rows, full=False)
        return result(False, problem) if problem else result(True, "input is valid")

    @staticmethod
    def verify_output(input_value, output_value, workspace):
        rows = input_value.rows
        cells = list("".join(rows))
        empty = [i for i in range(81) if cells[i] == "."]
        expected = [(i // 9, i % 9, "".join(options(cells, i))) for i in empty]
        given = [(cell.row, cell.col, cell.options) for cell in output_value.empty_cells]
        if given != expected or output_value.filled != 81 - len(empty):
            return result(False, "the empty cells or their options do not match the grid")
        if output_value.conflicts != repeats(rows):
            return result(False, "the conflicts do not match the grid")
        return result(True, "grid report matches the grid")


def verify_get_puzzle(arguments, output, reference, workspace):
    return GetPuzzle.verify_output(arguments, output, workspace)


def _judge(arguments, output, reference, workspace):
    """A solved grid is valid when it keeps every given and no unit repeats a digit; for a puzzle the
    verifier's own solver finds no solution for, only solvable false with an empty grid is valid."""
    if reference is None or grid_problem(reference.rows, full=False):
        return result(False, "no usable puzzle was pinned, so the submission cannot be judged")
    puzzle = list("".join(reference.rows))
    truth = solve(list(puzzle))
    empty = [i for i in range(81) if puzzle[i] == "."]
    details = {"puzzle_has_solution": truth is not None, "empty_cells": len(empty)}
    if not output.solvable:
        if output.solution:
            return result(False, "an unsolvable claim must leave solution empty", score=0.0, **details)
        if truth is not None:
            return result(False, "the puzzle has a solution, but solvable is false", score=0.0, **details)
        return result(True, "correct: the puzzle has no solution", **details)
    if truth is None:
        return result(False, "the puzzle has no solution, but solvable is true", score=0.0, **details)
    problem = grid_problem(output.solution, full=True)
    if problem:
        return result(False, f"malformed solution: {problem}", score=0.0, **details)
    cells = list("".join(output.solution))
    right = sum(1 for i in empty if cells[i] == truth[i])
    score = round(right / len(empty), 4) if empty else 1.0
    changed = [i for i in range(81) if puzzle[i] != "." and cells[i] != puzzle[i]]
    if changed:
        r, c = divmod(changed[0], 9)
        return result(False, f"the given at row {r}, column {c} was changed", score=0.0, **details)
    broken = repeats(output.solution)
    if broken:
        message = f"not a solution: {broken[0]}" + (f" (and {len(broken) - 1} more)" if len(broken) > 1 else "")
        return result(False, message, score=score, **details)
    return result(True, "a correct solution: every given kept, every row, column and box complete", **details)


def verify_solve(arguments, output, reference, workspace):
    return gave_up_verdict(_judge(arguments, output, reference, workspace), output)
