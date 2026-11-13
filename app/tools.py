from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    allowed_agents: tuple[str, ...]
    handler: Callable[[dict[str, Any]], Any]

def _task_summary(arguments: dict[str, Any]) -> dict[str, Any]:
    description = arguments.get("description", "").strip()
    if not description:
        raise ValueError("description is required")
    return {"summary": f"Task requires coordinated execution: {description}"}

def _word_count(arguments: dict[str, Any]) -> dict[str, int]:
    text = arguments.get("text", "").strip()
    if not text:
        raise ValueError("text is required")
    return {"words": len(text.split())}

TOOLS = (
    Tool("task_summary", "Create a short summary of a task", ("planner", "writer", "executor"), _task_summary),
    Tool("word_count", "Count words in supplied text", ("writer", "analyst", "executor"), _word_count),
)

def list_tools() -> list[Tool]:
    return list(TOOLS)

def execute_tool(name: str, agent: str, arguments: dict[str, Any]) -> Any:
    tool = next((item for item in TOOLS if item.name == name), None)
    if not tool:
        raise KeyError(f"Unknown tool: {name}")
    if agent not in tool.allowed_agents:
        raise PermissionError(f"Agent '{agent}' cannot use '{name}'")
    return tool.handler(arguments)
