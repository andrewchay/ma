"""Skill router for selecting and injecting skill context into prompts."""
from __future__ import annotations

from typing import Any

from agent_core.skills.loader import load_skill_text
from agent_core.skills.registry import SKILLS, resolve_skill_key


def _default_candidates(mode: str, brief_data: dict[str, Any]) -> list[str]:
    platform_text = " ".join(brief_data.get("preferred_platforms", []) or [])
    industry = str(brief_data.get("industry", "") or "")
    is_overseas = bool(brief_data.get("is_overseas", False))
    candidates = ["agency-agents"]

    if mode == "strategy":
        candidates.extend(["competitive-analysis", "content-marketing", "brand-storytelling"])
    if mode == "creative":
        candidates.extend(["brand-storytelling", "content-marketing"])
    if mode == "outreach":
        candidates.append("sales-outbound-strategist")

    # Domestic platforms
    if "小红书" in platform_text:
        candidates.append("marketing-xiaohongshu-specialist")
    if "抖音" in platform_text:
        candidates.append("marketing-douyin-strategist")

    # Overseas platforms
    if is_overseas or "TikTok" in platform_text or "抖音国际版" in platform_text:
        candidates.append("marketing-tiktok-strategist")
    if is_overseas or "Instagram" in platform_text or "IG" in platform_text:
        candidates.append("marketing-instagram-curator")
    if is_overseas or "YouTube" in platform_text or "Shorts" in platform_text:
        candidates.append("marketing-video-optimization-specialist")
    if "Twitter" in platform_text or "X" in platform_text or "推特" in platform_text:
        candidates.append("marketing-twitter-engager")
    if "Reddit" in platform_text or "红迪" in platform_text:
        candidates.append("marketing-reddit-community-builder")
    if "LinkedIn" in platform_text or "领英" in platform_text:
        candidates.append("marketing-linkedin-content-creator")

    # Overseas catch-all: if explicitly overseas but no specific platform matched, add core ones
    if is_overseas and not any(
        p in platform_text for p in ("TikTok", "Instagram", "YouTube", "Twitter", "X", "Reddit", "LinkedIn")
    ):
        candidates.extend([
            "marketing-tiktok-strategist",
            "marketing-instagram-curator",
            "marketing-video-optimization-specialist",
        ])

    if "运动鞋服" in industry:
        candidates.append("brand-storytelling")
    return list(dict.fromkeys(candidates))


def resolve_skill_context(
    mode: str,
    brief_data: dict[str, Any],
    requested_skills: list[str] | None = None,
) -> dict[str, Any]:
    """Return selected skills and prompt addon."""
    selected: list[str] = []
    missing: list[str] = []
    prompt_blocks: list[str] = []

    names = requested_skills or _default_candidates(mode, brief_data)
    for name in names:
        key = resolve_skill_key(name)
        if not key or key not in SKILLS:
            missing.append(name)
            continue
        spec = SKILLS[key]
        if mode not in spec.modes:
            continue
        text = load_skill_text(spec.path)
        if not text:
            missing.append(key)
            continue
        selected.append(key)
        prompt_blocks.append(f"[Skill:{key}] {text}")

    addon = ""
    if prompt_blocks:
        addon = "\n\n你必须遵循以下技能策略要点：\n" + "\n".join(prompt_blocks)
    return {"applied_skills": selected, "missing_skills": missing, "skill_prompt_addon": addon}

