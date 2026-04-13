"""Session adapter - bridge MA workflow runs to init_agent QueryEngine + SessionStore."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

_BRIDGE_SCRIPT = Path(__file__).resolve().parents[1] / "init_agent_bridge_runner.py"


def _call_bridge(cmd: str, args: dict) -> dict:
    result = subprocess.run(
        [sys.executable, str(_BRIDGE_SCRIPT), cmd, json.dumps(args, ensure_ascii=False)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"init_agent bridge failed: {result.stderr}")
    return json.loads(result.stdout)


def persist_workflow_session(
    workflow_name: str,
    input_data: Dict[str, Any],
    result: Dict[str, Any],
    prompt_label: str = "ma-workflow",
) -> Tuple[str, str]:
    """Persist a workflow run as a QueryEngine session via init_agent bridge.

    Returns:
        (session_id, session_path) where session_path is the persisted .agent/sessions/*.json file.
    """
    payload = _call_bridge(
        "persist_session",
        {
            "workflow_name": workflow_name,
            "input_data": input_data,
            "result": result,
            "prompt_label": prompt_label,
        },
    )
    return payload["session_id"], payload["session_path"]
