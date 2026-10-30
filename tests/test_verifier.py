from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import TASKS, TOOLS, PuzzleInput, Task, Tool
from plugin import get_puzzle, puzzle_record

# sudoku-01's one solution, found independently of the verifier.
SOLUTION = [
    "379264518",
    "865391742",
    "241758369",
    "953476821",
    "186923475",
    "724815936",
    "592147683",
    "637582194",
    "418639257",
]


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
def verify_input(tool: str, value: dict) -> dict:
    return verifier.verify_input(tool, build_output(value, TOOLS[Tool(tool)][0]))


def verify_output(tool: str, given: dict, made: dict, workspace: Path) -> dict:
    classes = TOOLS[Tool(tool)]
    return verifier.verify_output(tool, build_output(given, classes[0]), build_output(made, classes[1]), str(workspace))


def solve(workspace: Path, puzzle_id: str, output: dict, pin: bool = True) -> dict:
    given, made = TASKS[Task.SOLVE_SUDOKU]
    record = plain_output(puzzle_record(PuzzleInput(puzzle_id=puzzle_id), workspace))
    pinned = build_output(record, TOOLS[Tool.PUZZLE_RECORD][1]) if pin else None
    return verifier.verify_task(
        "solve-sudoku",
        build_output({"puzzle_id": puzzle_id}, given),
        build_output({"gave_up": False} | output, made),
        pinned,
        str(workspace),
    )


def test_approves_the_solution(tmp_path: Path) -> None:
    verdict = solve(tmp_path, "sudoku-01", {"solvable": True, "solution": SOLUTION})
    assert verdict["valid"] is True and verdict["score"] == 1.0


def swap_two_cells_in_row(rows: list[str], row: int, a: int, b: int) -> list[str]:
    line = list(rows[row])
    line[a], line[b] = line[b], line[a]
    return rows[:row] + ["".join(line)] + rows[row + 1 :]


def test_wrong_cells_are_invalid_with_partial_credit(tmp_path: Path) -> None:
    # Row 8, columns 3 and 6 are empty in the puzzle: swapping them breaks two columns.
    broken = swap_two_cells_in_row(SOLUTION, 8, 3, 6)
    verdict = solve(tmp_path, "sudoku-01", {"solvable": True, "solution": broken})
    assert verdict["valid"] is False and "column" in verdict["message"]
    assert verdict["score"] == round(39 / 41, 4)


def test_changing_a_given_is_invalid(tmp_path: Path) -> None:
    # Row 0 column 1 is a given 7: swapping it with column 0 keeps rows valid but moves a given.
    moved = swap_two_cells_in_row(SOLUTION, 0, 0, 1)
    verdict = solve(tmp_path, "sudoku-01", {"solvable": True, "solution": moved})
    assert verdict["valid"] is False and "given" in verdict["message"]


@pytest.mark.parametrize(
    "solution",
    [
        [],  # missing
        SOLUTION[:8],  # too few rows
        [SOLUTION[0][:8]] + SOLUTION[1:],  # a short row
        ["37926451."] + SOLUTION[1:],  # an empty cell left
        ["379264510"] + SOLUTION[1:],  # a zero
    ],
)
def test_malformed_solutions_score_zero(tmp_path: Path, solution: list[str]) -> None:
    verdict = solve(tmp_path, "sudoku-01", {"solvable": True, "solution": solution})
    assert verdict["valid"] is False and verdict["score"] == 0.0


def test_unsolvable_puzzle_must_be_reported_so(tmp_path: Path) -> None:
    verdict = solve(tmp_path, "sudoku-05", {"solvable": False, "solution": []})
    assert verdict["valid"] is True
    verdict = solve(tmp_path, "sudoku-05", {"solvable": True, "solution": SOLUTION})
    assert verdict["valid"] is False and verdict["score"] == 0.0


def test_calling_a_solvable_puzzle_unsolvable_is_invalid(tmp_path: Path) -> None:
    verdict = solve(tmp_path, "sudoku-04", {"solvable": False, "solution": []})
    assert verdict["valid"] is False and "has a solution" in verdict["message"]


def test_unsolvable_claim_with_a_grid_is_invalid(tmp_path: Path) -> None:
    verdict = solve(tmp_path, "sudoku-05", {"solvable": False, "solution": SOLUTION})
    assert verdict["valid"] is False and "empty" in verdict["message"]


def test_refuses_to_judge_without_the_puzzle(tmp_path: Path) -> None:
    verdict = solve(tmp_path, "sudoku-01", {"solvable": True, "solution": SOLUTION}, pin=False)
    assert verdict["valid"] is False and "puzzle" in verdict["message"]


def test_tool_task_and_tool_checks(tmp_path: Path) -> None:
    given = {"puzzle_id": "sudoku-01"}
    made = plain_output(get_puzzle(PuzzleInput(**given), tmp_path))
    task_given, task_made = TASKS[Task.GET_PUZZLE]
    verdict = verifier.verify_task(
        "get-puzzle", build_output(given, task_given), build_output(made, task_made), None, ""
    )
    assert verdict["valid"] is True
    assert verify_output("get_puzzle", given, made | {"givens": 41}, tmp_path)["valid"] is False
    assert verify_input("get_puzzle", given)["valid"] is True
    assert verify_input("analyze_grid", {"rows": SOLUTION})["valid"] is True
    assert verify_input("analyze_grid", {"rows": SOLUTION[:3]})["valid"] is False
    report = {"empty_cells": [], "conflicts": [], "filled": 81}
    assert verify_output("analyze_grid", {"rows": SOLUTION}, report, tmp_path)["valid"] is True
    assert verify_output("analyze_grid", {"rows": SOLUTION}, report | {"filled": 80}, tmp_path)["valid"] is False


def test_giving_up_is_a_failure_with_the_attempt_kept_in_details(tmp_path: Path) -> None:
    verdict = solve(tmp_path, "sudoku-01", {"solvable": True, "solution": SOLUTION, "gave_up": True})
    assert verdict["valid"] is False and verdict["score"] == 0.0 and "gave up" in verdict["message"]
    assert verdict["details"]["attempt_score"] == 1.0
    verdict = solve(tmp_path, "sudoku-01", {"solvable": True, "solution": [], "gave_up": True})
    assert verdict["valid"] is False and verdict["score"] == 0.0 and verdict["details"]["gave_up"] is True
