#!/usr/bin/env python3
"""FastAPI backend for MA Agent serving the flows HTML frontend."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent_core.llm import get_llm_client
from agent_core.tools.strategy_iq import parse_brief, generate_strategy
from agent_core.tools.match_ai import search_kols, generate_kol_combo_with_llm
from agent_core.tools.connect_bot import (
    generate_outreach_with_llm,
    generate_follow_up_with_llm,
    generate_negotiation_strategy_with_llm,
)
from agent_core.tools.creative_pilot import generate_creative_brief_with_llm
from agent_core.session_adapter import persist_workflow_session
from agent_core.feedback_bridge import (
    append_feedback,
    list_feedback,
    export_feedback_reports,
    generate_iteration_insights,
    generate_release_gate_recommendation,
    persist_iteration_insights,
    persist_release_gate_report,
    session_id_from_path,
)

WEB_DIR = Path(__file__).resolve().parent / "web"


class AnalyzeBriefRequest(BaseModel):
    text: str
    filename: str = ""


class GenerateAnalysisRequest(BaseModel):
    brand: str
    product: str
    features: str = ""
    goal: str = ""
    budget: str = ""
    cpm: str = ""
    cpe: str = ""
    theme: str = ""


class GenerateKOLsRequest(BaseModel):
    selected: List[Dict[str, Any]]
    brand: str = ""
    product: str = ""
    goal: str = ""
    budget: str = ""
    cpm: str = ""
    cpe: str = ""


class GenerateMessagesRequest(BaseModel):
    selected: List[Dict[str, Any]]
    brand: str = "某品牌"
    product: str = "某产品"


class GenerateContentRequest(BaseModel):
    selected: List[Dict[str, Any]]
    brand: str = "某品牌"
    product: str = "某产品"
    theme: str = ""


class FeedbackRequest(BaseModel):
    session_path: str
    tester: str = ""
    feedback: str
    severity: str = "medium"
    category: str = "general"
    steps_to_reproduce: str = ""
    expected_result: str = ""
    actual_result: str = ""
    version: str = ""


class AIPromptRequest(BaseModel):
    prompt: str
    system_prompt: str = "你是一位有10年经验的专业市场营销顾问，擅长品牌传播策略、KOL营销和内容创意。请用专业且结构化的方式回答。"
    temperature: float = 0.7


def _extract_json_from_text(text: str) -> dict:
    try:
        match = __import__("re").search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        return json.loads(text)
    except Exception:
        return {}


def _run_strategy_flow(brief_data: dict) -> dict:
    """Run StrategyIQ and return structured result."""
    parsed = parse_brief(
        f"品牌：{brief_data.get('brand', '')}\n"
        f"产品：{brief_data.get('product', '')}\n"
        f"卖点：{brief_data.get('features', '')}\n"
        f"目标：{brief_data.get('goal', '')}\n"
        f"预算：{brief_data.get('budget', '')}\n"
        f"CPM：{brief_data.get('cpm', '')}\n"
        f"CPE：{brief_data.get('cpe', '')}\n"
        f"主题：{brief_data.get('theme', '')}\n"
    )
    strategy = generate_strategy(parsed)
    return {
        "parsed": parsed,
        "strategy": strategy,
        "markdown": _strategy_to_markdown(parsed, strategy),
    }


def _strategy_to_markdown(parsed: dict, strategy: dict) -> str:
    lines = ["# AI传播方案", ""]
    lines.append("## 1. 用户研究")
    lines.append(f"- **目标受众**: {parsed.get('target_audience', '待补充')}")
    lines.append(f"- **品牌**: {parsed.get('brand', '')}")
    lines.append(f"- **产品**: {parsed.get('product', '')}")
    lines.append("")
    lines.append("## 2. 竞品分析")
    lines.append("建议分析主要竞品在相同平台的投放策略与内容形式。")
    lines.append("")
    lines.append("## 3. 传播策略建议")
    ps = strategy.get("platform_strategy", [])
    for p in ps[:3]:
        lines.append(f"- **{p.get('name', '平台')}**: {p.get('goal', '')}（{p.get('priority', '中')}优先级）")
    lines.append("")
    lines.append("## 4. 创意内容方向")
    lines.append("1. 真实体验分享向")
    lines.append("2. 专业测评科普向")
    lines.append("3. 场景化种草向")
    lines.append("")
    lines.append("## 5. 推荐平台优先级")
    lines.append(", ".join([p.get("name", "") for p in ps if p.get("name")]) or "小红书、抖音")
    return "\n".join(lines)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="MA Agent API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return FileResponse(WEB_DIR / "index.html")


@app.post("/api/analyze-brief")
async def api_analyze_brief(req: AnalyzeBriefRequest):
    """Parse uploaded brief text into structured fields."""
    if not req.text or len(req.text) < 10:
        return JSONResponse(status_code=400, content={"error": "文字内容太少"})

    parsed = parse_brief(req.text)
    # Normalize to frontend expected format
    result = {
        "brand": parsed.get("brand", ""),
        "product": parsed.get("product", "") or "",
        "features": ", ".join(parsed.get("key_messages", [])),
        "goal": parsed.get("goal", ""),
        "budget": str(parsed.get("budget_amount", "")),
        "cpm": "",
        "cpe": "",
        "theme": "",
    }
    return {"ok": True, "data": result}


@app.post("/api/generate-analysis")
async def api_generate_analysis(req: GenerateAnalysisRequest):
    """Generate full strategy analysis."""
    brief_data = req.dict()
    result = _run_strategy_flow(brief_data)

    # Persist session
    try:
        sid, spath = persist_workflow_session(
            workflow_name="StrategyIQ",
            input_data=brief_data,
            result=result,
            prompt_label="ma-strategy",
        )
        result["session_id"] = sid
        result["session_path"] = spath
    except Exception as e:
        result["session_error"] = str(e)

    return {"ok": True, "result": result}


@app.post("/api/generate-kols")
async def api_generate_kols(req: GenerateKOLsRequest):
    """Generate KOL combination recommendations."""
    selected = req.selected
    if len(selected) < 2:
        return JSONResponse(status_code=400, content={"error": "请至少选择2个KOL"})

    # Use MatchAI to generate combo reasoning
    budget_val = 100
    try:
        budget_str = req.budget or ""
        budget_val = float(budget_str) if budget_str else 100.0
    except Exception:
        budget_val = 100.0

    platforms = list({k.get("platform", "小红书") for k in selected})
    combo = generate_kol_combo_with_llm(
        budget=budget_val,
        platforms=platforms[:2],
        category="通用",
        brand=req.brand or "品牌",
        product=req.product or "产品",
        goal=req.goal or "种草",
    )

    total_price = sum(k.get("price", 0) for k in selected)
    total_views = sum(k.get("avgViews", 0) for k in selected)
    total_engagement = sum(k.get("avgEngagement", 0) for k in selected)

    result = {
        "combo": combo,
        "total_price": total_price,
        "total_views": total_views,
        "total_engagement": total_engagement,
        "cpm": round(total_price / max(total_views / 1000, 1), 2),
        "cpe": round(total_price / max(total_engagement, 1), 2),
    }

    # Persist session
    try:
        sid, spath = persist_workflow_session(
            workflow_name="MatchAI",
            input_data=req.dict(),
            result=result,
            prompt_label="ma-kol",
        )
        result["session_id"] = sid
        result["session_path"] = spath
    except Exception as e:
        result["session_error"] = str(e)

    return {"ok": True, "result": result}


@app.post("/api/generate-messages")
async def api_generate_messages(req: GenerateMessagesRequest):
    """Generate outreach messages for selected KOLs."""
    selected = req.selected
    if not selected:
        return JSONResponse(status_code=400, content={"error": "请先选择KOL"})

    messages = []
    for kol in selected:
        msg = generate_outreach_with_llm(
            kol_name=kol.get("name", "KOL"),
            kol_profile=kol,
            brand=req.brand,
            brand_intro=f"致力于提供优质{req.product}",
            product=req.product,
            platform=kol.get("platform", "小红书"),
            style="professional",
            cooperation_type="内容合作",
            budget_range="面议",
        )
        messages.append({"kol": kol.get("name"), "platform": kol.get("platform"), "message": msg})

    result = {"messages": messages}

    # Persist session
    try:
        sid, spath = persist_workflow_session(
            workflow_name="ConnectBot",
            input_data=req.dict(),
            result=result,
            prompt_label="ma-outreach",
        )
        result["session_id"] = sid
        result["session_path"] = spath
    except Exception as e:
        result["session_error"] = str(e)

    return {"ok": True, "result": result}


@app.post("/api/generate-content")
async def api_generate_content(req: GenerateContentRequest):
    """Generate creative content directions for selected KOLs."""
    selected = req.selected
    if not selected:
        return JSONResponse(status_code=400, content={"error": "请先选择KOL"})

    creatives = {}
    platforms = list({k.get("platform", "小红书") for k in selected})
    for p in platforms[:2]:
        creatives[p] = generate_creative_brief_with_llm(
            brand=req.brand,
            product=req.product,
            platform=p,
            kol_style="真实分享",
            key_messages=[],
            must_include=["产品展示", "使用体验"],
            forbidden=["竞品对比", "绝对化用语"],
            target_audience="目标受众",
            campaign_goal="种草",
            industry="通用",
            kol_profile=selected[0],
        )

    result = {"creatives": creatives, "selected": selected}

    # Persist session
    try:
        sid, spath = persist_workflow_session(
            workflow_name="CreativePilot",
            input_data=req.dict(),
            result=result,
            prompt_label="ma-creative",
        )
        result["session_id"] = sid
        result["session_path"] = spath
    except Exception as e:
        result["session_error"] = str(e)

    return {"ok": True, "result": result}


@app.post("/api/ai-proxy")
async def api_ai_proxy(req: AIPromptRequest):
    """Generic AI proxy for fallback prompts not covered by specific endpoints."""
    client = get_llm_client()
    try:
        content = client.chat(
            messages=[
                {"role": "system", "content": req.system_prompt},
                {"role": "user", "content": req.prompt},
            ],
            temperature=req.temperature,
        )
        return {"ok": True, "content": content}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/feedback")
async def api_feedback(req: FeedbackRequest):
    saved = append_feedback(
        session_path=req.session_path,
        tester=req.tester,
        feedback=req.feedback,
        severity=req.severity,
        category=req.category,
        steps_to_reproduce=req.steps_to_reproduce,
        expected_result=req.expected_result,
        actual_result=req.actual_result,
        version=req.version,
    )
    return {"ok": True, "data": saved}


@app.get("/api/feedback")
async def api_list_feedback(session_path: str):
    records = list_feedback(session_path=session_path, limit=50)
    return {"ok": True, "records": records}


@app.post("/api/feedback/export")
async def api_export_feedback(session_path: str):
    exported = export_feedback_reports(session_path=session_path)
    return {"ok": True, "data": exported}


@app.get("/api/iteration-insights")
async def api_iteration_insights(days: int = 30):
    insights = generate_iteration_insights(days=days)
    return insights


@app.post("/api/iteration-insights/export")
async def api_export_iteration_insights(payload: dict):
    path = persist_iteration_insights(payload)
    return {"ok": True, "path": path}


@app.get("/api/release-gate")
async def api_release_gate(
    min_feedback_score: float = 7.0,
    max_error_rate: float = 0.1,
    max_latency_ms: int = 5000,
    min_samples: int = 20,
):
    gate = generate_release_gate_recommendation(
        min_feedback_score=min_feedback_score,
        max_error_rate=max_error_rate,
        max_latency_ms=max_latency_ms,
        min_samples=min_samples,
    )
    return gate


@app.post("/api/release-gate/export")
async def api_export_release_gate(payload: dict):
    path = persist_release_gate_report(payload)
    return {"ok": True, "path": path}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8501)
