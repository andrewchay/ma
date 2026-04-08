from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    """Metadata for a registered tool."""

    name: str
    responsibility: str
    input_schema: dict[str, Any]
    executor: Callable[..., str]


@dataclass(frozen=True)
class ToolExecution:
    """Result of executing a tool."""

    name: str
    handled: bool
    payload: str
    output: str
    message: str
