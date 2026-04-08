"""CLI main entry point"""
from __future__ import annotations

import sys
from agent_core.commands import BUILTIN_COMMANDS


def main() -> int:
    """Main CLI entry"""
    if len(sys.argv) < 2:
        print("Usage: ma <command> [args...]")
        print("Run 'ma help' for more information")
        return 1
    
    command_name = sys.argv[1]
    args = sys.argv[2:]
    
    # Find command
    for command in BUILTIN_COMMANDS:
        if command.name == command_name:
            return command.handler(args)
    
    print(f"Unknown command: {command_name}")
    print("Run 'ma help' for available commands")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
