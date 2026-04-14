"""Tavily search client for AI-powered web research."""
from __future__ import annotations

import os
from typing import Any


def _get_api_key() -> str | None:
    return os.getenv("TAVILY_API_KEY")


def tavily_search(query: str, max_results: int = 5, search_depth: str = "basic") -> dict[str, Any]:
    """Synchronously search the web using Tavily.

    Args:
        query: Search query string.
        max_results: Number of results to return (default 5).
        search_depth: "basic" or "advanced".

    Returns:
        dict with keys: query, results[list], answer(str|None), error(str|None)
    """
    api_key = _get_api_key()
    if not api_key or api_key.startswith("your_"):
        return {
            "query": query,
            "results": [],
            "answer": None,
            "error": "TAVILY_API_KEY not configured. Please set it in .env or environment variables.",
        }

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=True,
            include_raw_content=False,
        )
        return {
            "query": query,
            "results": response.get("results", []),
            "answer": response.get("answer"),
            "error": None,
        }
    except Exception as e:
        return {
            "query": query,
            "results": [],
            "answer": None,
            "error": f"Tavily search failed: {e}",
        }


def tavily_search_multi(queries: list[str], max_results: int = 5, search_depth: str = "basic") -> list[dict[str, Any]]:
    """Run multiple Tavily searches sequentially.

    Returns a list of result dicts, one per query.
    """
    return [tavily_search(q, max_results=max_results, search_depth=search_depth) for q in queries]


class TavilyClient:
    """Thin wrapper around Tavily for strategy research."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or _get_api_key()

    def search(self, query: str, max_results: int = 5, search_depth: str = "basic") -> dict[str, Any]:
        if not self.api_key:
            return {
                "query": query,
                "results": [],
                "answer": None,
                "error": "TAVILY_API_KEY not configured.",
            }
        return tavily_search(query, max_results=max_results, search_depth=search_depth)

    def search_multi(self, queries: list[str], max_results: int = 5, search_depth: str = "basic") -> list[dict[str, Any]]:
        return [self.search(q, max_results=max_results, search_depth=search_depth) for q in queries]
