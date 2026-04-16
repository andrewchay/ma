"""StrategyIQ - 策略理解与生成引擎 (LLM Powered)"""
from __future__ import annotations

import json
from typing import Any

from agent_core.case_playbook import derive_case_playbook
from agent_core.industry_templates import get_industry_template, normalize_industry
from agent_core.models import BriefParseResult
from agent_core.research import research_for_strategy
from agent_core.skills import resolve_skill_context


# LLM prompt JSON schema for generate_strategy
_STRATEGY_JSON_SCHEMA = """{
    "market_strategy_framework": {
        "user_research": {
            "profile_dimensions": ["年龄", "性别", "收入", "城市层级", "社会关系"],
            "behavior_habits": ["行为习惯1", "行为习惯2"],
            "scenario_insights": ["使用场景痛点1", "使用场景痛点2"],
            "emotional_insights": ["社会关系/情绪洞察1", "洞察2"]
        },
        "competitor_analysis": {
            "recent_campaign_patterns": ["同质化传播角度1", "角度2"],
            "communication_choice": ["功能型利益点", "情感型利益点"],
            "opportunity_gaps": ["可差异化空白1", "空白2"]
        },
        "product_features": {
            "unique_attributes": ["独特属性1", "独特属性2"],
            "functional_benefits": ["功能利益点1", "功能利益点2"],
            "best_fit_scenarios": ["最佳使用场景1", "场景2"]
        },
        "triple_positioning_options": [
            {"name": "定位方向A", "logic": "用户洞察×竞品空白×产品利益点", "risk": "潜在风险", "fit_goal": "适合目标"}
        ]
    },
    "audience_research": {
        "segments": [{"name": "人群", "profile": "画像", "habits": ["习惯"], "product_linked_lifestyles": ["关联生活方式"], "core_tensions": ["矛盾痛点"]}],
        "insights": ["洞察1", "洞察2"]
    },
    "competitor_analysis": {
        "peer_brands": [{"name": "竞品", "angles": ["传播角度"], "formats": ["内容形式"], "what_works": ["有效点"], "what_to_avoid": ["风险点"]}],
        "white_space": ["可占领空白点"]
    },
    "communication_angle": {
        "functional_benefits": ["功能利益点"],
        "emotional_values": ["情绪价值"],
        "hero_message": "一句话主张",
        "creative_hook": "创意钩子"
    },
    "platform_strategy": [
        {"name": "平台名", "goal": "目标", "content_format": "内容形式", "priority": "优先级", "reasoning": "选择理由"}
    ],
    "kol_strategy": {
        "head_kol": {
            "count": "建议数量",
            "purpose": "作用",
            "budget_ratio": 0.4,
            "recommended_kols": [{"name": "KOL名称", "followers": "粉丝量", "platform": "平台", "style": "风格", "estimated_price": "预估报价"}]
        },
        "waist_kol": {
            "count": "建议数量",
            "purpose": "作用",
            "budget_ratio": 0.45,
            "recommended_kols": [{"name": "KOL名称", "followers": "粉丝量", "platform": "平台", "style": "风格", "estimated_price": "预估报价"}]
        },
        "koc": {
            "count": "建议数量",
            "purpose": "作用",
            "budget_ratio": 0.15,
            "selection_criteria": ["筛选标准1", "筛选标准2"]
        },
        "execution_tips": ["执行建议1", "执行建议2"]
    },
    "content_strategy": {
        "core_themes": ["主题1", "主题2"],
        "content_tone": "调性描述",
        "hashtag_strategy": "标签策略"
    },
    "budget_allocation": {"平台名": 40, ...},
    "kpis": {"primary": "主要KPI", "secondary": "次要KPI", "tertiary": "第三KPI"},
    "timeline": [
        {"phase": "阶段名", "duration": "时长", "activities": ["活动1", "活动2"]}
    ],
    "execution_guide": {
        "phases": [{"phase": "阶段", "duration": "时长", "key_actions": ["行动1"]}],
        "risk_warnings": ["风险1", "风险2"],
        "success_factors": ["要素1", "要素2"]
    },
    "case_playbook": {
        "selected_cases": ["案例1", "案例2"],
        "channel_roles": {"平台": "角色"},
        "content_pillars": [{"name": "支柱名", "objective": "目标", "formats": ["形式"]}],
        "execution_tracker_fields": ["字段1", "字段2"]
    },
    "applied_skills": ["skill1", "skill2"],
    "key_insights": ["核心洞察1", "核心洞察2"]
}"""


def parse_brief(brief_text: str) -> dict[str, Any]:
    """使用LLM解析客户brief，提取关键信息"""
    from agent_core.llm import get_llm_client

    llm = get_llm_client()

    system_prompt = f"""你是一个专业的社交营销brief解析专家。请从用户输入中提取以下信息，并以JSON格式返回：
{_STRATEGY_JSON_SCHEMA}

如果某些信息未提及，使用"未提及"或合理推断。
注意：
1. 如果文中提到"XX系列产品"，product 应该填写完整的系列名称
2. goal 如果是借大型赛事/节日热度提升认知，请填写"产品认知"
3. theme 请提取具体的热点事件或主题方向"""

    prompt = f"请解析以下营销brief：\n\n{brief_text}\n\n请提取关键信息并以JSON格式返回。"
    
    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result and not _is_weak_parse_result(result):
            # 用模型做字段补齐和校验，确保后向兼容
            return BriefParseResult.model_validate(result).model_dump()
        # Fallback to rule-based parsing
        return _rule_based_parse(brief_text)
    except Exception as e:
        return _rule_based_parse(brief_text)


def _is_weak_parse_result(result: dict[str, Any]) -> bool:
    """Detect low-quality parse outputs and trigger rule-based fallback."""
    brand = str(result.get("brand", "") or "")
    industry = str(result.get("industry", "") or "")
    key_messages = result.get("key_messages", []) or []
    preferred_platforms = result.get("preferred_platforms", []) or []

    weak_brand = brand in {"", "未提及", "未知"}
    weak_industry = industry in {"", "通用", "未提及", "未知"}
    weak_detail = len(key_messages) == 0 and len(preferred_platforms) == 0
    return weak_brand and weak_industry and weak_detail


def _rule_based_parse(brief_text: str) -> dict[str, Any]:
    """基于规则的备用解析"""
    import re
    
    text_lower = brief_text.lower()
    
    # 品牌检测 - 先匹配已知品牌，再尝试提取
    brand = "未提及"
    lower_text = brief_text.lower()
    
    # 1. 特殊品牌识别（优先）
    known_brands = {
        'anker': 'Anker',
        'nike': 'Nike',
        '耐克': 'Nike',
        '花西子': '花西子',
        '完美日记': '完美日记',
        '小米': '小米',
        '华为': '华为',
        '苹果': '苹果',
        'iphone': 'iPhone',
        'mac': 'Mac',
        'dior': 'Dior',
        'chanel': 'Chanel',
    }
    for kb_lower, kb_original in known_brands.items():
        if kb_lower in lower_text:
            brand = kb_original
            break
    
    # 2. 如果已知品牌没匹配到，尝试从文本提取
    if brand == "未提及":
        # 匹配模式：句子开头的大写英文品牌
        match = re.search(r'^([A-Z][a-zA-Z0-9]{1,10})\b', brief_text.strip())
        if match:
            potential = match.group(1)
            # 排除常见词
            common_words = ['The', 'This', 'That', 'There', 'These', 'Those', 'What', 'When', 'Where', 'Who', 'Why', 'How', 'I', 'We', 'You', 'They', 'Need', 'Want', 'Have', 'Do', 'Make', 'Create']
            if potential not in common_words:
                brand = potential
    
    # 3. 提取目标受众
    audience = "未提及"
    audience_patterns = [
        r'针对(.+?)(?:用户|人群|消费者|受众|市场)',
        r'目标(.+?)(?:用户|人群|消费者|受众)',
        r'(.+?)(?:用户|人群)(?:群体|为主)',
    ]
    for pattern in audience_patterns:
        match = re.search(pattern, brief_text)
        if match:
            audience = match.group(1).strip()[:10]  # 限制长度
            break
    
    # 行业检测（采用加权匹配，避免"宠物科技"被"3C/科技"误识别）
    industry = _detect_industry(brief_text)
    
    # Anker通常是3C/充电品牌
    if brand.lower() == "anker":
        industry = "3C"
    
    # 产品检测
    product = "未提及"
    if "aero-fit" in text_lower:
        product = "Aero-Fit系列产品"
    else:
        product_patterns = [
            r'(?:新品|新|推出|发布)(.+?)(?:上市|发布|上线|系列)',
            r'(.+?)(?:系列|款产品)',
        ]
        for pattern in product_patterns:
            match = re.search(pattern, brief_text)
            if match:
                potential = match.group(1).strip()
                if len(potential) > 1 and len(potential) < 20:
                    product = potential
                    break
    
    # 目标检测
    goal = "品牌曝光"
    if any(kw in text_lower for kw in ["种草", "转化", "购买"]):
        goal = "种草转化"
    elif any(kw in text_lower for kw in ["销售", "卖货", "成交", "gmv"]):
        goal = "销售转化"
    elif any(kw in text_lower for kw in ["认知度", "产品认知", "了解", "知道"]):
        goal = "产品认知"
    elif any(kw in text_lower for kw in ["曝光", "知名度", "声量", "品牌"]):
        goal = "品牌曝光"
    
    # 预算检测
    budget_match = re.search(r'(\d+)\s*万', brief_text)
    if budget_match:
        budget_num = int(budget_match.group(1))
    else:
        budget_num = None  # 未提及，不设置默认值
    
    if budget_num:
        if budget_num >= 100:
            budget = "高"
        elif budget_num >= 50:
            budget = "中高"
        elif budget_num >= 20:
            budget = "中等"
        else:
            budget = "低"
    else:
        budget = "未提及"
        budget_num = "待商议"
    
    # 目标受众检测
    audience = "未提及"
    audience_patterns = [
        r'针对(.+?)(?:用户|人群|消费者|受众)',
        r'目标(.+?)(?:用户|人群|消费者|受众)',
        r'(.+?)(?:用户|人群)群体',
    ]
    for pattern in audience_patterns:
        match = re.search(pattern, brief_text)
        if match:
            audience = match.group(1).strip()
            break
    if audience == "未提及":
        if any(k in brief_text for k in ["世界杯", "国家队", "球迷", "足球"]):
            audience = "18-40岁足球/世界杯关注人群，偏运动潮流消费者"
    
    # 海外市场检测
    overseas_markers = ["海外", "国外", "美国", "欧洲", "日本", "韩国", "东南亚", "全球", "跨境", "出海", "tiktok", "youtube", "instagram", "facebook", "twitter"]
    is_overseas = any(marker in text_lower for marker in overseas_markers)
    
    # 传播关键信息抽取（轻量规则）
    key_messages = []
    if "Aero-Fit" in brief_text or "aero-fit" in text_lower:
        key_messages.append("Aero-Fit系列产品卖点")
    if "世界杯" in brief_text:
        key_messages.append("世界杯主题传播")
    if "国家队" in brief_text or "球服" in brief_text:
        key_messages.append("国家队球服灵感演绎")
    if "名场面" in brief_text:
        key_messages.append("往届世界杯名场面再创作")

    preferred_platforms = []
    if any(k in brief_text for k in ["世界杯", "足球", "运动", "球服"]):
        preferred_platforms = ["抖音", "B站", "小红书"]

    constraints = []
    if "好莱坞风格" in brief_text:
        constraints.append("内容风格偏好莱坞叙事与视听质感")
    if "名场面" in brief_text:
        constraints.append("允许演绎往届世界杯名场面")
    constraints_text = "；".join(constraints) if constraints else "未提及"

    timeline = "未提及"
    if "即将" in brief_text:
        timeline = "建议在1-2个月内完成预热-爆发-长尾执行"

    # 主题/热点检测
    theme = "未提及"
    if "世界杯" in brief_text:
        theme = "世界杯主题传播"
    elif "春节" in brief_text or "年货" in brief_text:
        theme = "春节营销"
    elif "奥运" in brief_text:
        theme = "奥运会主题传播"

    return BriefParseResult.model_validate({
        "brand": brand,
        "product": product,
        "industry": normalize_industry(industry),
        "goal": goal,
        "budget": budget,
        "budget_amount": budget_num,
        "timeline": timeline,
        "target_audience": audience,
        "is_overseas": is_overseas,
        "key_messages": key_messages,
        "theme": theme,
        "preferred_platforms": preferred_platforms,
        "constraints": constraints_text,
    }).model_dump()


def _detect_industry(brief_text: str) -> str:
    """Detect industry with weighted keyword scoring."""
    text = (brief_text or "").lower()

    industry_keywords = {
        "宠物科技": ["宠物", "狗", "猫", "pet", "tracker", "collar", "分离焦虑", "项圈"],
        "运动鞋服": ["运动", "跑步", "篮球", "训练", "球鞋", "sneaker", "赛前", "赛事", "世界杯", "国家队", "球服", "足球", "aero-fit"],
        "美妆": ["美妆", "护肤", "化妆品", "口红", "粉底", "眼影"],
        "母婴": ["母婴", "婴儿", "宝宝", "孕妇", "育儿"],
        "时尚": ["时尚", "服装", "穿搭", "潮流", "配饰"],
        "快消": ["快消", "食品", "饮料", "日用品"],
        "3C": ["数码", "手机", "电脑", "科技", "智能", "电子", "充电", "配件"],
    }
    priority = {
        "宠物科技": 3.0,
        "运动鞋服": 2.0,
        "美妆": 1.5,
        "母婴": 1.5,
        "时尚": 1.2,
        "快消": 1.0,
        "3C": 0.8,  # 泛词较多，降低优先级
    }

    best = ("通用", 0.0)
    for industry, keywords in industry_keywords.items():
        hit_count = sum(1 for kw in keywords if kw in text)
        score = hit_count * priority.get(industry, 1.0)
        if score > best[1]:
            best = (industry, score)

    return best[0]


def generate_strategy(brief_data: dict[str, Any]) -> dict[str, Any]:
    """使用LLM生成营销策略"""
    from agent_core.llm import get_llm_client
    
    llm = get_llm_client()
    
    requested_skills = brief_data.get("skills", []) if isinstance(brief_data.get("skills", []), list) else []
    skill_ctx = resolve_skill_context("strategy", brief_data, requested_skills=requested_skills)

    # 执行真实调研
    research_report = research_for_strategy(brief_data)
    research_snippets = "\n\n".join(research_report.get("combined_snippets", []))
    research_sources = research_report.get("sources", [])

    _research_section = research_snippets if research_snippets else "（本次调研未获取到外部数据，请基于 brief 信息和你的专业知识生成策略。）"

    system_prompt = (
        f"你是一个资深的社交营销策略专家。请基于提供的brief信息和以下真实调研数据，生成一份专业的营销策略方案。\n\n"
        f"【真实调研数据 - 必须引用并标注来源】\n"
        f"以下是来自 Tavily 搜索引擎和 camoufox 浏览器抓取的最新调研摘要：\n\n"
        f"{_research_section}\n\n"
        "要求：\n"
        "- 竞品分析中的具体品牌、传播角度、有效点必须优先基于调研数据\n"
        "- 若调研提供了参考案例，请在 case_playbook.selected_cases 中明确列出品牌名\n"
        "- 每个关键事实判断请尽量引用调研来源；若来源不足，明确标注为\"行业常识推断\"\n"
        "- 在 key_insights 中至少列出 3 条基于调研或方法论推导出的核心洞察\n\n"
        "【注入方法论框架 - 必须遵循】\n\n"
        "1. 竞品分析框架 (competitive-analysis)\n"
        "   - 不要只对比直接竞品的功能，必须识别\"竞争替代方案\"（包括现状、人工 workaround、传统解决方式）\n"
        "   - 用 April Dunford 原则：先定义客户不买你的时候会做什么，再定位差异化空白\n"
        "   - 竞品传播分析要具体：主角度、内容范式、有效点、风险点、可差异化空白\n\n"
        "2. 内容营销框架 (content-marketing)\n"
        '   - 内容必须是 "painkiller" 而非 "vitamin"：解决具体焦虑/痛点，而非提供泛泛信息\n'
        "   - 追求 content-market fit：内容格式要匹配平台特性和创作者优势\n"
        "   - 一致性优先：建立可持续的内容支柱（pillars），再追求爆款\n\n"
        "3. 品牌叙事框架 (brand-storytelling)\n"
        '   - 品牌要 "lead a movement"，不只是解决问题\n'
        '   - 找到 "five-second moment"：用户认知/情绪转变的关键瞬间\n'
        "   - 顾客是英雄（Luke），品牌是导师（Obi-Wan），产品是光剑\n"
        "   - Hero Message 要一句话可复述，Creative Hook 要有情绪张力\n\n"
        "4. 定价与价值感知 (pricing-strategy)\n"
        '   - 若涉及产品定价/ tier 传播，价格锚点应在"竞争替代方案"和"感知价值"之间\n'
        "   - 用 Good-Better-Best 思维设计内容层级：入门种草 → 深度转化 → 品牌忠诚\n\n"
        "5. 结构化分析 (mckinsey-consultant)\n"
        "   - 使用 MECE 原则拆解市场：用户分层不重叠、平台选择有互斥标准\n"
        "   - 研究先行 → 假设驱动 → 证据支撑：每个策略建议都要有 brief 信息或逻辑推导作为依据\n"
        "   - 在 key_insights 中明确列出 3-5 条核心洞察\n\n"
        "6. 问题定义 (problem-definition)\n"
        "   - 在动笔策略前，先在 market_strategy_framework 里清晰定义：\n"
        "     * 这个问题是什么 / 不是什么\n"
        "     * 客户真正在对抗的是什么（status quo）\n\n"
        "7. 系统思维 (systems-thinking)\n"
        "   - 识别二阶效应：平台选择如何影响 KOL 生态、内容如何反哺搜索指数、预算分配如何影响 ROI\n"
        "   - 考虑多方利益相关者：品牌、KOL、平台算法、用户社交货币\n\n"
        "8. 研究方法论 (research-anything)\n"
        "   - 用 80/20 规则：聚焦 2-3 个最能产生洞察的方向深入，而非面面俱到\n"
        "   - 每个事实性判断尽量 triangulate：有 brief 信息、行业常识、逻辑推导三者中至少两者支撑\n"
        '   - 明确区分"已知事实"和"合理推断"\n\n'
        + (
            "【海外投放特别要求】\n"
            "   - 平台策略必须优先使用海外主流平台（TikTok、Instagram、YouTube、Twitter/X、Reddit、LinkedIn 等）\n"
            "   - KOL 推荐必须匹配海外创作者生态（按地区、语言、粉丝量级分层）\n"
            "   - 内容角度要考虑跨文化适应性，避免只有中文语境才能理解的梗\n"
            "   - 合规方面需提及 FTC 披露要求、平台社区准则、以及目标市场的广告法规\n\n"
            if brief_data.get("is_overseas", False) else ""
        )
        +
        "【重要要求 - 基于用户反馈迭代】\n"
        "1. 必须包含具体的KOL推荐（头部和腰部都要有具体人选或类型描述）\n"
        "2. 平台策略要有详细的选择理由\n"
        "3. 预算分配要具体到数字\n"
        "4. 时间线要可执行\n"
        "5. 传播策略必须遵循研究先行顺序：\n"
        "   - 先做目标人群研究（产品相关生活习惯、行为洞察、情绪动机）\n"
        "   - 再做竞品传播角度分析（同质化产品如何讲）\n"
        "   - 最后结合产品功能利益点，提出差异化且有情绪价值的传播角度\n\n"
        "请确保策略包含：\n"
        "0. 市场策略分块框架（用户研究、竞品分析、产品特征、三定位发散）\n"
        "1. 目标人群研究（用户分层、生活习惯、产品关联场景、核心痛点）\n"
        "2. 竞品传播分析（竞品主角度、内容范式、可借鉴与可避坑点）\n"
        "3. 差异化传播角度（功能利益点包装 + 情绪价值主张 + 创意表达）\n"
        "4. 平台选择及理由（至少2-3个平台）\n"
        "5. KOL组合策略（必须包含：头部/腰部/KOC的配比、具体推荐名单、预算占比）\n"
        "6. 内容方向建议（核心主题、调性、hashtag策略）\n"
        "7. 预算分配建议（平台维度+KOL维度）\n"
        "8. KPI设定（主要、次要、第三层级）\n"
        "9. 执行时间线（筹备期、预热期、爆发期、长尾期）\n"
        "10. 执行指导（关键节点、风险提醒、成功要素）\n"
        "11. 参考案例打法映射（case_playbook）\n"
        "12. applied_skills 字段必须列出本方案实际应用到的所有技能/方法论名称\n\n"
        "以JSON格式返回：\n"
        + _STRATEGY_JSON_SCHEMA
        + "\n"
        + skill_ctx.get("skill_prompt_addon", "")
    )

    prompt = f"""请为以下品牌制定社交营销策略：

品牌信息：
{json.dumps(brief_data, ensure_ascii=False, indent=2)}

调研来源：
{json.dumps(research_sources, ensure_ascii=False, indent=2)}

请生成完整的营销策略方案。"""

    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            # 为LLM结果补充行业模板，保证下游可稳定消费
            industry = normalize_industry(str(brief_data.get("industry", "通用")))
            industry_template = get_industry_template(industry, bool(brief_data.get("is_overseas", False)))
            result.setdefault("industry_template", {
                "industry": industry_template.get("industry", industry),
                "core_objective": industry_template.get("core_objective"),
                "tier_mix": industry_template.get("tier_mix"),
                "content_pillars": industry_template.get("content_pillars", []),
                "must_track_metrics": industry_template.get("must_track_metrics", []),
                "creative_must_include": industry_template.get("creative_must_include", []),
                "creative_forbidden": industry_template.get("creative_forbidden", []),
            })
            result.setdefault("market_strategy_framework", _build_market_strategy_framework(brief_data))
            result.setdefault("audience_research", _build_audience_research(brief_data))
            result.setdefault("competitor_analysis", _build_competitor_analysis(brief_data))
            result.setdefault("communication_angle", _build_communication_angle(brief_data))
            # Merge applied skills from research + skill context
            base_skills = set(skill_ctx.get("applied_skills", []))
            research_skills = set(research_report.get("applied_skills", []))
            result.setdefault("applied_skills", sorted(base_skills | research_skills))
            # Attach research metadata for downstream transparency
            result.setdefault("research_metadata", {
                "queries_count": len(research_report.get("tavily_results", [])),
                "sources": research_sources,
                "errors": [r.get("error") for r in research_report.get("tavily_results", []) if r.get("error")]
                        + [r.get("error") for r in research_report.get("camoufox_results", []) if r.get("error")],
            })
            return result
        return _rule_based_strategy(brief_data)
    except Exception as e:
        return _rule_based_strategy(brief_data)


def _rule_based_strategy(brief_data: dict[str, Any]) -> dict[str, Any]:
    """基于规则的备用策略生成 - 基于反馈迭代增强"""
    industry = normalize_industry(str(brief_data.get("industry", "通用")))
    budget = brief_data.get("budget", "中等")
    goal = brief_data.get("goal", "品牌曝光")
    is_overseas = brief_data.get("is_overseas", False)
    case_playbook = derive_case_playbook(brief_data)
    industry_template = get_industry_template(industry, is_overseas)
    requested_skills = brief_data.get("skills", []) if isinstance(brief_data.get("skills", []), list) else []
    skill_ctx = resolve_skill_context("strategy", brief_data, requested_skills=requested_skills)

    # 执行备用调研（规则分支也要尝试获取外部数据）
    research_report = research_for_strategy(brief_data)
    research_skills = set(research_report.get("applied_skills", []))

    # 平台推荐
    platform_strategy = _recommend_platforms(industry, goal, budget, is_overseas)
    if industry_template.get("platforms"):
        platform_strategy = []
        for i, p in enumerate(industry_template["platforms"]):
            platform_strategy.append({
                "name": p["name"],
                "goal": p.get("goal", goal),
                "content_format": p.get("content_format", _get_content_format(p["name"])),
                "priority": "高" if i == 0 else "中",
                "reasoning": f"行业模板推荐：{industry}在该平台的典型打法为{p.get('goal', goal)}",
            })
    
    # KOL策略 - 传递industry以获取具体KOL推荐
    kol_strategy = _generate_kol_strategy(budget, goal, industry)
    
    # 内容策略
    content_strategy = _generate_content_strategy(industry, goal)
    template_pillars = industry_template.get("content_pillars", [])
    if template_pillars:
        content_strategy["core_themes"] = list(
            dict.fromkeys(template_pillars + content_strategy.get("core_themes", []))
        )[:6]
    case_pillars = [p.get("name", "") for p in case_playbook.get("content_pillars", []) if p.get("name")]
    if case_pillars:
        content_strategy["core_themes"] = list(dict.fromkeys(case_pillars + content_strategy["core_themes"]))[:6]
    
    # 基于反馈迭代：增加执行指导
    execution_guide = _generate_execution_guide(industry, goal, budget)
    execution_guide["tracker_fields"] = case_playbook.get("execution_tracker_fields", [])
    
    return {
        "market_strategy_framework": _build_market_strategy_framework(brief_data),
        "audience_research": _build_audience_research(brief_data),
        "competitor_analysis": _build_competitor_analysis(brief_data),
        "communication_angle": _build_communication_angle(brief_data),
        "platform_strategy": platform_strategy,
        "kol_strategy": kol_strategy,
        "content_strategy": content_strategy,
        "budget_allocation": _allocate_budget(budget, platform_strategy),
        "kpis": _set_kpis(goal, budget),
        "timeline": _generate_timeline(),
        "execution_guide": execution_guide,  # 新增：执行指导
        "case_playbook": case_playbook,
        "industry_template": {
            "industry": industry_template.get("industry", industry),
            "core_objective": industry_template.get("core_objective"),
            "tier_mix": industry_template.get("tier_mix"),
            "content_pillars": industry_template.get("content_pillars", []),
            "must_track_metrics": industry_template.get("must_track_metrics", []),
            "creative_must_include": industry_template.get("creative_must_include", []),
            "creative_forbidden": industry_template.get("creative_forbidden", []),
        },
        "applied_skills": sorted(set(skill_ctx.get("applied_skills", [])) | research_skills),
        "key_insights": [
            "基于规则生成的策略（已基于用户反馈迭代增强KOL推荐）",
            f"案例映射: {', '.join(case_playbook.get('selected_cases', [])) or '通用方法'}",
            f"针对{industry}行业，推荐{len(kol_strategy.get('head_kol', {}).get('recommended_kols', []))}位头部KOL",
            f"推荐{len(kol_strategy.get('waist_kol', {}).get('recommended_kols', []))}位腰部KOL",
        ],
    }


def _build_market_strategy_framework(brief_data: dict[str, Any]) -> dict[str, Any]:
    """构建市场策略分块框架：用户研究/竞品分析/产品特征/三定位"""
    audience = brief_data.get("target_audience", "未提及")
    key_messages = brief_data.get("key_messages") or ["产品核心卖点"]
    industry = normalize_industry(str(brief_data.get("industry", "通用")))
    goal = str(brief_data.get("goal", "品牌曝光"))
    product_hint = key_messages[0]
    return {
        "user_research": {
            "profile_dimensions": ["年龄", "性别", "收入", "生活城市", "社会关系"],
            "behavior_habits": [
                "高频浏览短视频与图文社区",
                "决策前偏好先看测评与他人使用反馈",
            ],
            "scenario_insights": [
                f"围绕{product_hint}的高频使用场景中，用户最担心“踩坑”和“效果不稳定”",
                "用户在关键决策场景里更依赖真实案例，而不是抽象参数",
            ],
            "emotional_insights": [
                "用户购买不仅是功能选择，也是在表达自我身份和圈层归属",
                "在社交关系中，愿意转发能代表自己价值观的品牌内容",
            ],
            "target_audience_note": audience,
        },
        "competitor_analysis": {
            "recent_campaign_patterns": [
                "同质化竞品常用“功能参数罗列+达人背书”组合",
                "热门内容往往在情绪钩子和场景化表达上更强",
            ],
            "communication_choice": ["功能型利益点", "情感型利益点"],
            "opportunity_gaps": [
                "把功能优势直接翻译到关键时刻的可感知收益",
                "避免空泛价值观，强调“场景证据+情绪共鸣”双线并行",
            ],
        },
        "product_features": {
            "unique_attributes": [product_hint, f"{industry}行业下的差异化产品体验"],
            "functional_benefits": key_messages[:3],
            "best_fit_scenarios": ["通勤/日常高频场景", "社交表达或关键任务场景"],
        },
        "triple_positioning_options": [
            {
                "name": "理性证明型定位",
                "logic": "以用户痛点场景为核心，突出可验证的功能收益并建立信任",
                "risk": "容易被竞品在参数层面同质化跟进",
                "fit_goal": "种草转化/销售转化",
            },
            {
                "name": "情绪共鸣型定位",
                "logic": "借助用户关系与身份表达诉求，放大品牌精神价值",
                "risk": "若脱离产品机制，可能形成空洞叙事",
                "fit_goal": "品牌曝光/口碑传播",
            },
            {
                "name": "双核融合型定位",
                "logic": "先情绪抓人再功能落地，形成“被打动+被说服”闭环",
                "risk": "创意与执行要求高，需要严格内容管控",
                "fit_goal": goal,
            },
        ],
    }


def _build_audience_research(brief_data: dict[str, Any]) -> dict[str, Any]:
    audience = brief_data.get("target_audience", "泛人群")
    product_msg = (brief_data.get("key_messages") or ["产品核心卖点"])[0]
    return {
        "segments": [
            {
                "name": "核心消费人群",
                "profile": audience,
                "habits": ["高频社媒浏览", "关注赛事/趋势内容", "偏好短视频和真实体验内容"],
                "product_linked_lifestyles": ["训练与通勤场景", "社交表达与身份认同"],
                "core_tensions": ["想要专业表现，也在意风格表达", "信息过载下难以判断真实价值"],
            }
        ],
        "insights": [
            f"用户更容易被可感知的真实场景说服，而不是抽象功能描述（{product_msg}需场景化）。",
            "情绪共鸣内容（荣耀、遗憾、逆转）可显著提升记忆点和转发意愿。",
        ],
    }


def _build_competitor_analysis(brief_data: dict[str, Any]) -> dict[str, Any]:
    industry = normalize_industry(str(brief_data.get("industry", "通用")))
    peer = {
        "运动鞋服": ["Nike同类系列", "Adidas赛事主题", "Puma联名运动线"],
        "3C": ["同价位科技竞品A", "同价位科技竞品B"],
        "美妆": ["同品类头部品牌A", "同品类头部品牌B"],
    }
    peers = peer.get(industry, ["同品类竞品A", "同品类竞品B"])
    return {
        "peer_brands": [
            {
                "name": peers[0],
                "angles": ["功能参数导向", "明星/KOL背书"],
                "formats": ["短视频对比", "话题挑战"],
                "what_works": ["利益点清晰", "视觉记忆强"],
                "what_to_avoid": ["同质化口号", "缺少真实场景证据"],
            },
            {
                "name": peers[1],
                "angles": ["生活方式叙事", "情绪化表达"],
                "formats": ["剧情化内容", "UGC二创"],
                "what_works": ["共鸣强", "互动高"],
                "what_to_avoid": ["脱离产品机理", "转化链路弱"],
            },
        ],
        "white_space": [
            "把产品功能利益点和用户真实生活冲突直接绑定",
            "用“名场面再演绎”建立差异化叙事资产",
        ],
    }


def _build_communication_angle(brief_data: dict[str, Any]) -> dict[str, Any]:
    key_messages = brief_data.get("key_messages") or ["产品核心卖点"]
    constraints = str(brief_data.get("constraints", "") or "")
    hollywood = "好莱坞" in constraints
    return {
        "functional_benefits": key_messages[:3],
        "emotional_values": ["热血", "荣耀", "临场专注", "群体认同"],
        "hero_message": "把功能利益点转译成关键时刻可被感知的状态优势。",
        "creative_hook": "好莱坞式叙事镜头重构经典名场面，前半段情绪拉满，后半段产品机制落地。"
        if hollywood
        else "以高情绪冲突场景开场，接产品机制解释，再以群体认同收尾。",
    }


def _recommend_platforms(industry: str, goal: str, budget: str, is_overseas: bool = False) -> list[dict]:
    """推荐平台组合"""
    
    # 海外平台配置
    if is_overseas:
        industry_platforms = {
            "美妆": ["Instagram", "TikTok", "YouTube"],
            "3C": ["YouTube", "Instagram", "TikTok"],
            "快消": ["TikTok", "Instagram", "Facebook"],
            "母婴": ["Instagram", "YouTube", "Facebook"],
            "时尚": ["Instagram", "TikTok", "YouTube"],
        }
        default_platforms = ["TikTok", "Instagram", "YouTube"]
        region = "海外市场"
    else:
        # 国内平台配置
        industry_platforms = {
            "美妆": ["小红书", "抖音", "微博"],
            "3C": ["B站", "抖音", "微博"],
            "快消": ["抖音", "小红书", "微博"],
            "母婴": ["小红书", "抖音", "微信视频号"],
            "时尚": ["小红书", "抖音", "微博"],
        }
        default_platforms = ["抖音", "小红书", "微博"]
        region = "国内市场"
    
    selected = industry_platforms.get(industry, default_platforms)
    
    platforms = []
    for i, platform in enumerate(selected):
        platforms.append({
            "name": platform,
            "goal": goal,
            "content_format": _get_content_format(platform),
            "priority": "高" if i == 0 else "中",
            "reasoning": f"{platform}是{industry}行业在{region}的主要营销阵地",
        })
    
    return platforms


def _get_content_format(platform: str) -> str:
    """获取平台默认内容格式"""
    formats = {
        # 国内平台
        "小红书": "图文笔记",
        "抖音": "短视频",
        "微博": "图文/视频",
        "B站": "中长视频",
        "微信视频号": "短视频/直播",
        # 海外平台
        "Instagram": "图文/Stories/Reels",
        "TikTok": "短视频",
        "YouTube": "长视频/Shorts",
        "Facebook": "图文/视频",
        "Twitter": "图文/视频",
    }
    return formats.get(platform, "图文/视频")


# 示例KOL库（基于反馈迭代添加 - 解决"方案缺少KOL"问题）
SAMPLE_KOL_DATABASE = {
    "美妆": {
        "head": [
            {"name": "李佳琦", "followers": "7000万+", "platform": "抖音", "style": "专业测评", "estimated_price": "80-150万"},
            {"name": "薇娅", "followers": "4000万+", "platform": "淘宝直播", "style": "带货女王", "estimated_price": "50-100万"},
            {"name": "程十安", "followers": "3000万+", "platform": "抖音/B站", "style": "美妆教学", "estimated_price": "30-60万"},
        ],
        "waist": [
            {"name": "美妆博主小美", "followers": "100-300万", "platform": "小红书", "style": "真实分享", "estimated_price": "5-15万"},
            {"name": "护肤达人小雅", "followers": "80-200万", "platform": "抖音", "style": "成分党", "estimated_price": "3-10万"},
            {"name": "彩妆师Leo", "followers": "50-150万", "platform": "B站", "style": "专业教程", "estimated_price": "2-8万"},
        ],
    },
    "3C": {
        "head": [
            {"name": "何同学", "followers": "1200万+", "platform": "B站", "style": "科技人文", "estimated_price": "100-200万"},
            {"name": "老师好我叫何同学", "followers": "1200万+", "platform": "B站/抖音", "style": "创意科技", "estimated_price": "80-150万"},
            {"name": "极客湾", "followers": "500万+", "platform": "B站", "style": "硬核测评", "estimated_price": "30-60万"},
        ],
        "waist": [
            {"name": "数码君", "followers": "100-300万", "platform": "抖音", "style": "产品体验", "estimated_price": "5-15万"},
            {"name": "科技美学", "followers": "200-500万", "platform": "B站", "style": "深度评测", "estimated_price": "10-25万"},
            {"name": "小白测评", "followers": "150-400万", "platform": "B站/抖音", "style": "数据说话", "estimated_price": "8-20万"},
        ],
    },
    "快消": {
        "head": [
            {"name": "papi酱", "followers": "7000万+", "platform": "抖音", "style": "搞笑创意", "estimated_price": "60-120万"},
            {"name": "办公室小野", "followers": "2000万+", "platform": "抖音/YouTube", "style": "创意生活", "estimated_price": "40-80万"},
        ],
        "waist": [
            {"name": "生活家小王", "followers": "80-200万", "platform": "小红书", "style": "生活方式", "estimated_price": "3-10万"},
            {"name": "测评达人", "followers": "50-150万", "platform": "抖音", "style": "产品测评", "estimated_price": "2-8万"},
        ],
    },
    "母婴": {
        "head": [
            {"name": "年糕妈妈", "followers": "3000万+", "platform": "微信/抖音", "style": "育儿专家", "estimated_price": "50-100万"},
            {"name": "崔玉涛", "followers": "1000万+", "platform": "抖音", "style": "权威医生", "estimated_price": "40-80万"},
        ],
        "waist": [
            {"name": "宝妈丽丽", "followers": "50-150万", "platform": "小红书", "style": "真实育儿", "estimated_price": "2-8万"},
            {"name": "奶爸日常", "followers": "30-100万", "platform": "抖音", "style": "亲子互动", "estimated_price": "1-5万"},
        ],
    },
    "通用": {
        "head": [
            {"name": "头部达人A", "followers": "500万+", "platform": "抖音", "style": "综合内容", "estimated_price": "30-60万"},
            {"name": "头部达人B", "followers": "300万+", "platform": "小红书", "style": "生活方式", "estimated_price": "20-40万"},
        ],
        "waist": [
            {"name": "腰部达人A", "followers": "50-150万", "platform": "抖音", "style": "垂直内容", "estimated_price": "3-10万"},
            {"name": "腰部达人B", "followers": "30-100万", "platform": "B站", "style": "深度内容", "estimated_price": "2-8万"},
        ],
    },
}


def _generate_kol_strategy(budget: str, goal: str, industry: str = "通用") -> dict:
    """生成KOL组合策略 - 基于反馈迭代：增加具体KOL推荐"""
    budget_tiers = {
        "高": {"head": "2-3个", "waist": "10-15个", "koc": "50-100个"},
        "中高": {"head": "1-2个", "waist": "8-12个", "koc": "30-50个"},
        "中等": {"head": "0-1个", "waist": "5-10个", "koc": "20-30个"},
        "低": {"head": "0个", "waist": "3-5个", "koc": "10-20个"},
    }
    
    tier = budget_tiers.get(budget, budget_tiers["中等"])
    head_ratio = 0.4 if budget in ["高", "中高"] else 0.3
    
    # 获取行业相关的示例KOL
    industry_kols = SAMPLE_KOL_DATABASE.get(industry, SAMPLE_KOL_DATABASE["通用"])
    
    # 根据预算级别选择推荐KOL数量
    head_count = 2 if budget == "高" else (1 if budget == "中高" else 0)
    waist_count = 3 if budget in ["高", "中高"] else 2
    
    recommended_head = industry_kols["head"][:head_count] if head_count > 0 else []
    recommended_waist = industry_kols["waist"][:waist_count]
    
    return {
        "head_kol": {
            "count": tier["head"],
            "count_range": [int(x) for x in tier["head"].replace("个", "").split("-")] if "-" in tier["head"] else [0, 0],
            "purpose": "品牌背书，大曝光",
            "budget_ratio": head_ratio,
            "recommended_kols": recommended_head,  # 新增：具体推荐
        },
        "waist_kol": {
            "count": tier["waist"],
            "count_range": [int(x) for x in tier["waist"].replace("个", "").split("-")],
            "purpose": "精准种草，ROI核心",
            "budget_ratio": 0.45,
            "recommended_kols": recommended_waist,  # 新增：具体推荐
        },
        "koc": {
            "count": tier["koc"],
            "count_range": [int(x) for x in tier["koc"].replace("个", "").split("-")],
            "purpose": "真实口碑，长尾效应",
            "budget_ratio": 1 - head_ratio - 0.45,
            "selection_criteria": [  # 新增：筛选标准
                "真实用户账号",
                "内容垂直度>80%",
                "互动率>3%",
                "粉丝画像匹配",
            ],
        },
        "execution_tips": [  # 新增：执行建议
            "头部KOL提前2-4周预约",
            "腰部KOL可批量联系",
            "KOC采用产品置换+佣金模式",
            "分批次投放测试效果",
        ],
    }


def _generate_content_strategy(industry: str, goal: str) -> dict:
    """生成内容策略"""
    themes = {
        "美妆": ["成分党测评", "妆教教程", "好物分享", "开箱体验"],
        "3C": ["科技测评", "开箱体验", "使用教程", "对比评测"],
        "快消": ["生活方式", "好物推荐", "场景植入", "开箱体验"],
        "母婴": ["育儿经验", "好物分享", "使用测评", "知识科普"],
        "时尚": ["穿搭分享", "开箱体验", "趋势解读", "好物推荐"],
    }
    
    default_themes = ["好物分享", "使用体验", "场景植入"]
    
    tones = {
        "美妆": "真实、亲和、专业",
        "3C": "专业、硬核、理性",
        "快消": "轻松、生活化、有趣",
        "母婴": "温暖、可信、实用",
        "时尚": "潮流、品味、质感",
    }
    
    return {
        "core_themes": themes.get(industry, default_themes),
        "content_tone": tones.get(industry, "真实、亲和"),
        "hashtag_strategy": "品牌词+品类词+场景词组合",
    }


def _generate_execution_guide(industry: str, goal: str, budget: str) -> dict:
    """生成执行指导 - 基于反馈迭代：提供更详细的执行建议"""
    # 阶段规划
    phases = [
        {
            "phase": "筹备期",
            "duration": "1-2周",
            "key_actions": [
                "确定KOL名单并发出邀约",
                "准备产品样品和brief",
                "确认合作细节和排期",
            ],
        },
        {
            "phase": "预热期",
            "duration": "1周",
            "key_actions": [
                "头部KOL发布预告",
                "官方账号话题预热",
                "种子用户内容铺垫",
            ],
        },
        {
            "phase": "爆发期",
            "duration": "2-3周",
            "key_actions": [
                "头部+腰部KOL集中发布",
                "话题营销和互动引导",
                "实时监测和数据反馈",
            ],
        },
        {
            "phase": "长尾期",
            "duration": "2-4周",
            "key_actions": [
                "KOC持续产出内容",
                "UGC内容二次传播",
                "数据复盘和效果评估",
            ],
        },
    ]
    
    # 风险提醒
    risk_warnings = {
        "美妆": ["注意成分宣传合规", "避免绝对化用语", "敏感肌测试声明"],
        "3C": ["参数准确性核查", "避免竞品直接对比", "3C认证展示"],
        "母婴": ["强调个人体验", "避免医疗建议", "安全使用提示"],
        "快消": ["价格宣传合规", "促销规则清晰", "库存预警"],
        "通用": ["内容需品牌方审核", "保留发布截图", "合同条款明确"],
    }
    
    # 成功关键
    success_factors = [
        "KOL选择与品牌调性匹配",
        "Brief清晰，减少沟通成本",
        "内容审核严格，避免违规",
        "数据监测及时，快速调整",
        "危机预案完备，快速响应",
    ]
    
    return {
        "phases": phases,
        "risk_warnings": risk_warnings.get(industry, risk_warnings["通用"]),
        "success_factors": success_factors,
        "budget_emergency_reserve": "建议预留10-15%预算应对突发情况",
        "data_tracking_points": [
            "曝光量、互动率",
            "CPE、CPM成本",
            "搜索指数变化",
            "电商转化数据",
        ],
    }


def _allocate_budget(budget: str, platforms: list) -> dict:
    """分配预算"""
    if len(platforms) >= 3:
        return {
            platforms[0]["name"]: 40,
            platforms[1]["name"]: 30,
            platforms[2]["name"]: 20,
            "其他": 10,
        }
    elif len(platforms) == 2:
        return {
            platforms[0]["name"]: 60,
            platforms[1]["name"]: 40,
        }
    else:
        return {platforms[0]["name"]: 100}


def _set_kpis(goal: str, budget: str) -> dict:
    """设定KPI"""
    budget_multipliers = {"高": 100, "中高": 50, "中等": 20, "低": 5}
    multiplier = budget_multipliers.get(budget, 20)
    
    if "曝光" in goal or "awareness" in goal.lower():
        return {
            "primary": f"总曝光 {multiplier * 100}万+",
            "secondary": f"互动量 {multiplier}万+",
            "tertiary": "品牌提及量提升50%+",
        }
    elif "转化" in goal or "销售" in goal:
        return {
            "primary": f"ROI 1:{max(3, multiplier//10)}",
            "secondary": f"销售额 {multiplier}0万+",
            "tertiary": "转化率提升30%+",
        }
    else:
        return {
            "primary": f"种草笔记 {multiplier * 5}0篇+",
            "secondary": f"搜索指数提升 {multiplier * 2}%+",
            "tertiary": "品牌词热度提升",
        }


def _generate_timeline() -> list[dict]:
    """生成执行时间线"""
    return [
        {"phase": "预热期", "duration": "1周", "activities": ["话题预热", "头部KOL官宣"]},
        {"phase": "爆发期", "duration": "2周", "activities": ["腰部KOL集中发布", "KOC铺量", "话题引爆"]},
        {"phase": "持续期", "duration": "1-2周", "activities": ["长尾内容持续", "UGC引导", "效果追踪"]},
    ]


# Tool executors
def strategy_parse_executor(payload: str) -> str:
    """解析brief的执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {"brief": ""}
    except json.JSONDecodeError:
        args = {"brief": payload}
    
    brief = args.get("brief", "")
    if not brief:
        return json.dumps({"error": "No brief provided"}, ensure_ascii=False)
    
    result = parse_brief(brief)
    return json.dumps(result, indent=2, ensure_ascii=False)


def strategy_generate_executor(payload: str) -> str:
    """生成策略的执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        args = {"brief_data": {"industry": "通用", "budget": "中等", "goal": "品牌曝光"}}
    
    brief_data = args.get("brief_data", {})
    if args.get("skills") and isinstance(args.get("skills"), list):
        brief_data["skills"] = args["skills"]
    result = generate_strategy(brief_data)
    return json.dumps(result, indent=2, ensure_ascii=False)
