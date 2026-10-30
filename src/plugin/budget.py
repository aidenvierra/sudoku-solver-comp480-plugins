from __future__ import annotations

from typing import Any

from contract import Tool

# Tool calls the agent may make per puzzle, get_puzzle included. NanoAgent keeps one plugin
# process per run, so this caps a run's calls wherever it runs, RUSH Lab included.
LIMIT = 12


class BudgetSpent(RuntimeError):
    pass


class Budget:
    """Counts tool calls per puzzle; a get_puzzle for a different puzzle starts a new count."""

    def __init__(self, limit: int = LIMIT) -> None:
        self.limit = limit
        self.puzzle: str | None = None
        self.used = 0

    def charge(self, tool: Tool, arguments: dict[str, Any]) -> None:
        if tool is Tool.PUZZLE_RECORD:
            return  # the verifier's reference, called by NanoAgent, never by the agent
        if tool is Tool.GET_PUZZLE and arguments.get("puzzle_id") != self.puzzle:
            self.puzzle, self.used = arguments.get("puzzle_id"), 0
        if self.used >= self.limit:
            raise BudgetSpent(
                f"tool budget used up: all {self.limit} tool calls for this puzzle are spent;"
                " submit your best answer now, or set gave_up to true if you could not solve it"
            )
        self.used += 1


BUDGET = Budget()
