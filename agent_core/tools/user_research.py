"""Autonomous user research helper (provider-agnostic)."""
from __future__ import annotations

import json
import re
from typing import Any


def _strip_html(raw: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fetch_url_text(url: str, timeout: int = 8) -> str:
    try:
        import requests

        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code >= 400:
            return ""
        body = _strip_html(resp.text)
        return body[:1800]
    except Exception:
        return ""


def _duckduckgo_search_snippets(query: str, max_items: int = 5) -> list[dict[str, str]]:
    """Use DuckDuckGo instant-answer API for lightweight web snippets."""
    try:
        import requests

        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code >= 400:
            return []
        data = resp.json()
        out: list[dict[str, str]] = []

        abstract = (data.get("AbstractText") or "").strip()
        abstract_url = (data.get("AbstractURL") or "").strip()
        if abstract:
            out.append({"title": data.get("Heading", query), "snippet": abstract, "url": abstract_url})

        for item in data.get("RelatedTopics", []) or []:
            if isinstance(item, dict) and item.get("Text"):
                out.append(
                    {
                        "title": item.get("Text", "")[:80],
                        "snippet": item.get("Text", ""),
                        "url": item.get("FirstURL", ""),
                    }
                )
            if len(out) >= max_items:
                break
        return out[:max_items]
    except Exception:
        return []


def _default_queries(brief_data: dict[str, Any], brief_text: str) -> list[str]:
    brand = brief_data.get("brand", "品牌")
    industry = brief_data.get("industry", "行业")
    audience = brief_data.get("target_audience", "目标受众")
    return [
        f"{industry} 消费者画像 2025 2026",
        f"{industry} 用户行为 生活习惯 报告",
        f"{brand} 竞品 传播 案例",
        f"{audience} 社交媒体 内容偏好",
        brief_text[:60],
    ]


def generate_user_research_with_llm(
    brief_data: dict[str, Any],
    brief_text: str = "",
    external_links: list[str] | None = None,
    user_notes: str = "",
) -> dict[str, Any]:
    """Run autonomous desk-research + LLM synthesis for user research."""
    from agent_core.llm import get_llm_client

    llm = get_llm_client()

    queries = _default_queries(brief_data, brief_text)
    evidence: list[dict[str, str]] = []

    # 1) autonomous quick web snippets
    for q in queries[:4]:
        items = _duckduckgo_search_snippets(q, max_items=3)
        for it in items:
            if it.get("snippet"):
                evidence.append({
                    "source": it.get("url", ""),
                    "title": it.get("title", ""),
                    "summary": it.get("snippet", "")[:280],
                    "query": q,
                })

    # 2) user-provided links have highest priority
    for url in (external_links or [])[:8]:
        text = _fetch_url_text(url)
        if text:
            evidence.append({
                "source": url,
                "title": "User Provided Source",
                "summary": text[:420],
                "query": "user_link",
            })

    evidence = evidence[:20]

    system_prompt = """你是资深市场研究分析师。请基于输入brief和证据，产出结构化用户研究，必须给出可执行洞察。
输出JSON：
{
  "persona_profile": {
    "target_audience": "...",
    "dimensions": ["年龄", "性别", "收入", "城市层级", "社会关系"],
    "key_traits": ["特征1", "特征2"]
  },
  "behavior_habits": ["习惯1", "习惯2", "习惯3"],
  "scenario_insights": ["场景洞察1", "场景洞察2", "场景洞察3"],
  "emotional_insights": ["情感洞察1", "情感洞察2"],
  "research_hypotheses": ["待验证假设1", "待验证假设2"],
  "evidence_used": [
    {"source": "url", "why_it_matters": "为何有价值"}
  ]
}"""

    prompt = f"""Brief信息：
{json.dumps(brief_data, ensure_ascii=False, indent=2)}

原始Brief：
{brief_text}

用户补充说明：
{user_notes}

已收集证据：
{json.dumps(evidence, ensure_ascii=False, indent=2)}

请输出用户研究JSON。"""

    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            result.setdefault(
                "research_inputs",
                {
                    "queries": queries,
                    "external_links": external_links or [],
                    "user_notes": user_notes,
                    "auto_evidence_count": len(evidence),
                },
            )
            return result
    except Exception:
        pass

    # fallback
    return {
        "persona_profile": {
            "target_audience": brief_data.get("target_audience", "未提及"),
            "dimensions": ["年龄", "性别", "收入", "城市层级", "社会关系"],
            "key_traits": ["关注真实证据", "社媒高频活跃"],
        },
        "behavior_habits": ["决策前看测评", "依赖口碑与KOL内容"],
        "scenario_insights": ["关键场景更关注可感知收益", "内容需从生活情境切入"],
        "emotional_insights": ["消费承载身份表达", "情绪共鸣驱动转发"],
        "research_hypotheses": ["情绪叙事+功能证明组合可提升互动"],
        "evidence_used": [{"source": e.get("source", ""), "why_it_matters": "外部证据参考"} for e in evidence[:6]],
        "research_inputs": {
            "queries": queries,
            "external_links": external_links or [],
            "user_notes": user_notes,
            "auto_evidence_count": len(evidence),
        },
    }
