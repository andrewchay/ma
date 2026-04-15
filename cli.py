#!/usr/bin/env python3
"""CLI entry point for MA Agent"""
from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path if _env_path.exists() else None)

from agent_core.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
