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
    "marketing-tiktok-strategist": SkillSpec(
        key="marketing-tiktok-strategist",
        path="/Users/chaihao/LLM/agency-agents/marketing/marketing-tiktok-strategist.md",
        description="TikTok viral content, algorithm optimization, and Gen Z community building.",
        modes=("strategy", "kol", "creative"),
        platforms=("TikTok", "抖音国际版"),
    ),
    "marketing-instagram-curator": SkillSpec(
        key="marketing-instagram-curator",
        path="/Users/chaihao/LLM/agency-agents/marketing/marketing-instagram-curator.md",
        description="Instagram visual storytelling, Reels, and social commerce.",
        modes=("strategy", "kol", "creative"),
        platforms=("Instagram", "IG"),
    ),
    "marketing-twitter-engager": SkillSpec(
        key="marketing-twitter-engager",
        path="/Users/chaihao/LLM/agency-agents/marketing/marketing-twitter-engager.md",
        description="Twitter/X real-time engagement, thought leadership, and community-driven growth.",
        modes=("strategy", "kol", "creative"),
        platforms=("Twitter", "X", "推特"),
    ),
    "marketing-reddit-community-builder": SkillSpec(
        key="marketing-reddit-community-builder",
        path="/Users/chaihao/LLM/agency-agents/marketing/marketing-reddit-community-builder.md",
        description="Reddit authentic community engagement and value-driven brand building.",
        modes=("strategy", "kol", "creative"),
        platforms=("Reddit", "红迪"),
    ),
    "marketing-video-optimization-specialist": SkillSpec(
        key="marketing-video-optimization-specialist",
        path="/Users/chaihao/LLM/agency-agents/marketing/marketing-video-optimization-specialist.md",
        description="YouTube algorithm optimization, audience retention, thumbnail strategy, and video SEO.",
        modes=("strategy", "kol", "creative"),
        platforms=("YouTube", "油管", "YouTube Shorts"),
    ),
    "marketing-linkedin-content-creator": SkillSpec(
        key="marketing-linkedin-content-creator",
        path="/Users/chaihao/LLM/agency-agents/marketing/marketing-linkedin-content-creator.md",
        description="LinkedIn thought leadership, personal brand building, and B2B professional content.",
        modes=("strategy", "kol", "creative"),
        platforms=("LinkedIn", "领英"),
    ),
    "paid-media-paid-social-strategist": SkillSpec(
        key="paid-media-paid-social-strategist",
        path="/Users/chaihao/LLM/agency-agents/paid-media/paid-media-paid-social-strategist.md",
        description="Cross-platform paid social ads (Meta/Facebook/Instagram, TikTok, LinkedIn, X, Snapchat) with full-funnel architecture.",
        modes=("strategy", "creative"),
        platforms=("Meta", "Facebook", "Instagram", "TikTok Ads", "Snapchat", "Pinterest", "X Ads"),
    ),
    "paid-media-ppc-strategist": SkillSpec(
        key="paid-media-ppc-strategist",
        path="/Users/chaihao/LLM/agency-agents/paid-media/paid-media-ppc-strategist.md",
        description="Google Ads, Microsoft Ads, Amazon Ads — search, shopping, Performance Max, and scale strategy.",
        modes=("strategy", "creative"),
        platforms=("Google", "Google Ads", "YouTube Ads", "Microsoft Ads", "Bing", "Amazon Ads"),
    ),
}


ALIASES: dict[str, str] = {
    "agency": "agency-agents",
    "xhs": "marketing-xiaohongshu-specialist",
    "douyin": "marketing-douyin-strategist",
    "outbound": "sales-outbound-strategist",
    "tiktok": "marketing-tiktok-strategist",
    "instagram": "marketing-instagram-curator",
    "twitter": "marketing-twitter-engager",
    "reddit": "marketing-reddit-community-builder",
    "youtube": "marketing-video-optimization-specialist",
    "linkedin": "marketing-linkedin-content-creator",
    "meta-ads": "paid-media-paid-social-strategist",
    "facebook-ads": "paid-media-paid-social-strategist",
    "paid-social": "paid-media-paid-social-strategist",
    "google-ads": "paid-media-ppc-strategist",
    "ppc": "paid-media-ppc-strategist",
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

