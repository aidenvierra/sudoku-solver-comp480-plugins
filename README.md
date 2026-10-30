# Sudoku Solver

A `nanoagent.plugin/v0001` plugin, created by `nanoagent plugin new` with the
structure of NanoAgent's reference plugin,
[arxiv-source](https://github.com/zeyuyang8/arxiv-source).

## Tools

Five fixed 9x9 puzzles live in `src/plugin/puzzles.py`: four with one solution
each, from 40 clues down to 25, and one that looks fine (no row, column or box
repeats a digit) but has no solution. The agent must solve each, or show it has
no solution, within 12 tool calls per puzzle. No network is used.

| Tool | Does | Code |
|---|---|---|
| `get_puzzle` | Returns a puzzle's nine rows and its number of givens | `src/plugin/puzzles.py` |
| `analyze_grid` | Lists each empty cell's options and any repeated digits | `src/plugin/puzzles.py` |
| `puzzle_record` | Returns the puzzle; only the verifier's reference | `src/plugin/puzzles.py` |

`src/plugin/budget.py` caps the agent at 12 tool calls per puzzle; after that
every tool fails and asks it to submit.

### Tasks

| Task | Does | Runner |
|---|---|---|
| `get-puzzle` | Shows a sudoku puzzle | `tool`, with `get_puzzle` |
| `solve-sudoku` | Solves the puzzle, or reports it has no solution | `agent`, with `get_puzzle`, `analyze_grid`; reference `puzzle_record` |

The verifier solves the pinned puzzle itself by backtracking. A submitted grid
is valid when it keeps every given and no row, column or box repeats a digit,
so any correct solution is accepted. A wrong grid scores the share of empty
cells it filled correctly. For the puzzle with no solution, only
`solvable: false` with an empty grid is valid.

A submission with `gave_up: true` always fails (invalid, score 0); its attempt's own score is kept
in the verdict details as `attempt_score`.

## Layout

```text
.
├── nanoagent.yaml   # manifest (a slimconfig ManifestConfig): id, runtime, permissions, tools, tasks
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # environment variable NAMEs this plugin needs, never values
├── src/plugin/      # the MCP server: __main__.py, its IMPLEMENTATIONS, and the plugin's own modules
├── tests/
├── ui/              # how the page draws the outputs: renderers.js and renderers.css
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier package
```

`contract.py` is the one place a value's shape is declared. Its `Output`
classes are the JSON Schemas the server offers and the agent sees, and every
input and output is built into its class on the way in and out: the server,
NanoAgent and the verifier all get typed values, never loose dicts. A tool
that fails raises; NanoAgent sees an MCP error.

To add a tool: add a `Tool` member, its input and output classes and its
`TOOLS` entry to `contract.py` (a snake_case name, classes named `...Input`
and `...Output`); write its implementation in `src/plugin/`, taking its input
and the workspace and returning its output; write its `verify_input` /
`verify_output` in `verifier/`, and tests for both. Then register it in
`src/plugin/__main__.py` (`IMPLEMENTATIONS`), `verifier/__init__.py` (`TOOLS`),
`nanoagent.yaml` (`tools`) and this README's Tools table; a task goes in its
Tasks table.

`LICENSE` stays the template's MIT license under your name, `.gitignore`
keeps its entries, and this README keeps its title and sections: NanoAgent refuses a plugin
that changes them (rule 10 of `nanoagent.plugin.manifest`). Renaming the
plugin means renaming it in `nanoagent.yaml` and this title together.

To add a task, add a `Task` member (a kebab-case id) and its `TASKS` input and
output classes to `contract.py`, and declare it in `nanoagent.yaml` with its `runner` (`tool`,
`agent` or `decide`) and a `reference` tool, or `null` if it has none. A `tool`
task's classes are its tool's; an `agent` task's agent ends by calling `submit`
with the task's output; a `decide` task's model only chooses, and every tool
argument and output field is an Enum or bool, or copied from a value of exactly
its type in the task's input or an earlier tool output. Then add the check of
its output, `verify_task(arguments, output, reference, workspace)`, to `TASKS`
in `verifier/__init__.py`. People use the plugin by chatting with its agent,
which runs its tasks and shows each output on the page (see `ui/`).

## Develop and run

```bash
uv sync --extra dev
uv run pytest
```

Publishing checks every plugin rule: push the plugin to a public GitHub
repository and run `rush publish <server> <github-url>`.
