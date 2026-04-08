"""Allow running as python -m agent_core"""
from __future__ import annotations

from agent_core.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
