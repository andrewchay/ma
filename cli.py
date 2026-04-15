#!/usr/bin/env python3
"""CLI entry point for MA Agent"""
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from agent_core.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
