"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    GET_PUZZLE = "get_puzzle"
    ANALYZE_GRID = "analyze_grid"
    PUZZLE_RECORD = "puzzle_record"


class Task(Enum):
    GET_PUZZLE = "get-puzzle"
    SOLVE_SUDOKU = "solve-sudoku"


ROWS = "Nine rows, top first, each nine characters: a digit 1 to 9, or . for an empty cell"


GAVE_UP = (
    "True only if you could not solve it: then submit your best partial attempt, or empty values."
    " False when you believe your answer is right"
)


@dataclass
class PuzzleInput(Output):
    puzzle_id: Annotated[str, "The puzzle's id, e.g. sudoku-01"]


@dataclass
class PuzzleOutput(Output):
    puzzle_id: Annotated[str, "The puzzle's id, as given"]
    rows: Annotated[list[str], ROWS]
    givens: Annotated[int, "How many cells are filled in"]


@dataclass
class GridInput(Output):
    rows: Annotated[list[str], ROWS]


@dataclass
class CellOptions(Output):
    row: Annotated[int, "The cell's row, 0 to 8 from the top"]
    col: Annotated[int, "The cell's column, 0 to 8 from the left"]
    options: Annotated[str, "The digits not yet used in its row, column or 3x3 box, in order; empty if none"]


@dataclass
class GridReportOutput(Output):
    empty_cells: Annotated[list[CellOptions], "Each empty cell and its options, row by row"]
    conflicts: Annotated[list[str], "Each row, column or box that holds a digit twice, e.g. row 0 repeats 7"]
    filled: Annotated[int, "How many cells are filled in"]


@dataclass
class SolutionOutput(Output):
    solvable: Annotated[bool, "Whether the puzzle has any solution at all"]
    solution: Annotated[
        list[str], "The solved grid as nine rows of nine digits 1 to 9, keeping every given; empty if unsolvable"
    ]
    gave_up: Annotated[bool, GAVE_UP]


TOOLS = {
    Tool.GET_PUZZLE: (PuzzleInput, PuzzleOutput),
    Tool.ANALYZE_GRID: (GridInput, GridReportOutput),
    Tool.PUZZLE_RECORD: (PuzzleInput, PuzzleOutput),
}
TASKS = {
    Task.GET_PUZZLE: (PuzzleInput, PuzzleOutput),
    Task.SOLVE_SUDOKU: (PuzzleInput, SolutionOutput),
}
