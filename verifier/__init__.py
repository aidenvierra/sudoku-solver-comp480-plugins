"""The deterministic verifier: each tool's checks live in its own class, on contract instances."""

from contract import Task, Tool

from .sudoku import AnalyzeGrid, GetPuzzle, verify_get_puzzle, verify_solve

TOOLS = {
    Tool.GET_PUZZLE: GetPuzzle,
    Tool.ANALYZE_GRID: AnalyzeGrid,
    Tool.PUZZLE_RECORD: GetPuzzle,
}
# task -> its output's check, verify_task(arguments, output, reference, workspace)
TASKS = {
    Task.GET_PUZZLE: verify_get_puzzle,
    Task.SOLVE_SUDOKU: verify_solve,
}


def verify_input(tool, value):
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    return TASKS[Task(task)](arguments, output, reference, workspace)
