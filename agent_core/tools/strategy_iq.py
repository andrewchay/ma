"""StrategyIQ - 策略理解与生成引擎 (LLM Powered)"""
from __future__ import annotations

import json
from typing import Any

from agent_core.case_playbook import derive_case_playbook
from agent_core.industry_templates import get_industry_template, normalize_industry


def parse_brief(brief_text: str) -> dict[str, Any]:
    """使用LLM解析客户brief，提取关键信息"""
    from agent_core.llm import get_llm_client
    
    llm = get_llm_client()
    
    system_prompt = """你是一个专业的社交营销brief解析专家。请从用户输入中提取以下信息，并以JSON格式返回：
{
    "brand": "品牌名称",
    "industry": "行业类别（美妆/3C/快消/母婴/时尚/食品等）",
    "goal": "营销目标（品牌曝光/种草/转化/销售）",
    "budget": "预算级别（高/中高/中等/低），根据金额判断：>100万=高，50-100万=中高，20-50万=中等，<20万=低",
    "timeline": "执行周期",
    "target_audience": "目标受众描述",
    "key_messages": ["关键传播信息1", "关键传播信息2"],
    "preferred_platforms": ["首选平台1", "首选平台2"],
    "constraints": "特殊要求或限制"
}

如果某些信息未提及，使用"未提及"或合理推断。"""

    prompt = f"请解析以下营销brief：\n\n{brief_text}\n\n请提取关键信息并以JSON格式返回。"
    
    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            return result
        # Fallback to rule-based parsing
        return _rule_based_parse(brief_text)
    except Exception as e:
        return _rule_based_parse(brief_text)


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
    
    # 目标检测
    goal = "品牌曝光"
    if any(kw in text_lower for kw in ["种草", "转化", "购买"]):
        goal = "种草转化"
    elif any(kw in text_lower for kw in ["销售", "卖货", "成交", "gmv"]):
        goal = "销售转化"
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
    
    # 海外市场检测
    overseas_markers = ["海外", "国外", "美国", "欧洲", "日本", "韩国", "东南亚", "全球", "跨境", "出海", "tiktok", "youtube", "instagram", "facebook", "twitter"]
    is_overseas = any(marker in text_lower for marker in overseas_markers)
    
    return {
        "brand": brand,
        "industry": normalize_industry(industry),
        "goal": goal,
        "budget": budget,
        "budget_amount": budget_num,
        "timeline": "未提及",
        "target_audience": audience,
        "is_overseas": is_overseas,  # 添加海外市场标记
        "key_messages": [],
        "preferred_platforms": [],
        "constraints": "未提及",
    }


def _detect_industry(brief_text: str) -> str:
    """Detect industry with weighted keyword scoring."""
    text = (brief_text or "").lower()

    industry_keywords = {
        "宠物科技": ["宠物", "狗", "猫", "pet", "tracker", "collar", "分离焦虑", "项圈"],
        "运动鞋服": ["运动", "跑步", "篮球", "训练", "球鞋", "sneaker", "赛前", "赛事"],
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
    
    system_prompt = """你是一个资深的社交营销策略专家。请基于提供的brief信息，生成一份专业的营销策略方案。

【重要要求 - 基于用户反馈迭代】
1. 必须包含具体的KOL推荐（头部和腰部都要有具体人选或类型描述）
2. 平台策略要有详细的选择理由
3. 预算分配要具体到数字
4. 时间线要可执行

请确保策略包含：
1. 平台选择及理由（至少2-3个平台）
2. KOL组合策略（必须包含：头部/腰部/KOC的配比、具体推荐名单、预算占比）
3. 内容方向建议（核心主题、调性、hashtag策略）
4. 预算分配建议（平台维度+KOL维度）
5. KPI设定（主要、次要、第三层级）
6. 执行时间线（筹备期、预热期、爆发期、长尾期）
7. 执行指导（关键节点、风险提醒、成功要素）
8. 参考案例打法映射（case_playbook）

以JSON格式返回：
{
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
    "key_insights": ["核心洞察1", "核心洞察2"]
}"""

    prompt = f"""请为以下品牌制定社交营销策略：

品牌信息：
{json.dumps(brief_data, ensure_ascii=False, indent=2)}

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
        "key_insights": [
            "基于规则生成的策略（已基于用户反馈迭代增强KOL推荐）",
            f"案例映射: {', '.join(case_playbook.get('selected_cases', [])) or '通用方法'}",
            f"针对{industry}行业，推荐{len(kol_strategy.get('head_kol', {}).get('recommended_kols', []))}位头部KOL",
            f"推荐{len(kol_strategy.get('waist_kol', {}).get('recommended_kols', []))}位腰部KOL",
        ],
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
    result = generate_strategy(brief_data)
    return json.dumps(result, indent=2, ensure_ascii=False)
