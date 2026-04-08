from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class CommandModule:
    """Metadata for a registered CLI command."""

    name: str
    responsibility: str
    source_hint: str
    handler: Callable[[list[str]], int]


@dataclass(frozen=True)
class CommandExecution:
    """Result of executing a command."""

    name: str
    handled: bool
    message: str
    exit_code: int = 0
