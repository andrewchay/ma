"""ConnectBot - 智能建联与协作代理 (LLM Powered)"""
from __future__ import annotations

import json
from typing import Any, Optional

from agent_core.skills import resolve_skill_context


def generate_outreach_with_llm(
    kol_name: str,
    kol_profile: dict,
    brand: str,
    brand_intro: str,
    product: str,
    platform: str,
    style: str,
    cooperation_type: str,
    budget_range: str,
    skills: list[str] | None = None,
) -> dict[str, str]:
    """使用LLM生成个性化建联话术"""
    from agent_core.llm import get_llm_client
    
    llm = get_llm_client()
    skill_ctx = resolve_skill_context(
        "outreach",
        {"industry": kol_profile.get("category", "通用"), "preferred_platforms": [platform]},
        requested_skills=skills,
    )
    
    style_prompts = {
        "formal": "正式商务风格，专业严谨",
        "casual": "轻松友好风格，像朋友聊天",
        "professional": "专业但不失亲切，平衡商务与友好",
    }
    
    system_prompt = f"""你是一个资深的KOL商务合作专家。请根据提供的KOL信息和品牌信息，撰写一封个性化的合作邀约。

风格要求：{style_prompts.get(style, style_prompts["professional"])}

请以JSON格式返回：
{{
    "subject": "邮件/私信主题",
    "greeting": "称呼和开场",
    "body": "正文内容",
    "value_proposition": "合作价值说明",
    "cooperation_details": "合作内容简述",
    "next_steps": "下一步行动建议",
    "closing": "结尾礼貌用语",
    "full_message": "完整的消息内容"
}}""" + skill_ctx.get("skill_prompt_addon", "")

    prompt = f"""请为以下品牌撰写给KOL的合作邀约：

KOL信息：
- 名称：{kol_name}
- 平台：{platform}
- 粉丝量：{kol_profile.get('followers', '未知')}
- 内容领域：{kol_profile.get('category', '未知')}
- 近期内容：{', '.join(kol_profile.get('recent_posts', []))}
- 合作历史：{', '.join(kol_profile.get('brand_history', []))}

品牌信息：
- 品牌：{brand}
- 品牌介绍：{brand_intro}
- 产品：{product}
- 合作形式：{cooperation_type}
- 预算范围：{budget_range}

请撰写个性化的合作邀约。"""

    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            result.setdefault("applied_skills", skill_ctx.get("applied_skills", []))
            return result
    except Exception:
        pass
    
    fallback = _template_outreach(kol_name, brand, platform, style)
    fallback["applied_skills"] = skill_ctx.get("applied_skills", [])
    return fallback


def _template_outreach(kol_name: str, brand: str, platform: str, style: str) -> dict[str, str]:
    """模板备用话术"""
    subjects = {
        "formal": f"【品牌合作邀约】{brand} × {kol_name}",
        "casual": f"嘿，{kol_name}！有个超棒的合作想聊聊 ✨",
        "professional": f"商业合作邀请 | {brand} × {kol_name}",
    }
    
    bodies = {
        "formal": f"{kol_name}，您好！\n\n我是{brand}的市场负责人。我们关注到您在{platform}上的优质内容，希望探讨合作机会。",
        "casual": f"嗨 {kol_name}！\n\n我是{brand}的，经常刷到你的内容，超级喜欢！想邀请你一起合作～",
        "professional": f"{kol_name}，您好\n\n我是{brand}市场部。经内部评估，我们认为您的内容影响力与我们的项目高度匹配。",
    }
    
    return {
        "subject": subjects.get(style, subjects["professional"]),
        "greeting": f"{kol_name}，您好",
        "body": bodies.get(style, bodies["professional"]),
        "full_message": bodies.get(style, bodies["professional"]),
    }


def generate_follow_up_with_llm(
    kol_name: str,
    brand: str,
    days_since: int,
    previous_message: str,
    kol_response: Optional[str],
) -> dict[str, str]:
    """使用LLM生成智能跟进话术"""
    from agent_core.llm import get_llm_client
    
    llm = get_llm_client()
    
    system_prompt = """你是一个资深的商务跟进专家。请根据跟进的时间点和KOL的反馈状态，撰写合适的跟进消息。

请以JSON格式返回：
{
    "tone": "语气类型(gentle/moderate/final)",
    "subject": "主题",
    "message": "跟进消息内容",
    "psychology": "这条消息的心理学原理",
    "call_to_action": "明确的下一步行动号召"
}"""

    response_info = f"KOL上次回复：{kol_response}" if kol_response else "KOL尚未回复"
    
    prompt = f"""请撰写跟进消息：

KOL：{kol_name}
品牌：{brand}
距离上次联系：{days_since}天
上次消息：{previous_message[:100]}...
{response_info}

请撰写合适的跟进消息。"""

    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            return result
    except Exception:
        pass
    
    return _template_follow_up(kol_name, days_since)


def _template_follow_up(kol_name: str, days_since: int) -> dict[str, str]:
    """模板备用跟进"""
    if days_since < 3:
        tone = "gentle"
        message = f"{kol_name}，您好！想跟进一下之前的合作邀请，不知道您是否有看到呢？期待您的回复～"
    elif days_since < 7:
        tone = "moderate"
        message = f"{kol_name}您好，一周前发送的合作邀请，可能您比较忙没有注意到。我们的项目时间比较紧，如果您感兴趣的话希望可以尽快沟通。"
    else:
        tone = "final"
        message = f"{kol_name}您好，这是我们关于本次合作的最后一次跟进。如果暂时没有时间合作，我们也完全理解，期待下次有机会合作！"
    
    return {
        "tone": tone,
        "message": message,
        "psychology": "基于规则的跟进",
        "call_to_action": "请回复是否感兴趣",
    }


def generate_negotiation_strategy_with_llm(
    kol_price: float,
    budget: float,
    kol_data: dict,
    brand_value: str,
) -> dict[str, Any]:
    """使用LLM生成谈判策略"""
    from agent_core.llm import get_llm_client
    
    llm = get_llm_client()
    
    system_prompt = """你是一个资深的商务谈判专家。请基于提供的报价信息和KOL数据，制定最优的谈判策略。

请以JSON格式返回：
{
    "price_assessment": "价格评估",
    "market_comparison": "市场行情对比",
    "suggested_offer": "建议报价",
    "offer_rationale": "报价理由",
    "negotiation_tactics": ["策略1", "策略2", "策略3"],
    "value_propositions": ["可提供的价值1", "可提供的价值2"],
    "deal_breakers": ["底线条件1", "底线条件2"],
    "best_alternative": "如果谈不拢的替代方案",
    "success_probability": "成功概率评估"
}"""

    prompt = f"""请制定谈判策略：

KOL报价：{kol_price}万
品牌预算：{budget}万
KOL数据：{json.dumps(kol_data, ensure_ascii=False)}
品牌价值：{brand_value}

请制定最优谈判策略。"""

    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            return result
    except Exception:
        pass
    
    return _template_negotiation(kol_price, budget, kol_data)


def _template_negotiation(kol_price: float, budget: float, kol_data: dict) -> dict[str, Any]:
    """模板备用谈判策略"""
    engagement_val = kol_data.get("engagement", "0%")
    if isinstance(engagement_val, (int, float)):
        engagement = float(engagement_val)
    else:
        engagement = float(str(engagement_val).rstrip("%"))
    
    if kol_price > budget:
        suggested = budget * 0.9
    else:
        suggested = kol_price * 0.85
    
    return {
        "price_assessment": "报价" + ("偏高" if kol_price > budget else "合理"),
        "suggested_offer": round(suggested, 2),
        "offer_rationale": "基于预算和市场行情的合理报价",
        "negotiation_tactics": ["强调长期合作", "提供产品置换", "展示品牌实力"],
    }


def generate_contract_clauses(
    cooperation_type: str = "content",
) -> dict[str, list[str]]:
    """生成合同条款建议"""
    base_clauses = {
        "must_have": [
            "内容发布前需经品牌方审核确认",
            "发布后需保留至少30天不删除/隐藏",
            "需标注'广告'或'合作'等合规声明",
            "保证内容为原创，不侵犯第三方权益",
        ],
        "content_specific": {
            "content": [
                "需包含品牌指定关键词：XXX",
                "产品露出时长不少于XX秒",
                "需包含购买链接/引导语",
                "允许品牌方二次传播使用",
            ],
            "live": [
                "直播时长不少于XX小时",
                "需讲解产品核心卖点",
                "需配合促销活动节奏",
                "直播回放保留权利",
            ],
            "event": [
                "需按时到场参加活动",
                "需配合现场拍摄安排",
                "活动结束后XX小时内发布相关内容",
            ],
        },
        "payment": [
            "预付XX%，发布后付尾款",
            "需提供发票",
            "付款周期：收到发票后XX个工作日",
        ],
        "breach": [
            "未按时发布：扣除XX%费用",
            "内容不符合约定：需修改或退还费用",
            "数据造假：有权终止合作并追回费用",
        ],
    }
    
    return {
        "must_have": base_clauses["must_have"],
        "content_requirements": base_clauses["content_specific"].get(cooperation_type, []),
        "payment_terms": base_clauses["payment"],
        "breach_terms": base_clauses["breach"],
    }


# Tool executors
def outreach_generate_executor(payload: str) -> str:
    """生成建联话术执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        args = {}
    
    result = generate_outreach_with_llm(
        kol_name=args.get("kol_name", "KOL"),
        kol_profile=args.get("kol_profile", {}),
        brand=args.get("brand", "品牌"),
        brand_intro=args.get("brand_intro", "优质品牌"),
        product=args.get("product", "产品"),
        platform=args.get("platform", "小红书"),
        style=args.get("style", "professional"),
        cooperation_type=args.get("cooperation_type", "内容合作"),
        budget_range=args.get("budget_range", "面议"),
        skills=[s.strip() for s in str(args.get("skills", "")).split(",") if s.strip()] if args.get("skills") else None,
    )
    
    return json.dumps(result, indent=2, ensure_ascii=False)


def follow_up_generate_executor(payload: str) -> str:
    """生成跟进话术执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        args = {}
    
    result = generate_follow_up_with_llm(
        kol_name=args.get("kol_name", "KOL"),
        brand=args.get("brand", "品牌"),
        days_since=args.get("days_since", 3),
        previous_message=args.get("previous_message", ""),
        kol_response=args.get("kol_response"),
    )
    
    return json.dumps(result, indent=2, ensure_ascii=False)


def negotiation_advice_executor(payload: str) -> str:
    """谈判建议执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        args = {}
    
    result = generate_negotiation_strategy_with_llm(
        kol_price=args.get("kol_price", 0),
        budget=args.get("budget", 0),
        kol_data={
            "engagement": args.get("kol_engagement", 0),
            "followers": args.get("kol_followers", 0),
        },
        brand_value=args.get("brand_value", ""),
    )
    
    return json.dumps(result, indent=2, ensure_ascii=False)


def contract_clauses_executor(payload: str) -> str:
    """合同条款建议执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        args = {}
    
    result = generate_contract_clauses(
        cooperation_type=args.get("cooperation_type", "content"),
    )
    
    return json.dumps(result, indent=2, ensure_ascii=False)
