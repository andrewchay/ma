"""Skill registry for MA runtime prompt augmentation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SkillSpec:
    key: str
    path: str
    description: str
    modes: tuple[str, ...] = ("strategy", "kol", "outreach", "creative")
    industries: tuple[str, ...] = ()
    platforms: tuple[str, ...] = ()


SKILLS: dict[str, SkillSpec] = {
    "agency-agents": SkillSpec(
        key="agency-agents",
        path="/Users/chaihao/.agents/skills/agency-agents/SKILL.md",
        description="Specialized role activation and agency workflow patterns.",
    ),
    "competitive-analysis": SkillSpec(
        key="competitive-analysis",
        path="/Users/chaihao/.agents/skills/competitive-analysis/SKILL.md",
        description="Competitor positioning and angle analysis.",
        modes=("strategy",),
    ),
    "content-marketing": SkillSpec(
        key="content-marketing",
        path="/Users/chaihao/.agents/skills/content-marketing/SKILL.md",
        description="Content strategy and distribution logic.",
        modes=("strategy", "creative"),
    ),
    "brand-storytelling": SkillSpec(
        key="brand-storytelling",
        path="/Users/chaihao/.agents/skills/brand-storytelling/SKILL.md",
        description="Narrative design and emotional storytelling.",
        modes=("strategy", "creative"),
    ),
    "marketing-xiaohongshu-specialist": SkillSpec(
        key="marketing-xiaohongshu-specialist",
        path="/Users/chaihao/LLM/agency-agents/marketing/marketing-xiaohongshu-specialist.md",
        description="Xiaohongshu specialist playbook.",
        modes=("strategy", "kol", "creative"),
        platforms=("小红书",),
    ),
    "marketing-douyin-strategist": SkillSpec(
        key="marketing-douyin-strategist",
        path="/Users/chaihao/LLM/agency-agents/marketing/marketing-douyin-strategist.md",
        description="Douyin strategy specialist.",
        modes=("strategy", "kol", "creative"),
        platforms=("抖音",),
    ),
    "sales-outbound-strategist": SkillSpec(
        key="sales-outbound-strategist",
        path="/Users/chaihao/LLM/agency-agents/sales/sales-outbound-strategist.md",
        description="Outreach and negotiation specialist.",
        modes=("outreach",),
    ),
}


ALIASES: dict[str, str] = {
    "agency": "agency-agents",
    "xhs": "marketing-xiaohongshu-specialist",
    "douyin": "marketing-douyin-strategist",
    "outbound": "sales-outbound-strategist",
}


def resolve_skill_key(name: str) -> Optional[str]:
    if not name:
        return None
    raw = name.strip()
    if raw in SKILLS:
        return raw
    lower = raw.lower()
    if lower in SKILLS:
        return lower
    if lower in ALIASES:
        return ALIASES[lower]
    return None

