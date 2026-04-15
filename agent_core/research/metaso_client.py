"""Metaso (秘塔AI搜索) client for Chinese web research."""
from __future__ import annotations

import os
from typing import Any

import requests


def _get_api_key() -> str | None:
    key = os.getenv("METASO_API_KEY", "")
    if not key or key.startswith("your_"):
        return None
    return key


def metaso_search(
    query: str,
    max_results: int = 5,
    scope: str = "webpage",
    include_summary: bool = True,
) -> dict[str, Any]:
    """Search using Metaso AI Search API (v1).

    Args:
        query: Search query string.
        max_results: Number of results to return.
        scope: Search scope - "webpage" | "scholar" | "doc" | "image" | "video" | "podcast"
        include_summary: Whether to include AI-generated summary.

    Returns:
        dict with keys: query, results[list], answer(str|None), error(str|None)
    """
    api_key = _get_api_key()
    if not api_key:
        return {
            "query": query,
            "results": [],
            "answer": None,
            "error": "METASO_API_KEY not configured. Please set it in .env or environment variables.",
        }

    payload = {
        "q": query,
        "scope": scope,
        "includeSummary": include_summary,
        "size": max_results,
        "includeRawContent": False,
        "conciseSnippet": True,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        resp = requests.post(
            "https://metaso.cn/api/v1/search",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        return {
            "query": query,
            "results": [],
            "answer": None,
            "error": f"Metaso request failed: {e}",
        }
    except Exception as e:
        return {
            "query": query,
            "results": [],
            "answer": None,
            "error": f"Metaso response parse failed: {e}",
        }

    # Handle API-level errors
    if data.get("errCode"):
        return {
            "query": query,
            "results": [],
            "answer": None,
            "error": f"Metaso API error {data.get('errCode')}: {data.get('errMsg', 'Unknown error')}",
        }

    # Try to extract results from various possible response shapes
    results: list[dict[str, Any]] = []
    answer: str | None = None

    # Metaso v1 search returns flat dict with keys like webpages, images, videos
    if isinstance(data, dict):
        answer = data.get("summary") or data.get("answer")
        raw_results = (
            data.get("webpages")
            or data.get("results")
            or data.get("data")
            or []
        )
    elif isinstance(data, list):
        raw_results = data
    else:
        raw_results = []

    for item in raw_results:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("name", "")
        url = item.get("link") or item.get("url") or ""
        content = item.get("snippet") or item.get("content") or item.get("summary", "")
        if title or content:
            results.append({
                "title": str(title),
                "url": str(url),
                "content": str(content),
            })

    # If no structured results but we have a flat text response, treat it as answer
    if not results and not answer and isinstance(data, dict) and "text" in data:
        answer = data.get("text")

    return {
        "query": query,
        "results": results,
        "answer": answer,
        "error": None,
    }


def metaso_search_multi(
    queries: list[str],
    max_results: int = 5,
    scope: str = "webpage",
    include_summary: bool = True,
) -> list[dict[str, Any]]:
    """Run multiple Metaso searches sequentially.

    Returns a list of result dicts, one per query.
    """
    return [
        metaso_search(q, max_results=max_results, scope=scope, include_summary=include_summary)
        for q in queries
    ]


class MetasoClient:
    """Thin wrapper around Metaso for strategy research."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or _get_api_key()

    def search(
        self,
        query: str,
        max_results: int = 5,
        scope: str = "webpage",
        include_summary: bool = True,
    ) -> dict[str, Any]:
        if not self.api_key:
            return {
                "query": query,
                "results": [],
                "answer": None,
                "error": "METASO_API_KEY not configured.",
            }
        return metaso_search(
            query,
            max_results=max_results,
            scope=scope,
            include_summary=include_summary,
        )

    def search_multi(
        self,
        queries: list[str],
        max_results: int = 5,
        scope: str = "webpage",
        include_summary: bool = True,
    ) -> list[dict[str, Any]]:
        return [
            self.search(q, max_results=max_results, scope=scope, include_summary=include_summary)
            for q in queries
        ]
