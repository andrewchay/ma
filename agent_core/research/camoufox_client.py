"""Camoufox browser client for platform-specific scraping."""
from __future__ import annotations

import time
from typing import Any


def _fetch_page(url: str, wait_seconds: int = 3) -> dict[str, Any]:
    """Fetch a page using camoufox anti-detect browser.

    Returns dict with keys: url, title, text_snippet, html_length, error
    """
    try:
        from camoufox.sync_api import CamoufoxSession
    except ImportError as e:
        return {
            "url": url,
            "title": "",
            "text_snippet": "",
            "html_length": 0,
            "error": f"camoufox not installed: {e}",
        }

    try:
        with CamoufoxSession() as fox:
            page = fox.new_page()
            page.goto(url, timeout=30000)
            # Wait for dynamic content
            time.sleep(wait_seconds)
            title = page.title() or ""
            text = page.inner_text("body")[:3000]
            html = page.content()
            page.close()
            return {
                "url": url,
                "title": title,
                "text_snippet": text,
                "html_length": len(html),
                "error": None,
            }
    except Exception as e:
        return {
            "url": url,
            "title": "",
            "text_snippet": "",
            "html_length": 0,
            "error": f"camoufox fetch failed: {e}",
        }


def camoufox_search_google(query: str) -> dict[str, Any]:
    """Search Google via camoufox and return top result snippets."""
    encoded = query.replace(" ", "+")
    url = f"https://www.google.com/search?q={encoded}&num=10"
    result = _fetch_page(url, wait_seconds=3)
    if result["error"]:
        return result
    # Simple extraction: split by common result separators
    text = result["text_snippet"]
    # Heuristic cleanup
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 20]
    return {
        "engine": "google",
        "query": query,
        "url": url,
        "title": result["title"],
        "snippets": lines[:10],
        "error": None,
    }


def camoufox_search_xiaohongshu(query: str) -> dict[str, Any]:
    """Attempt to search Xiaohongshu via camoufox.

    Note: Xiaohongshu often requires login for search results.
    """
    encoded = query.replace(" ", "%20")
    url = f"https://www.xiaohongshu.com/search_result?keyword={encoded}&source=web_search_result_notes"
    result = _fetch_page(url, wait_seconds=5)
    if result["error"]:
        return result
    text = result["text_snippet"]
    # If we detect login wall, report it
    if "登录" in text or "手机号" in text or "验证码" in text:
        return {
            "engine": "xiaohongshu",
            "query": query,
            "url": url,
            "title": result["title"],
            "snippets": [],
            "error": "Xiaohongshu requires login to view search results. Please import cookies or use an authenticated session.",
        }
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 10]
    return {
        "engine": "xiaohongshu",
        "query": query,
        "url": url,
        "title": result["title"],
        "snippets": lines[:15],
        "error": None,
    }


def camoufox_search_douyin(query: str) -> dict[str, Any]:
    """Attempt to search Douyin via camoufox.

    Note: Douyin may block or require verification for automated access.
    """
    encoded = query.replace(" ", "%20")
    url = f"https://www.douyin.com/search/{encoded}?type=video"
    result = _fetch_page(url, wait_seconds=5)
    if result["error"]:
        return result
    text = result["text_snippet"]
    if "验证" in text or "验证码" in text or "滑动" in text:
        return {
            "engine": "douyin",
            "query": query,
            "url": url,
            "title": result["title"],
            "snippets": [],
            "error": "Douyin triggered verification challenge. Automated access blocked.",
            "recommendation": "Use Douyin StarMap API (星图) for official KOL data instead.",
        }
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 10]
    return {
        "engine": "douyin",
        "query": query,
        "url": url,
        "title": result["title"],
        "snippets": lines[:15],
        "error": None,
    }


def camoufox_search(query: str, platform: str = "google") -> dict[str, Any]:
    """Unified camoufox search dispatcher."""
    if platform == "xiaohongshu":
        return camoufox_search_xiaohongshu(query)
    if platform == "douyin":
        return camoufox_search_douyin(query)
    return camoufox_search_google(query)


class CamoufoxClient:
    """Thin wrapper around camoufox for strategy research."""

    def search(self, query: str, platform: str = "google") -> dict[str, Any]:
        return camoufox_search(query, platform=platform)

    def fetch(self, url: str, wait_seconds: int = 3) -> dict[str, Any]:
        return _fetch_page(url, wait_seconds=wait_seconds)
