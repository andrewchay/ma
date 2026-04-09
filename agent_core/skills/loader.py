"""Skill file loader."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=64)
def load_skill_text(path: str, max_chars: int = 1800) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
        compact = " ".join(text.split())
        return compact[:max_chars]
    except Exception:
        return ""

