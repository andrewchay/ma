"""Case playbook library extracted from internal marketing cases.

This module turns reusable case learnings into structured playbooks that can
be reused by strategy, matching, and creative modules.
"""
from __future__ import annotations

from typing import Any


PETPHONE_CASE = {
    "name": "Petphone1127",
    "core_patterns": [
        "痛点锚点（分离焦虑/安全焦虑）驱动内容主线",
        "事件锚点（如CES）集中爆发，缩短预热链路",
        "双阵营KOL（前线现场组 + Homebase场景组）并行叙事",
        "认知-信任-订阅的全链路转化",
    ],
    "channel_roles": {
        "TikTok/Instagram": "情绪化短视频与话题扩散",
        "YouTube": "深度评测与科技背书",
        "PR/Tech Media": "权威信任建设",
    },
    "content_pillars": [
        {
            "name": "痛点解决型",
            "objective": "把核心焦虑映射到产品功能",
            "formats": ["真实案例复盘", "前后对比", "UGC共鸣故事"],
        },
        {
            "name": "功能科普型",
            "objective": "降低技术理解门槛与决策门槛",
            "formats": ["技术拆解", "图解说明", "专家背书"],
        },
        {
            "name": "事件现场型",
            "objective": "借重大节点放大前沿感和讨论度",
            "formats": ["展会现场vlog", "新品首发", "KOL联动挑战"],
        },
    ],
}


MIND_SOCIAL_CASE = {
    "name": "Mind social",
    "core_patterns": [
        "多平台 content pillar 管理（科普/赛事moment/FOP植入/线下活动）",
        "按 TOP/MID/BTM 分层配置达人池与预算",
        "Creator Brief Book 标准化下发，提高执行一致性",
        "过程追踪表驱动（提报-合作-发布-复盘）",
    ],
    "channel_roles": {
        "小红书": "种草与生活方式内容沉淀",
        "抖音": "高频触达与热点扩散",
        "B站": "深度内容与专业解释",
    },
    "content_pillars": [
        {
            "name": "科普认知",
            "objective": "解释科学原理和产品机制",
            "formats": ["机制拆解", "专业测评", "图文知识卡"],
        },
        {
            "name": "赛事Moment",
            "objective": "借赛事/热点提升相关性与传播效率",
            "formats": ["事件快评", "热点借势短视频", "运动员素材二创"],
        },
        {
            "name": "场景化植入",
            "objective": "把产品放进真实场景降低理解成本",
            "formats": ["vlog", "开箱体验", "日常场景脚本"],
        },
        {
            "name": "线下活动联动",
            "objective": "放大品牌在真实世界的存在感",
            "formats": ["活动探店", "快闪记录", "现场采访"],
        },
    ],
}


def _build_tracker_fields(case_names: list[str]) -> list[str]:
    base_fields = [
        "提报日期",
        "主平台",
        "Tier(TOP/MID/BTM)",
        "KOL名称",
        "内容规划",
        "是否合作",
        "品牌反馈",
        "主页链接",
        "互动中位数",
        "档期",
        "分发平台",
        "备注",
    ]
    if "Petphone1127" in case_names:
        base_fields.extend(["事件节点", "阵营(frontline/homebase)", "是否放大投流"])
    return base_fields


def derive_case_playbook(brief_data: dict[str, Any]) -> dict[str, Any]:
    """Derive a practical playbook from the two reference cases."""
    industry = str(brief_data.get("industry", "") or "")
    goal = str(brief_data.get("goal", "") or "")
    is_overseas = bool(brief_data.get("is_overseas", False))

    selected = []
    if is_overseas or industry in {"3C", "通用"}:
        selected.append(PETPHONE_CASE)
    if not is_overseas or industry in {"时尚", "美妆", "快消"} or "种草" in goal:
        selected.append(MIND_SOCIAL_CASE)
    if not selected:
        selected = [MIND_SOCIAL_CASE]

    case_names = [c["name"] for c in selected]

    channel_roles = {}
    content_pillars = []
    insights = []
    for case in selected:
        channel_roles.update(case["channel_roles"])
        content_pillars.extend(case["content_pillars"])
        insights.extend(case["core_patterns"])

    return {
        "selected_cases": case_names,
        "insights": insights[:8],
        "channel_roles": channel_roles,
        "content_pillars": content_pillars[:6],
        "tier_model": {
            "TOP": "品牌背书与破圈曝光",
            "MID": "效率转化与核心ROI",
            "BTM": "高频铺量与UGC口碑",
        },
        "execution_tracker_fields": _build_tracker_fields(case_names),
        "creator_brief_sections": [
            "Campaign opportunity",
            "Product science / mechanism",
            "Content direction by pillar",
            "Must include / forbidden",
            "Delivery format and timeline",
        ],
    }

