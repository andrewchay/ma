"""Feedback bridge - connect MA web feedback to init_agent self-evolution stack."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_BRIDGE_SCRIPT = Path(__file__).resolve().parents[1] / "init_agent_bridge_runner.py"
DEFAULT_FEEDBACK_LOG = Path("output/test_feedback_log.jsonl")


def _call_bridge(cmd: str, args: dict) -> dict:
    result = subprocess.run(
        [sys.executable, str(_BRIDGE_SCRIPT), cmd, json.dumps(args, ensure_ascii=False)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"init_agent bridge failed: {result.stderr}")
    return json.loads(result.stdout)


def session_id_from_path(session_path: str | None) -> str:
    if not session_path:
        return ""
    return Path(session_path).stem


def append_feedback(
    *,
    session_path: str,
    tester: str,
    feedback: str,
    severity: str = "medium",
    category: str = "general",
    steps_to_reproduce: str = "",
    expected_result: str = "",
    actual_result: str = "",
    version: str = "",
    log_path: Path = DEFAULT_FEEDBACK_LOG,
) -> Dict[str, Any]:
    session_id = session_id_from_path(session_path)
    item: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "session_id": session_id,
        "session_path": session_path,
        "tester": tester.strip() or "anonymous",
        "severity": (severity or "medium").strip().lower(),
        "category": (category or "general").strip().lower(),
        "version": (version or "").strip(),
        "feedback": feedback.strip(),
        "steps_to_reproduce": steps_to_reproduce.strip(),
        "expected_result": expected_result.strip(),
        "actual_result": actual_result.strip(),
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Bridge to init_agent FeedbackCollector + TrajectoryStore
    try:
        _call_bridge(
            "append_feedback",
            {
                "session_id": session_id,
                "severity": severity,
                "category": category,
                "comment": feedback,
                "correction_text": expected_result,
            },
        )
    except Exception:
        # Never block main UX due to optional bridge failure.
        pass

    return item


def list_feedback(
    *,
    session_id: Optional[str] = None,
    session_path: Optional[str] = None,
    log_path: Path = DEFAULT_FEEDBACK_LOG,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    if not log_path.exists():
        return []

    target_session_id = (session_id or "").strip()
    if not target_session_id and session_path:
        target_session_id = session_id_from_path(session_path)

    rows: List[Dict[str, Any]] = []
    lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for line in reversed(lines):
        raw = line.strip()
        if not raw:
            continue
        try:
            item = json.loads(raw)
        except Exception:
            continue
        if target_session_id and str(item.get("session_id", "")) != target_session_id:
            continue
        rows.append(item)
        if len(rows) >= limit:
            break
    return rows


def build_feedback_markdown(
    *,
    records: List[Dict[str, Any]],
    session_id: str,
    session_path: str = "",
) -> str:
    lines = [
        f"# 测试反馈报告（Session: {session_id or 'unknown'}）",
        "",
        f"- 生成时间: {datetime.now().isoformat(timespec='seconds')}",
        f"- Session Path: {session_path or 'N/A'}",
        f"- 反馈总数: {len(records)}",
        "",
    ]
    if not records:
        lines.append("暂无反馈记录。")
        return "\n".join(lines)

    for i, r in enumerate(records, start=1):
        lines.extend(
            [
                f"## {i}. {r.get('timestamp', '')} · {r.get('tester', 'anonymous')}",
                f"- 严重级别: {r.get('severity', '')}",
                f"- 问题类别: {r.get('category', '')}",
                f"- 版本: {r.get('version', '')}",
                f"- 反馈: {r.get('feedback', '')}",
                f"- 复现步骤: {r.get('steps_to_reproduce', '')}",
                f"- 期望结果: {r.get('expected_result', '')}",
                f"- 实际结果: {r.get('actual_result', '')}",
                "",
            ]
        )
    return "\n".join(lines)


def export_feedback_reports(
    *,
    session_path: str,
    log_path: Path = DEFAULT_FEEDBACK_LOG,
    output_dir: Path = Path("output"),
) -> Dict[str, str]:
    session_id = session_id_from_path(session_path)
    records = list_feedback(session_id=session_id, log_path=log_path, limit=1000)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"feedback_{session_id or 'unknown'}_{ts}"
    json_path = output_dir / f"{base}.json"
    md_path = output_dir / f"{base}.md"

    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(
        build_feedback_markdown(records=records, session_id=session_id, session_path=session_path),
        encoding="utf-8",
    )
    return {"json_path": str(json_path), "md_path": str(md_path), "session_id": session_id}


def generate_iteration_insights(days: int = 30) -> Dict[str, Any]:
    """Run init_agent trajectory reflection and return recommendations."""
    try:
        return _call_bridge("iteration_insights", {"days": days})
    except Exception as e:
        return {"ok": False, "message": f"bridge failed: {e}", "analysis": {}}


def persist_iteration_insights(payload: Dict[str, Any], output_dir: Path = Path("output")) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"iteration_insights_{ts}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def generate_release_gate_recommendation(
    *,
    min_feedback_score: float = 7.0,
    max_error_rate: float = 0.1,
    max_latency_ms: int = 5000,
    min_samples: int = 20,
) -> Dict[str, Any]:
    """Semi-automatic release gate recommendation (advisory only, never apply changes)."""
    try:
        return _call_bridge(
            "release_gate",
            {
                "min_feedback_score": min_feedback_score,
                "max_error_rate": max_error_rate,
                "max_latency_ms": max_latency_ms,
                "min_samples": min_samples,
            },
        )
    except Exception as e:
        return {"ok": False, "message": f"bridge failed: {e}", "recommendation": {}}


def persist_release_gate_report(payload: Dict[str, Any], output_dir: Path = Path("output")) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"release_gate_recommendation_{ts}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
