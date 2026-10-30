from __future__ import annotations

from pathlib import Path

import pytest

from contract import GridInput, PuzzleInput, Tool
from plugin import analyze_grid, get_puzzle, puzzle_record
from plugin.budget import Budget, BudgetSpent
from plugin.puzzles import PUZZLES


def test_get_puzzle_returns_nine_rows(tmp_path: Path) -> None:
    puzzle = get_puzzle(PuzzleInput(puzzle_id="sudoku-01"), tmp_path)
    assert len(puzzle.rows) == 9 and all(len(row) == 9 for row in puzzle.rows)
    assert puzzle.rows[0] == ".79.6.5.8" and puzzle.givens == 40
    assert puzzle_record(PuzzleInput(puzzle_id="sudoku-01"), tmp_path) == puzzle
    with pytest.raises(ValueError, match="unknown puzzle"):
        get_puzzle(PuzzleInput(puzzle_id="sudoku-99"), tmp_path)


def test_puzzle_bank() -> None:
    assert len(PUZZLES) == 5
    assert all(len(text) == 81 and set(text) <= set(".123456789") for text in PUZZLES.values())


def test_analyze_grid_lists_options_and_conflicts(tmp_path: Path) -> None:
    rows = get_puzzle(PuzzleInput(puzzle_id="sudoku-01"), tmp_path).rows
    report = analyze_grid(GridInput(rows=rows), tmp_path)
    assert report.filled == 40 and report.conflicts == [] and len(report.empty_cells) == 41
    first = report.empty_cells[0]
    # Row 0 has 7 9 6 5 8, column 0 has 5 4: only 1, 2, 3 remain.
    assert (first.row, first.col, first.options) == (0, 0, "123")
    clash = ["77" + rows[0][2:]] + rows[1:]
    assert "row 0 repeats 7" in analyze_grid(GridInput(rows=clash), tmp_path).conflicts
    with pytest.raises(ValueError, match="9 rows of 9"):
        analyze_grid(GridInput(rows=rows[:8]), tmp_path)
    with pytest.raises(ValueError, match="9 rows of 9"):
        analyze_grid(GridInput(rows=["x" * 9] * 9), tmp_path)


def test_budget_allows_twelve_calls_per_puzzle() -> None:
    budget = Budget(limit=12)
    budget.charge(Tool.GET_PUZZLE, {"puzzle_id": "sudoku-01"})
    for _ in range(11):
        budget.charge(Tool.ANALYZE_GRID, {})
    with pytest.raises(BudgetSpent, match="submit your best answer now, or set gave_up"):
        budget.charge(Tool.ANALYZE_GRID, {})
    budget.charge(Tool.PUZZLE_RECORD, {})
    budget.charge(Tool.GET_PUZZLE, {"puzzle_id": "sudoku-02"})
    assert budget.used == 1
