"""MatchAI - KOL/KOC智能匹配系统 (LLM Powered)"""
from __future__ import annotations

import json
import os
import random
from typing import Any, Optional

from agent_core.case_playbook import derive_case_playbook
from agent_core.industry_templates import get_industry_template, normalize_industry
from agent_core.skills import resolve_skill_context


# 尝试导入数据源
try:
    from agent_core.data_sources import manager as data_source_manager
    HAS_DATA_SOURCES = True
except ImportError:
    HAS_DATA_SOURCES = False
    data_source_manager = None


# 模拟KOL数据库（当没有配置真实数据源时使用）
SAMPLE_KOLS = {
    "小红书": [
        {"name": "@美妆达人小美", "followers": "50万", "engagement": "8.5%", "category": "美妆", "price": "3万", "city": "上海", "recent_posts": ["口红试色", "护肤日常"], "brand_history": ["花西子", "完美日记"]},
        {"name": "@护肤分享师", "followers": "30万", "engagement": "9.2%", "category": "美妆", "price": "2万", "city": "杭州", "recent_posts": ["成分分析", "敏感肌护理"], "brand_history": ["薇诺娜", "理肤泉"]},
        {"name": "@生活方式博主", "followers": "80万", "engagement": "6.8%", "category": "生活方式", "price": "5万", "city": "北京", "recent_posts": ["日常vlog", "好物分享"], "brand_history": ["无印良品", "宜家"]},
        {"name": "@母婴博主乐乐", "followers": "40万", "engagement": "10.1%", "category": "母婴", "price": "2.5万", "city": "广州", "recent_posts": ["育儿经验", "宝宝辅食"], "brand_history": ["贝亲", "帮宝适"]},
        {"name": "@数码测评君", "followers": "60万", "engagement": "7.5%", "category": "3C", "price": "4万", "city": "深圳", "recent_posts": ["手机评测", "数码开箱"], "brand_history": ["小米", "华为"]},
    ],
    "抖音": [
        {"name": "@时尚小姐姐", "followers": "200万", "engagement": "5.2%", "category": "时尚", "price": "15万", "city": "上海", "recent_posts": ["穿搭分享", "变装视频"], "brand_history": ["ZARA", "H&M"]},
        {"name": "@搞笑日常", "followers": "500万", "engagement": "4.8%", "category": "娱乐", "price": "30万", "city": "成都", "recent_posts": ["搞笑段子", "生活日常"], "brand_history": []},
        {"name": "@美食探店", "followers": "150万", "engagement": "6.5%", "category": "美食", "price": "10万", "city": "重庆", "recent_posts": ["探店视频", "美食制作"], "brand_history": ["海底捞", "喜茶"]},
        {"name": "@科技大人", "followers": "300万", "engagement": "5.8%", "category": "3C", "price": "20万", "city": "北京", "recent_posts": ["科技评测", "产品开箱"], "brand_history": ["苹果", "三星"]},
        {"name": "@辣妈日记", "followers": "120万", "engagement": "7.2%", "category": "母婴", "price": "8万", "city": "杭州", "recent_posts": ["育儿日常", "母婴好物"], "brand_history": ["飞鹤", "好孩子"]},
    ],
    "微博": [
        {"name": "@时尚icon", "followers": "800万", "engagement": "3.5%", "category": "时尚", "price": "50万", "city": "北京", "recent_posts": ["时尚资讯", "穿搭分享"], "brand_history": ["LV", "Gucci"]},
        {"name": "@美妆教主", "followers": "600万", "engagement": "4.2%", "category": "美妆", "price": "40万", "city": "上海", "recent_posts": ["美妆教程", "产品推荐"], "brand_history": ["MAC", "雅诗兰黛"]},
        {"name": "@数码控", "followers": "400万", "engagement": "4.8%", "category": "3C", "price": "25万", "city": "深圳", "recent_posts": ["数码资讯", "评测分享"], "brand_history": ["华为", "OPPO"]},
    ],
    "B站": [
        {"name": "@测评实验室", "followers": "150万", "engagement": "12.5%", "category": "3C", "price": "12万", "city": "上海", "recent_posts": ["深度评测", "对比测试"], "brand_history": ["小米", "一加"]},
        {"name": "@生活分享官", "followers": "100万", "engagement": "10.2%", "category": "生活", "price": "8万", "city": "北京", "recent_posts": ["生活vlog", "好物分享"], "brand_history": ["网易严选", "小米有品"]},
        {"name": "@游戏解说", "followers": "300万", "engagement": "8.8%", "category": "游戏", "price": "18万", "city": "广州", "recent_posts": ["游戏评测", "直播回放"], "brand_history": ["腾讯游戏", "网易游戏"]},
    ],
    # 海外平台样本（用于海外场景全链路测试）
    "TikTok": [
        {"name": "@PetTechDaily", "followers": "180万", "engagement": "7.1%", "category": "宠物科技", "price": "9万", "city": "Los Angeles", "recent_posts": ["dog tracker test", "pet anxiety tips"], "brand_history": ["Tractive", "Whistle"]},
        {"name": "@DogMomVlog", "followers": "65万", "engagement": "9.4%", "category": "宠物科技", "price": "4万", "city": "Austin", "recent_posts": ["lost dog story", "pet camera review"], "brand_history": ["Furbo"]},
        {"name": "@RunnerGearLab", "followers": "95万", "engagement": "6.8%", "category": "运动鞋服", "price": "5万", "city": "New York", "recent_posts": ["pregame shoes", "training setup"], "brand_history": ["Nike", "Adidas"]},
    ],
    "Instagram": [
        {"name": "@petsignal.studio", "followers": "120万", "engagement": "5.9%", "category": "宠物科技", "price": "8万", "city": "San Diego", "recent_posts": ["rescue story", "smart collar routine"], "brand_history": ["Tractive"]},
        {"name": "@golden.and.human", "followers": "48万", "engagement": "8.3%", "category": "宠物科技", "price": "3万", "city": "Seattle", "recent_posts": ["dog separation anxiety", "daily check-in"], "brand_history": ["Furbo"]},
        {"name": "@mindful.runner", "followers": "70万", "engagement": "6.4%", "category": "运动鞋服", "price": "4万", "city": "Boston", "recent_posts": ["pregame focus", "shoe test"], "brand_history": ["Nike"]},
    ],
    "YouTube": [
        {"name": "@PetGearReviewLab", "followers": "210万", "engagement": "4.9%", "category": "宠物科技", "price": "12万", "city": "Toronto", "recent_posts": ["gps collar comparison", "petphone review"], "brand_history": ["Whistle", "Tractive"]},
        {"name": "@DogBehaviorCoach", "followers": "82万", "engagement": "7.0%", "category": "宠物科技", "price": "6万", "city": "Vancouver", "recent_posts": ["separation anxiety guide", "owner training"], "brand_history": ["PetPace"]},
        {"name": "@SportScienceRun", "followers": "130万", "engagement": "5.3%", "category": "运动鞋服", "price": "7万", "city": "London", "recent_posts": ["performance footwear", "game day prep"], "brand_history": ["Nike", "Puma"]},
    ],
}


def analyze_kol_with_llm(kol_data: dict, brand: str, product: str, target_audience: str) -> dict[str, Any]:
    """使用LLM分析KOL匹配度"""
    from agent_core.llm import get_llm_client
    
    llm = get_llm_client()
    
    system_prompt = """你是一个专业的KOL评估专家。请基于提供的KOL数据和品牌信息，进行全面的匹配度分析。

请以JSON格式返回分析结果：
{
    "match_score": 85,
    "match_reasoning": "详细说明为什么这个KOL适合/不适合该品牌",
    "audience_overlap": "目标受众重叠度分析",
    "content_fit": "内容风格契合度评估",
    "brand_alignment": "与品牌调性的匹配程度",
    "risk_factors": ["风险1", "风险2"],
    "advantages": ["优势1", "优势2"],
    "estimated_roi": "预估ROI范围，如1:5-1:8",
    "cooperation_suggestions": "合作建议"
}"""

    prompt = f"""请分析以下KOL与品牌的匹配度：

KOL信息：
{json.dumps(kol_data, ensure_ascii=False, indent=2)}

品牌信息：
- 品牌：{brand}
- 产品：{product}
- 目标受众：{target_audience}

请进行全面的匹配度分析。"""

    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            template = get_industry_template(
                normalize_industry(category),
                any(p in {"TikTok", "Instagram", "YouTube", "Facebook"} for p in platforms),
            )
            result.setdefault("industry_template", {
                "industry": template.get("industry"),
                "tier_mix": template.get("tier_mix"),
                "must_track_metrics": template.get("must_track_metrics", []),
            })
            return result
    except Exception:
        pass
    
    return _rule_based_analysis(kol_data, brand, product)


def _rule_based_analysis(kol_data: dict, brand: str, product: str) -> dict[str, Any]:
    """基于规则的备用分析"""
    score = 70
    
    # 互动率加分
    engagement_val = kol_data.get("engagement", "0%")
    if isinstance(engagement_val, (int, float)):
        engagement = float(engagement_val)
    else:
        engagement = float(str(engagement_val).rstrip("%"))
    if engagement > 8:
        score += 15
    elif engagement > 5:
        score += 5
    
    # 随机波动
    score += random.randint(-5, 5)
    
    return {
        "match_score": min(100, max(0, score)),
        "match_reasoning": "基于规则的基础匹配分析",
        "audience_overlap": "中等",
        "content_fit": "良好",
        "brand_alignment": "一般",
        "risk_factors": [],
        "advantages": ["互动率良好"],
        "estimated_roi": "1:5-1:8",
        "cooperation_suggestions": "建议小规模试水合作",
    }


def search_kols(
    platform: str,
    category: Optional[str] = None,
    min_followers: Optional[str] = None,
    max_followers: Optional[str] = None,
    min_engagement: Optional[float] = None,
    city: Optional[str] = None,
    brand: str = "",
    product: str = "",
    target_audience: str = "",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """搜索并智能分析KOL
    
    优先使用真实数据源，如果没有配置则使用模拟数据
    """
    # 解析粉丝数范围
    min_followers_num = parse_followers(min_followers) if min_followers else None
    max_followers_num = parse_followers(max_followers) if max_followers else None
    
    # 尝试从真实数据源搜索
    if HAS_DATA_SOURCES and data_source_manager:
        try:
            use_real_data = os.getenv("KOL_DATA_SOURCE", "mock") != "mock"
            if use_real_data:
                results = data_source_manager.search_all(
                    platform=platform,
                    category=category,
                    min_followers=min_followers_num,
                    max_followers=max_followers_num,
                    min_engagement=min_engagement,
                    city=city,
                    limit=limit
                )
                if results:
                    # 对真实数据进行智能分析
                    analyzed_results = []
                    for kol in results:
                        analysis = analyze_kol_with_llm(kol, brand, product, target_audience)
                        followers_count = parse_followers(kol.get("followers", "0"))
                        kol_result = {
                            **kol,
                            "tier": classify_kol_tier(followers_count),
                            **analysis,
                        }
                        analyzed_results.append(kol_result)
                    return analyzed_results
        except Exception as e:
            print(f"[MatchAI] 真实数据源搜索失败，使用模拟数据: {e}")
    
    # 使用模拟数据
    platform_kols = SAMPLE_KOLS.get(platform, [])
    
    results = []
    for kol in platform_kols:
        # 分类筛选
        if category and kol["category"] != category:
            continue
        
        # 城市筛选
        if city and city not in kol["city"]:
            continue
        
        # 粉丝量筛选
        followers_num = parse_followers(kol["followers"])
        if min_followers and followers_num < parse_followers(min_followers):
            continue
        if max_followers and followers_num > parse_followers(max_followers):
            continue
        
        # 互动率筛选
        engagement_val = kol.get("engagement", "0%")
        if isinstance(engagement_val, (int, float)):
            engagement = float(engagement_val)
        else:
            engagement = float(str(engagement_val).rstrip("%"))
        if min_engagement and engagement < min_engagement:
            continue
        
        # LLM智能分析
        analysis = analyze_kol_with_llm(kol, brand, product, target_audience)
        
        # 合并数据
        kol_result = {
            **kol,
            "tier": classify_kol_tier(followers_num),
            **analysis,
        }
        results.append(kol_result)
    
    # 按匹配度排序
    results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    return results[:limit]


def parse_followers(followers_str: str) -> int:
    """解析粉丝数量"""
    if not followers_str:
        return 0
    if isinstance(followers_str, (int, float)):
        return int(followers_str)
    
    followers_str = str(followers_str).strip()
    
    # 处理 "50万" 格式
    if "万" in followers_str:
        try:
            return int(float(followers_str.replace("万", "")) * 10000)
        except ValueError:
            return 0
    
    # 处理 "5千" 格式
    if "千" in followers_str:
        try:
            return int(float(followers_str.replace("千", "")) * 1000)
        except ValueError:
            return 0
    
    # 处理 "500k" 格式
    if followers_str.lower().endswith("k"):
        try:
            return int(float(followers_str[:-1]) * 1000)
        except ValueError:
            return 0
    
    # 处理 "5m" 格式
    if followers_str.lower().endswith("m"):
        try:
            return int(float(followers_str[:-1]) * 1000000)
        except ValueError:
            return 0
    
    # 纯数字
    try:
        return int(float(followers_str))
    except ValueError:
        return 0


def format_followers(count: int) -> str:
    """格式化粉丝数为易读格式"""
    if count >= 100000000:
        return f"{count / 100000000:.1f}亿"
    elif count >= 10000:
        return f"{count / 10000:.1f}万"
    elif count >= 1000:
        return f"{count / 1000:.1f}千"
    return str(count)


def classify_kol_tier(followers_count: int) -> str:
    """按粉丝量划分TOP/MID/BTM层级。"""
    if followers_count >= 1_000_000:
        return "TOP"
    if followers_count >= 100_000:
        return "MID"
    return "BTM"


def generate_kol_combo_with_llm(
    budget: float,
    platforms: list[str],
    category: str,
    brand: str,
    product: str,
    goal: str,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    """使用LLM生成KOL组合方案"""
    from agent_core.llm import get_llm_client
    
    llm = get_llm_client()
    
    skill_ctx = resolve_skill_context(
        "kol",
        {"industry": category, "preferred_platforms": platforms},
        requested_skills=skills,
    )
    system_prompt = """你是一个资深的KOL投放策略专家。请基于预算和品牌需求，设计最优的KOL组合方案。

请以JSON格式返回：
{
    "strategy_overview": "整体策略概述",
    "communication_plan": {
        "theme_options": [
            {"type": "理性利益点", "theme": "主题A", "fit_reason": "适配理由"},
            {"type": "感性利益点", "theme": "主题B", "fit_reason": "适配理由"}
        ],
        "rhythm": {
            "opening": {"duration_days": "1-3", "goal": "核心人群预热", "creator_profile": "专业/硬核意见领袖", "focus": "预热影响与二次传播"},
            "explosion": {"duration_days": "1-2", "goal": "大众扩圈", "content_mix": "PGC+UGC", "focus": "传播广度"},
            "elevation": {"duration_days": "1-2", "goal": "深度沉淀", "creator_profile": "行业专家/深度观点创作者", "focus": "品牌资产与精神共鸣"}
        }
    },
    "kol_selection_framework": {
        "priority_metrics": ["CPM", "CPE"],
        "content_relevance_ranking_logic": "内容关联性排序规则",
        "budget_reverse_estimation": "根据目标倒推曝光互动与预算配比",
        "rhythm_distribution_logic": "三段式节奏下的KOL分布原则",
        "performance_forecast_method": "AI预估模型说明"
    },
    "budget_allocation": {
        "head_kol": {"percentage": 40, "amount": 40, "rationale": "分配理由"},
        "waist_kol": {"percentage": 45, "amount": 45, "rationale": "分配理由"},
        "koc": {"percentage": 15, "amount": 15, "rationale": "分配理由"}
    },
    "platform_strategy": {
        "平台名": {"priority": "高", "budget_share": 50, "reasoning": "选择理由"}
    },
    "recommended_head": [{"name": "KOL名", "followers": "粉丝量", "price": "报价", "reasoning": "推荐理由"}],
    "recommended_waist": [{"name": "KOL名", "followers": "粉丝量", "price": "报价", "reasoning": "推荐理由"}],
    "koc_strategy": {"count": 30, "selection_criteria": "筛选标准", "execution_approach": "执行方式"},
    "expected_results": {
        "total_reach": "预计总触达",
        "estimated_engagement": "预估互动量",
        "expected_roi": "预期ROI"
    },
    "manual_override": {
        "enabled": true,
        "operations": ["add", "modify", "delete"],
        "note": "支持人工实时干预调整KOL组合"
    },
    "timeline": "执行时间建议",
    "risk_mitigation": ["风险应对措施1", "风险应对措施2"],
    "applied_skills": ["skill1"]
}""" + skill_ctx.get("skill_prompt_addon", "")

    prompt = f"""请为以下品牌设计KOL组合方案：

预算：{budget}万
平台：{', '.join(platforms)}
品类：{category}
品牌：{brand}
产品：{product}
目标：{goal}

请设计最优的KOL组合方案。"""

    try:
        result = llm.complete(prompt, system_prompt=system_prompt, json_mode=True)
        if isinstance(result, dict) and "error" not in result:
            result.setdefault("applied_skills", skill_ctx.get("applied_skills", []))
            return result
    except Exception:
        pass
    
    # 确保 budget 是数值类型
    budget_num = _parse_budget(budget)
    return _rule_based_combo(budget_num, platforms, category, goal, skills=skills)


def _rule_based_combo(
    budget: float,
    platforms: list[str],
    category: str,
    goal: str,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    """基于规则的备用组合生成"""
    # 从样本数据中筛选匹配的KOL
    all_kols = []
    for platform in platforms:
        all_kols.extend(SAMPLE_KOLS.get(platform, []))
    
    # 按分类筛选
    category_kols = [k for k in all_kols if k["category"] == category] or all_kols
    
    # 分配到不同层级
    head_kols = [k for k in category_kols if parse_followers(k["followers"]) >= 1000000][:2]
    waist_kols = [k for k in category_kols if 100000 <= parse_followers(k["followers"]) < 1000000][:8]
    platform_ratio = _allocate_platform_ratio(platforms)
    normalized_industry = normalize_industry(category)
    case_playbook = derive_case_playbook({
        "industry": category,
        "goal": goal,
        "is_overseas": any(p in {"TikTok", "Instagram", "YouTube", "Facebook"} for p in platforms),
    })
    template = get_industry_template(
        normalized_industry,
        any(p in {"TikTok", "Instagram", "YouTube", "Facebook"} for p in platforms),
    )
    tier_mix = template.get("tier_mix", {})
    skill_ctx = resolve_skill_context(
        "kol",
        {"industry": category, "preferred_platforms": platforms},
        requested_skills=skills,
    )
    
    return {
        "strategy_overview": f"基于{budget}万预算的KOL组合策略",
        "communication_plan": _build_communication_plan(goal, category),
        "kol_selection_framework": {
            "priority_metrics": ["CPM", "CPE"],
            "content_relevance_ranking_logic": "先按传播内容关联性排序，再结合近30天条均互动与报价筛选",
            "budget_reverse_estimation": "根据目标曝光与互动倒推所需达人数量和层级组合",
            "rhythm_distribution_logic": "开篇以专业硬核达人种子触达，引爆阶段扩展大众达人，升华阶段配置观点型创作者",
            "performance_forecast_method": "基于历史互动率、粉丝量、报价与平台系数进行AI区间预估",
        },
        "budget_allocation": {
            "head_kol": {"percentage": 40, "amount": budget * 0.4, "rationale": "品牌背书"},
            "waist_kol": {"percentage": 45, "amount": budget * 0.45, "rationale": "精准种草"},
            "koc": {"percentage": 15, "amount": budget * 0.15, "rationale": "口碑铺量"},
        },
        "recommended_head": head_kols,
        "recommended_waist": waist_kols,
        "koc_strategy": {"count": 30, "selection_criteria": "真实用户", "execution_approach": "批量铺量"},
        "tier_quota": _build_tier_quota(budget, tier_mix),
        "platform_strategy": {
            p: {"budget_share": platform_ratio[p], "priority": "高" if i == 0 else "中"}
            for i, p in enumerate(platforms)
        },
        "industry_template": {
            "industry": normalized_industry,
            "core_objective": template.get("core_objective"),
            "tier_mix": tier_mix,
            "must_track_metrics": template.get("must_track_metrics", []),
            "creative_must_include": template.get("creative_must_include", []),
        },
        "execution_tracker_fields": case_playbook.get("execution_tracker_fields", []),
        "creator_assignment": {
            "frontline_group": "事件现场/新品首发内容",
            "homebase_group": "生活场景/真实体验内容",
        },
        "expected_results": _estimate_combo_results(head_kols, waist_kols, budget),
        "manual_override": {
            "enabled": True,
            "operations": ["add", "modify", "delete"],
            "note": "支持人工实时干预调整KOL组合与节奏分布",
        },
        "applied_skills": skill_ctx.get("applied_skills", []),
    }


def _allocate_platform_ratio(platforms: list[str]) -> dict[str, int]:
    if not platforms:
        return {}
    if len(platforms) == 1:
        return {platforms[0]: 100}
    if len(platforms) == 2:
        return {platforms[0]: 60, platforms[1]: 40}
    return {platforms[0]: 40, platforms[1]: 35, platforms[2]: 25}


def _build_tier_quota(budget: float, tier_mix: dict[str, float] | None = None) -> dict[str, dict[str, Any]]:
    mix = tier_mix or {}
    top_ratio = float(mix.get("TOP", 0.35))
    mid_ratio = float(mix.get("MID", 0.5))
    btm_ratio = float(mix.get("BTM", max(0.0, 1 - top_ratio - mid_ratio)))
    if budget >= 100:
        return {
            "TOP": {"count": "2-3", "budget_ratio": top_ratio},
            "MID": {"count": "8-12", "budget_ratio": mid_ratio},
            "BTM": {"count": "40-80", "budget_ratio": btm_ratio},
        }
    if budget >= 50:
        return {
            "TOP": {"count": "1-2", "budget_ratio": top_ratio},
            "MID": {"count": "6-10", "budget_ratio": mid_ratio},
            "BTM": {"count": "20-40", "budget_ratio": btm_ratio},
        }
    return {
        "TOP": {"count": "0-1", "budget_ratio": top_ratio},
        "MID": {"count": "4-8", "budget_ratio": mid_ratio},
        "BTM": {"count": "10-30", "budget_ratio": btm_ratio},
    }


def _build_communication_plan(goal: str, category: str) -> dict[str, Any]:
    """构建三段式传播节奏与主题选项。"""
    return {
        "theme_options": [
            {
                "type": "理性利益点",
                "theme": f"{category}产品关键场景下的可验证效果证明",
                "fit_reason": f"适合{goal}目标，便于清晰传递产品价值与提升转化效率",
            },
            {
                "type": "感性利益点",
                "theme": f"{category}产品与用户关系/身份表达的情感共鸣叙事",
                "fit_reason": "有利于提升品牌记忆与社交传播意愿",
            },
        ],
        "rhythm": {
            "opening": {
                "duration_days": "1-3",
                "goal": "埋点式预热，影响核心受众",
                "creator_profile": "专业/硬核意见领袖",
                "focus": "形成种子讨论并触发二次传播",
            },
            "explosion": {
                "duration_days": "1-2",
                "goal": "PGC+UGC 联动扩圈",
                "creator_profile": "大众影响型KOL/KOC",
                "focus": "在不偏离主题下借势大众话题，放大传播广度",
            },
            "elevation": {
                "duration_days": "1-2",
                "goal": "深度内容沉淀与立意拔高",
                "creator_profile": "行业专家/观点型创作者",
                "focus": "沉淀品牌资产并加深精神共鸣",
            },
        },
    }


def _estimate_combo_results(head_kols: list[dict[str, Any]], waist_kols: list[dict[str, Any]], budget: float) -> dict[str, Any]:
    """规则估算组合效果，提供曝光/互动/ROI区间。"""
    total_pool = head_kols + waist_kols
    follower_base = sum(parse_followers(k.get("followers", "0")) for k in total_pool)
    avg_engagement = 0.06
    if total_pool:
        rates = []
        for k in total_pool:
            raw = str(k.get("engagement", "6")).replace("%", "")
            try:
                rates.append(float(raw) / 100.0)
            except ValueError:
                continue
        if rates:
            avg_engagement = sum(rates) / len(rates)
    total_reach = int(follower_base * 0.35) if follower_base else int(budget * 120000)
    estimated_engagement = int(total_reach * avg_engagement)
    roi_hint = round(max(1.2, min(4.5, 1.5 + budget / 120.0 + avg_engagement * 10)), 2)
    return {
        "total_reach": f"{total_reach:,}",
        "estimated_engagement": f"{estimated_engagement:,}",
        "expected_roi": f"1:{roi_hint}",
    }


# Tool executors
def kol_search_executor(payload: str) -> str:
    """KOL搜索执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        args = {}
    
    results = search_kols(
        platform=args.get("platform", "小红书"),
        category=args.get("category"),
        min_followers=args.get("min_followers"),
        max_followers=args.get("max_followers"),
        min_engagement=args.get("min_engagement"),
        city=args.get("city"),
        brand=args.get("brand", ""),
        product=args.get("product", ""),
        target_audience=args.get("target_audience", ""),
        limit=args.get("limit", 10),
    )
    
    return json.dumps({
        "platform": args.get("platform", "小红书"),
        "filters": args,
        "results": results,
        "total_found": len(results),
    }, indent=2, ensure_ascii=False)


def _parse_budget(budget_value) -> float:
    """安全解析预算值为数值类型"""
    if isinstance(budget_value, (int, float)):
        return float(budget_value)
    if isinstance(budget_value, str):
        # 处理 "待商议" 或其他非数字字符串
        if budget_value in ["待商议", "未提及", "", "未知"]:
            return 50.0  # 默认值
        # 尝试提取数字
        try:
            # 移除常见的单位字符
            cleaned = budget_value.replace("万", "").replace("元", "").replace(",", "").strip()
            return float(cleaned)
        except (ValueError, TypeError):
            return 50.0  # 默认预算
    return 50.0


def kol_combo_executor(payload: str) -> str:
    """KOL组合生成执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        args = {}
    
    budget = _parse_budget(args.get("budget", 50))
    
    combo = generate_kol_combo_with_llm(
        budget=budget,
        platforms=args.get("platforms", ["小红书", "抖音"]),
        category=args.get("category", "美妆"),
        brand=args.get("brand", "品牌"),
        product=args.get("product", "产品"),
        goal=args.get("goal", "种草"),
        skills=[s.strip() for s in str(args.get("skills", "")).split(",") if s.strip()] if args.get("skills") else None,
    )
    
    return json.dumps({
        "budget_total": budget,
        "platforms": args.get("platforms", ["小红书", "抖音"]),
        "category": args.get("category", "美妆"),
        "combo": combo,
    }, indent=2, ensure_ascii=False)


def kol_analyze_executor(payload: str) -> str:
    """KOL数据分析执行器"""
    try:
        args = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        args = {}
    
    kol_data = args.get("kol_data", {})
    
    if not kol_data:
        return json.dumps({"error": "No KOL data provided"}, ensure_ascii=False)
    
    analysis = analyze_kol_with_llm(
        kol_data,
        args.get("brand", ""),
        args.get("product", ""),
        args.get("target_audience", ""),
    )
    
    return json.dumps(analysis, indent=2, ensure_ascii=False)
