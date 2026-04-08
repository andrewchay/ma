"""CreativePilot - 创意内容指导助手 (LLM Powered)"""
from __future__ import annotations

import json
import re
from typing import Any

from agent_core.case_playbook import derive_case_playbook
from agent_core.industry_templates import get_industry_template, normalize_industry


PLATFORM_GUIDELINES = {
    "小红书": {
        "title_formulas": [
            "数字+结果+方法：30天瘦10斤，我是这样做的",
            "痛点+解决方案：毛孔粗大怎么办？亲测有效的3个方法",
            "对比+反差：月薪3千 vs 月薪3万的妆容区别",
            "悬念+揭秘：大牌柜姐不会告诉你的省钱秘籍",
        ],
        "content_structure": [
            "开头：痛点共鸣/结果预告（3行内）",
            "正文：分点说明，每点配emoji",
            "结尾：总结+互动提问",
        ],
        "image_tips": [
            "封面图要美观吸睛，建议3:4竖图",
            "内页图要信息密度高，可拼接",
            "配色统一，符合品牌调性",
            "文字不要太多，关键信息突出",
        ],
        "hashtag_strategy": "3-5个精准标签 + 1-2个热门标签 + 品牌标签",
        "optimal_length": "300-800字",
        "forbidden_words": ["最", "第一", "国家级", "纯天然", "100%"],
    },
    "抖音": {
        "hook_templates": [
            "你知道吗？...",
            "千万不要...",
            "我花了X万才学到的...",
            "为什么你...",
            "挑战...",
        ],
        "video_structure": [
            "0-3秒：黄金3秒抓眼球",
            "3-15秒：核心内容输出",
            "15-30秒：详细展开",
            "30-60秒：结尾+CTA",
        ],
        "shooting_tips": [
            "光线充足，画面清晰",
            "背景简洁不杂乱",
            "收音清晰，可用领夹麦",
            "镜头稳定，可用云台",
        ],
        "bgm_tips": "使用平台热门音乐，增强算法推荐",
        "optimal_length": "15-60秒",
        "caption_tips": "字幕要大而清晰，关键词突出",
    },
    "微博": {
        "content_types": ["图文", "视频", "长微博", "投票"],
        "hashtag_strategy": "1个主话题 + 2-3个相关话题",
        "timing_tips": "早8-9点，午12-13点，晚8-10点",
        "interaction_tips": "多@相关账号，增加曝光",
        "optimal_length": "100-500字",
    },
    "B站": {
        "video_structure": [
            "0-30秒：开场+内容预告",
            "30秒-3分钟：引入+背景",
            "3-10分钟：核心内容",
            "10-15分钟：总结+升华",
        ],
        "thumbnail_tips": "标题党封面，高对比度配色",
        "title_tips": "包含关键词，适当使用【】强调",
        "bullet_comments": "引导弹幕互动，增加完播率",
        "optimal_length": "5-15分钟",
    },
}


def generate_creative_brief_with_llm(
    brand: str,
    product: str,
    platform: str,
    kol_style: str,
    key_messages: list[str],
    must_include: list[str],
    forbidden: list[str],
    target_audience: str,
    campaign_goal: str,
    industry: str = "通用",
) -> dict[str, Any]:
    """使用LLM生成创意Brief"""
    from agent_core.llm import get_llm_client
    
    llm = get_llm_client()
    normalized_industry = normalize_industry(industry)
    industry_template = get_industry_template(
        normalized_industry,
        platform in {"TikTok", "Instagram", "YouTube", "Facebook"},
    )
    final_must_include = list(dict.fromkeys((must_include or []) + industry_template.get("creative_must_include", [])))
    final_forbidden = list(dict.fromkeys((forbidden or []) + industry_template.get("creative_forbidden", [])))
    case_playbook = derive_case_playbook({
        "brand": brand,
        "industry": normalized_industry,
        "goal": campaign_goal,
        "is_overseas": platform in {"TikTok", "Instagram", "YouTube", "Facebook"},
    })
    
    system_prompt = """你是一个资深的内容创意总监。请基于品牌需求和平台特性，生成一份详细的KOL内容创作Brief。

请以JSON格式返回：
{
    "project_overview": "项目概述",
    "content_strategy": {
        "core_message": "核心传播信息",
        "content_angle": "内容切入角度",
        "emotional_appeal": "情感诉求点",
        "story_framework": "故事框架建议"
    },
    "creative_elements": {
        "visual_direction": "视觉指导",
        "tone_voice": "语气语调",
        "key_phrases": ["关键词1", "关键词2"],
        "hashtag_strategy": "标签策略"
    },
    "execution_guide": {
        "opening_hook": "开头抓人技巧",
        "content_flow": "内容流程建议",
        "cta": "行动号召设计",
        "engagement_tactics": "互动引导技巧"
    },
    "platform_specific": "平台特殊要求",
    "brand_integration": "品牌植入建议",
    "compliance_notes": "合规注意事项",
    "success_criteria": "成功标准",
    "reference_examples": "参考案例方向"
}"""

    prompt = f"""请为以下品牌生成创意Brief：

品牌：{brand}
产品：{product}
平台：{platform}
KOL风格：{kol_style}
关键信息：{', '.join(key_messages)}
必须包含：{', '.join(final_must_include)}
禁止事项：{', '.join(final_forbidden)}
目标受众：{target_audience}
活动目标：{campaign_goal}

请生成详细的创意Brief。"""

    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            # 合并平台指南
            guidelines = PLATFORM_GUIDELINES.get(platform, {})
            return {
                "project_info": {
                    "brand": brand,
                    "product": product,
                    "platform": platform,
                },
                "llm_brief": result,
                "platform_guidelines": guidelines,
                "case_content_pillars": case_playbook.get("content_pillars", []),
                "creator_brief_book": _build_creator_brief_book(
                    brand=brand,
                    product=product,
                    platform=platform,
                    campaign_goal=campaign_goal,
                    key_messages=key_messages,
                    must_include=final_must_include,
                    forbidden=final_forbidden,
                ),
                "industry_template": {
                    "industry": normalized_industry,
                    "core_objective": industry_template.get("core_objective"),
                    "content_pillars": industry_template.get("content_pillars", []),
                    "must_track_metrics": industry_template.get("must_track_metrics", []),
                },
                "compliance": {
                    "disclosure": "需标注'广告'或'合作'",
                    "forbidden_words": guidelines.get("forbidden_words", []),
                },
            }
    except Exception:
        pass
    
    return _template_brief(
        brand,
        product,
        platform,
        kol_style,
        key_messages,
        final_must_include,
        final_forbidden,
        normalized_industry,
    )


def _template_brief(
    brand,
    product,
    platform,
    kol_style,
    key_messages,
    must_include,
    forbidden,
    industry: str = "通用",
):
    """模板备用Brief"""
    guidelines = PLATFORM_GUIDELINES.get(platform, {})
    industry_template = get_industry_template(
        normalize_industry(industry),
        platform in {"TikTok", "Instagram", "YouTube", "Facebook"},
    )
    case_playbook = derive_case_playbook({
        "brand": brand,
        "industry": normalize_industry(industry),
        "goal": "种草转化",
        "is_overseas": platform in {"TikTok", "Instagram", "YouTube", "Facebook"},
    })
    
    return {
        "project_info": {
            "brand": brand,
            "product": product,
            "platform": platform,
        },
        "content_requirements": {
            "key_messages": key_messages,
            "must_include": must_include,
            "forbidden": forbidden,
            "tone": kol_style,
        },
        "platform_guidelines": guidelines,
        "creative_direction": {
            "title_suggestions": guidelines.get("title_formulas", [])[:3],
            "content_structure": guidelines.get("content_structure", []),
            "visual_tips": guidelines.get("image_tips", []) or guidelines.get("shooting_tips", []),
        },
        "case_content_pillars": case_playbook.get("content_pillars", []),
        "creator_brief_book": _build_creator_brief_book(
            brand=brand,
            product=product,
            platform=platform,
            campaign_goal="种草转化",
            key_messages=key_messages,
            must_include=must_include,
            forbidden=forbidden,
        ),
        "industry_template": {
            "industry": industry_template.get("industry"),
            "core_objective": industry_template.get("core_objective"),
            "content_pillars": industry_template.get("content_pillars", []),
            "must_track_metrics": industry_template.get("must_track_metrics", []),
        },
        "hashtags": {
            "required": [f"#{brand}"],
            "recommended": [f"#{product}", "#好物分享", "#测评"],
        },
        "compliance": {
            "disclosure": "需标注'广告'或'合作'",
            "forbidden_words": guidelines.get("forbidden_words", []),
        },
    }


def generate_content_with_llm(
    template_type: str,
    platform: str,
    brand: str,
    product: str,
    key_points: list[str],
    style: str,
) -> dict[str, str]:
    """使用LLM生成内容"""
    from agent_core.llm import get_llm_client
    
    llm = get_llm_client()
    
    system_prompt = f"""你是一个资深的{platform}内容创作者。请根据要求生成一篇优质的内容。

请以JSON格式返回：
{{
    "title": "标题",
    "content": "正文内容",
    "hashtags": ["标签1", "标签2"],
    "posting_tips": "发布建议",
    "engagement_prediction": "互动预测"
}}"""

    prompt = f"""请生成一篇{platform}的{template_type}内容：

品牌：{brand}
产品：{product}
核心卖点：{', '.join(key_points)}
风格：{style}

请生成完整的内容。"""

    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            return result
    except Exception:
        pass
    
    return {
        "title": f"{brand}{product}真实测评",
        "content": f"今天来分享一下{brand}的{product}...",
        "hashtags": [f"#{brand}", f"#{product}", "#好物分享"],
        "note": "LLM生成失败，返回模板内容",
    }


def review_content_with_llm(
    content: str,
    brand: str,
    platform: str,
    requirements: dict[str, Any],
) -> dict[str, Any]:
    """使用LLM审核内容"""
    from agent_core.llm import get_llm_client
    
    llm = get_llm_client()
    
    system_prompt = """你是一个严格的内容审核专家。请基于品牌要求和平台规范，对内容进行全面审核。

请以JSON格式返回：
{
    "overall_score": 85,
    "passed": true,
    "brand_alignment": {"score": 90, "feedback": "品牌契合度反馈"},
    "compliance_check": {"score": 85, "issues": []},
    "content_quality": {"score": 80, "strengths": [], "weaknesses": []},
    "platform_optimization": {"score": 85, "suggestions": []},
    "critical_issues": ["严重问题1"],
    "warnings": ["警告1"],
    "improvement_suggestions": ["建议1", "建议2"],
    "estimated_performance": "预估表现"
}"""

    prompt = f"""请审核以下内容：

平台：{platform}
品牌：{brand}
内容：{content[:500]}...

要求：
- 必须包含：{requirements.get('must_include', [])}
- 禁止：{requirements.get('forbidden', [])}
- 调性：{requirements.get('tone', '真实分享')}

请进行全面审核。"""

    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            return result
    except Exception:
        pass
    
    return _template_review(content, brand, platform)


def _template_review(content: str, brand: str, platform: str) -> dict[str, Any]:
    """模板备用审核"""
    issues = []
    warnings = []
    
    # 基础检查
    if brand not in content:
        issues.append("内容未提及品牌名")
    
    platform_guidelines = PLATFORM_GUIDELINES.get(platform, {})
    forbidden = platform_guidelines.get("forbidden_words", [])
    
    for word in forbidden:
        if word in content:
            issues.append(f"包含禁用词: {word}")
    
    # 合规检查
    if platform in ["小红书", "抖音", "微博"]:
        if not any(m in content for m in ["广告", "合作", "推广"]):
            warnings.append("建议添加'广告'或'合作'声明")
    
    score = max(0, 100 - len(issues) * 20 - len(warnings) * 10)
    
    return {
        "overall_score": score,
        "passed": len(issues) == 0,
        "critical_issues": issues,
        "warnings": warnings,
        "improvement_suggestions": ["增加emoji提升可读性", "添加CTA引导互动"],
    }


def _build_creator_brief_book(
    brand: str,
    product: str,
    platform: str,
    campaign_goal: str,
    key_messages: list[str],
    must_include: list[str],
    forbidden: list[str],
) -> dict[str, Any]:
    """Case-inspired creator brief structure."""
    return {
        "campaign_opportunity": (
            f"围绕{campaign_goal}构建内容叙事，用真实场景触发用户共鸣，再过渡到功能认知。"
        ),
        "product_truth": f"{brand}{product}的核心机制与使用价值需可视化讲清楚，避免空泛表述。",
        "content_direction": [
            "第一层：痛点/机会洞察切入",
            "第二层：功能机制解释",
            "第三层：场景化体验与结果呈现",
        ],
        "deliverables": {
            "platform": platform,
            "must_include": must_include or ["产品露出", "场景化演示"],
            "key_messages": key_messages or [f"{brand}{product}核心卖点"],
            "forbidden": forbidden,
        },
        "quality_bar": [
            "开头3秒给出冲突或问题",
            "中段提供具体证据或机制说明",
            "结尾给出可执行行动建议或互动引导",
        ],
    }


# Tool executors
def creative_brief_executor(payload: str) -> str:
    """生成创意Brief执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        args = {}
    
    result = generate_creative_brief_with_llm(
        brand=args.get("brand", "品牌"),
        product=args.get("product", "产品"),
        platform=args.get("platform", "小红书"),
        kol_style=args.get("kol_style", "真实分享"),
        key_messages=args.get("key_messages", []),
        must_include=args.get("must_include", []),
        forbidden=args.get("forbidden", []),
        target_audience=args.get("target_audience", "年轻女性"),
        campaign_goal=args.get("campaign_goal", "种草"),
        industry=args.get("industry", "通用"),
    )
    
    return json.dumps(result, indent=2, ensure_ascii=False)


def content_template_executor(payload: str) -> str:
    """生成内容模板执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        args = {}
    
    result = generate_content_with_llm(
        template_type=args.get("template_type", "product_review"),
        platform=args.get("platform", "小红书"),
        brand=args.get("brand", "品牌"),
        product=args.get("product", "产品"),
        key_points=args.get("key_points", []),
        style=args.get("style", "真实分享"),
    )
    
    return json.dumps(result, indent=2, ensure_ascii=False)


def content_review_executor(payload: str) -> str:
    """内容审核执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        args = {}
    
    result = review_content_with_llm(
        content=args.get("content", ""),
        brand=args.get("brand", ""),
        platform=args.get("platform", "小红书"),
        requirements=args.get("requirements", {}),
    )
    
    return json.dumps(result, indent=2, ensure_ascii=False)
