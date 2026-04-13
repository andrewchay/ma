#!/usr/bin/env python3
"""Bridge runner that isolates init_agent imports from ma's agent_core shadowing."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _clean_sys_path():
    ma_root = Path(__file__).resolve().parent
    filtered = []
    for p in sys.path:
        if p == "":
            continue
        try:
            if Path(p).resolve() == ma_root.resolve():
                continue
        except Exception:
            pass
        filtered.append(p)
    sys.path = filtered


def _add_init_agent():
    init_agent_root = Path(__file__).resolve().parent.parent / "init_agent"
    sys.path.insert(0, str(init_agent_root))


def cmd_persist_session(args: dict) -> dict:
    from agent_core.engine.engine import QueryEngine
    from agent_core.models import ToolExecution

    workflow_name = args["workflow_name"]
    input_data = args["input_data"]
    result = args["result"]
    prompt_label = args.get("prompt_label", "ma-workflow")

    engine = QueryEngine()
    payload_json = json.dumps(input_data, ensure_ascii=False)
    output_json = json.dumps(result, ensure_ascii=False)

    te = ToolExecution(
        name=workflow_name,
        handled=True,
        payload=payload_json,
        output=output_json,
        message="ok",
    )

    engine.submit_turn(
        prompt=f"{prompt_label} workflow={workflow_name}",
        matched_commands=(),
        matched_tools=(workflow_name,),
        tool_results=(te,),
    )

    session_path = engine.persist_session()
    return {"session_id": engine.session_id, "session_path": str(session_path)}


def cmd_append_feedback(args: dict) -> dict:
    from agent_core.feedback.collector import FeedbackCollector
    from agent_core.models.feedback import FeedbackTag, FeedbackTaxonomy
    from agent_core.models.trajectory import TrajectorySession
    from agent_core.trajectory.events import EventBuilder
    from agent_core.trajectory.store import TrajectoryStore

    session_id = str(args.get("session_id", "")).strip()
    if not session_id:
        return {"ok": False, "message": "missing session_id"}

    severity = str(args.get("severity", "medium")).strip().lower()
    score_map = {"critical": 2, "high": 4, "medium": 7, "low": 9}
    score = score_map.get(severity, 7)

    category = str(args.get("category", "general")).strip().lower()
    tag_map = {
        "ui": [FeedbackTag.OTHER],
        "data": [FeedbackTag.METRIC_MISMATCH],
        "logic": [FeedbackTag.CONCLUSION_UNGROUNDED],
        "performance": [FeedbackTag.TOO_VERBOSE],
        "llm": [FeedbackTag.CLARIFICATION_OFF],
        "integration": [FeedbackTag.TOOL_MISUSE],
        "general": [FeedbackTag.OTHER],
    }
    tags = tag_map.get(category, [FeedbackTag.OTHER])

    collector = FeedbackCollector()
    feedback = collector.collect(
        session_id=session_id,
        score=score,
        tags=tags,
        comment=str(args.get("comment", "")),
        correction_text=str(args.get("correction_text", "")) or None,
        taxonomy=FeedbackTaxonomy.STRUCTURED_RATING,
        collected_at="web_feedback_form",
    )

    store = TrajectoryStore()
    builder = EventBuilder()
    event = builder.user_feedback(
        session_id=session_id,
        feedback_id=feedback.feedback_id,
        score=feedback.score,
        tags=[t.value for t in feedback.tags],
        comment=feedback.comment,
    )
    store.store_event(event)

    summary = store.get_session(session_id) or TrajectorySession(session_id=session_id)
    summary.has_feedback = True
    summary.feedback_score = float(feedback.score)
    store.update_session_summary(summary)

    return {"ok": True, "feedback_id": feedback.feedback_id, "score": feedback.score}


def cmd_iteration_insights(args: dict) -> dict:
    from agent_core.meta.reflector import TrajectoryReflector
    from agent_core.trajectory.store import TrajectoryStore

    days = args.get("days", 30)
    store = TrajectoryStore()
    recent = store.get_recent_sessions(limit=200, with_feedback_only=True)
    sessions = []
    for row in recent:
        sid = row.get("session_id")
        if not sid:
            continue
        s = store.get_session(sid)
        if s:
            sessions.append(s)
    reflector = TrajectoryReflector()
    analysis = reflector.analyze_sessions(sessions=sessions, min_feedback_score=7.0)
    analysis["period_days"] = days
    return {"ok": True, "message": f"analyzed {len(sessions)} sessions", "analysis": analysis}


def cmd_release_gate(args: dict) -> dict:
    from agent_core.experiment.release import ReleaseManager

    rm = ReleaseManager(root=Path.cwd())
    status = rm.status()
    state = status.get("state", {}) if isinstance(status, dict) else {}
    has_canary = bool(state.get("has_canary", False))

    gates = {
        "min_feedback_score": float(args.get("min_feedback_score", 7.0)),
        "max_error_rate": float(args.get("max_error_rate", 0.1)),
        "max_latency_ms": int(args.get("max_latency_ms", 5000)),
        "min_samples": int(args.get("min_samples", 20)),
    }

    if has_canary:
        check = rm.check_canary_health(
            max_error_rate=gates["max_error_rate"],
            min_feedback_score=gates["min_feedback_score"],
            max_latency_ms=gates["max_latency_ms"],
            min_samples=gates["min_samples"],
            auto_rollback=False,
            apply=False,
            reviewer="flow-advisor",
            reason="advisory-check",
        )
        passed = bool(check.get("ok", False))
        return {
            "ok": True,
            "message": "canary health evaluated",
            "mode": "canary_gate",
            "gates": gates,
            "status": state,
            "health_check": check,
            "recommendation": {
                "decision": "promote_candidate" if passed else "hold_and_iterate",
                "confidence": "high" if passed else "medium",
                "reason": check.get("message", ""),
                "next_actions": (
                    ["人工确认后执行 release-promote --apply"]
                    if passed
                    else ["修复问题后继续采样，再次执行 release-check"]
                ),
            },
        }

    # pre-canary advisory (simplified without feedback health query here)
    return {
        "ok": True,
        "message": "advisory recommendation generated (no active canary)",
        "mode": "pre_canary_advisory",
        "gates": gates,
        "status": state,
        "recommendation": {
            "decision": "collect_more_feedback",
            "confidence": "medium",
            "reason": "pre-canary advisory without local feedback health query",
            "next_actions": ["继续收集反馈并优化，达到阈值后再进入 canary"],
        },
    }


def main():
    _clean_sys_path()
    _add_init_agent()

    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    handlers = {
        "persist_session": cmd_persist_session,
        "append_feedback": cmd_append_feedback,
        "iteration_insights": cmd_iteration_insights,
        "release_gate": cmd_release_gate,
    }

    handler = handlers.get(cmd)
    if not handler:
        print(json.dumps({"ok": False, "message": f"unknown command: {cmd}"}))
        sys.exit(1)

    try:
        result = handler(args)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"ok": False, "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
