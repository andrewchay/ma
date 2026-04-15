"""Strategy researcher - orchestrates external data gathering for marketing strategy."""
from __future__ import annotations

from typing import Any

from agent_core.research.tavily_client import tavily_search_multi
from agent_core.research.metaso_client import metaso_search_multi
from agent_core.research.camoufox_client import camoufox_search


def _build_queries(brief_data: dict[str, Any]) -> list[str]:
    """Generate targeted research queries from brief data."""
    brand = brief_data.get("brand", "")
    product = brief_data.get("product", "")
    industry = brief_data.get("industry", "")
    theme = brief_data.get("theme", "")
    goal = brief_data.get("goal", "")
    key_messages = brief_data.get("key_messages", []) or []

    queries = []

    # Brand + product positioning
    if brand and product:
        queries.append(f"{brand} {product} 营销案例 品牌传播策略")
    elif brand:
        queries.append(f"{brand} 社交营销 2024 2025 案例")

    # Industry + theme trend
    if industry and theme:
        queries.append(f"{industry} {theme} KOL营销 趋势 案例")
    elif industry:
        queries.append(f"{industry} 小红书 抖音 投放策略 案例")
    elif theme:
        queries.append(f"{theme} 品牌合作 营销案例")

    # Goal-oriented research
    if goal and industry:
        queries.append(f"{industry} {goal} 营销策略 成功案例")

    # Key message / product concept
    if key_messages:
        concept = key_messages[0]
        queries.append(f"{concept} 竞品分析 差异化营销")

    # Prevent empty queries
    if not queries:
        queries.append(f"{brand or product or '品牌营销'} 社交传播 策略案例")

    return queries[:4]  # Limit to avoid excessive API calls


def _build_platform_queries(brief_data: dict[str, Any]) -> list[dict[str, str]]:
    """Build platform-specific camoufox queries."""
    brand = brief_data.get("brand", "")
    product = brief_data.get("product", "")
    industry = brief_data.get("industry", "")
    theme = brief_data.get("theme", "")

    queries = []
    base = f"{brand} {product}".strip() or industry or ""
    if base:
        queries.append({"q": base, "platform": "google"})
        if theme:
            queries.append({"q": f"{base} {theme}", "platform": "google"})
    return queries[:2]


def research_for_strategy(brief_data: dict[str, Any]) -> dict[str, Any]:
    """Gather external research for a marketing strategy.

    Returns a structured report with findings from Tavily and Camoufox.
    """
    queries = _build_queries(brief_data)
    platform_queries = _build_platform_queries(brief_data)

    # Tavily + Metaso web search (parallel-ish sequential calls)
    tavily_results = tavily_search_multi(queries, max_results=5, search_depth="basic")
    metaso_results = metaso_search_multi(queries, max_results=5, scope="webpage", include_summary=True)

    # Camoufox platform scraping (slower, so keep minimal)
    camoufox_results = []
    for pq in platform_queries:
        result = camoufox_search(pq["q"], platform=pq["platform"])
        camoufox_results.append(result)

    # Aggregate snippets into a research digest
    sources = []
    combined_snippets = []

    for tr in tavily_results:
        if tr.get("error"):
            combined_snippets.append(f"[Tavily: {tr['query']}] Error: {tr['error']}")
            continue
        answer = tr.get("answer")
        if answer:
            combined_snippets.append(f"【Tavily: {tr['query']}】\n{answer}")
        for r in tr.get("results", []):
            title = r.get("title", "")
            content = r.get("content", "")
            url = r.get("url", "")
            if content:
                combined_snippets.append(f"- {title}: {content}")
                sources.append({"title": title, "url": url, "source": "tavily"})

    for mr in metaso_results:
        if mr.get("error"):
            combined_snippets.append(f"[Metaso: {mr['query']}] Error: {mr['error']}")
            continue
        answer = mr.get("answer")
        if answer:
            combined_snippets.append(f"【Metaso: {mr['query']}】\n{answer}")
        for r in mr.get("results", []):
            title = r.get("title", "")
            content = r.get("content", "")
            url = r.get("url", "")
            if content:
                combined_snippets.append(f"- {title}: {content}")
                sources.append({"title": title, "url": url, "source": "metaso"})

    for cr in camoufox_results:
        if cr.get("error"):
            combined_snippets.append(f"[Camoufox {cr.get('engine','')}]: {cr['error']}")
            continue
        snippets = cr.get("snippets", [])
        if snippets:
            combined_snippets.append(f"【{cr.get('engine')} 搜索结果: {cr.get('query')}】\n" + "\n".join(snippets[:5]))
            sources.append({"title": cr.get("title", ""), "url": cr.get("url", ""), "source": f"camoufox/{cr.get('engine')}"})

    return {
        "tavily_results": tavily_results,
        "metaso_results": metaso_results,
        "camoufox_results": camoufox_results,
        "combined_snippets": combined_snippets,
        "sources": sources,
        "applied_skills": [
            "tavily-web-search",
            "metaso-cn-search",
            "camoufox-platform-scraping",
            "research-anything",
            "competitive-analysis",
        ],
    }


class StrategyResearcher:
    """Orchestrator for strategy research."""

    def research(self, brief_data: dict[str, Any]) -> dict[str, Any]:
        return research_for_strategy(brief_data)
