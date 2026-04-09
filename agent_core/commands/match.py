"""MatchAI Commands"""
from __future__ import annotations

import json


def run_kol_search(args: list[str]) -> int:
    """Search KOLs command"""
    from agent_core.tools.match_ai import kol_search_executor
    
    # 解析参数
    params = {"platform": "小红书", "limit": 10}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key in ["min_engagement"]:
                params[key] = float(value)
            elif key in ["limit"]:
                params[key] = int(value)
            else:
                params[key] = value
    
    result = kol_search_executor(json.dumps(params))
    data = json.loads(result)
    
    print(f"\n🔍 KOL搜索结果 ({data.get('platform')})")
    print("=" * 60)
    print(f"过滤条件: {data.get('filters', {})}")
    print(f"找到 {data.get('total_found', 0)} 个结果\n")
    
    for i, kol in enumerate(data.get("results", []), 1):
        print(f"{i}. {kol['name']}")
        print(f"   粉丝: {kol['followers']} | 互动率: {kol['engagement']} | 报价: {kol['price']} | 层级: {kol.get('tier', 'N/A')}")
        print(f"   分类: {kol['category']} | 城市: {kol['city']}")
        print(f"   匹配度: {kol.get('match_score', 0)}% | 风险: {kol.get('risk_level', '未知')} | 预估ROI: {kol.get('estimated_roi', '未知')}")
        print()
    
    return 0


def run_kol_combo(args: list[str]) -> int:
    """Generate KOL combo command"""
    from agent_core.tools.match_ai import kol_combo_executor
    
    # 解析参数
    params = {"budget": 50, "platforms": ["小红书", "抖音"], "category": "美妆"}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key == "budget":
                params[key] = float(value)
            elif key == "platforms":
                params[key] = value.split(",")
            else:
                params[key] = value
    
    result = kol_combo_executor(json.dumps(params))
    data = json.loads(result)
    
    print(f"\n🎯 KOL组合方案")
    print("=" * 60)
    print(f"预算: {data.get('budget_total')}万 | 平台: {', '.join(data.get('platforms', []))} | 分类: {data.get('category')}")
    
    combo = data.get("combo", {})
    
    print(f"\n预算分配:")
    breakdown = combo.get("budget_allocation", {})
    for tier, d in breakdown.items():
        if isinstance(d, dict):
            print(f"  {tier}: {d.get('amount')}万 ({int(float(d.get('percentage', 0)))}%)")

    print(f"\n头部KOL ({len(combo.get('recommended_head', []))}个):")
    for kol in combo.get("recommended_head", []):
        print(f"  • {kol['name']} - {kol['followers']}粉 - {kol['price']}")
    
    print(f"\n腰部KOL ({len(combo.get('recommended_waist', []))}个):")
    for kol in combo.get("recommended_waist", [])[:5]:  # 只显示前5个
        print(f"  • {kol['name']} - {kol['followers']}粉 - {kol['price']}")
    if len(combo.get("recommended_waist", [])) > 5:
        print(f"  ... 还有 {len(combo.get('recommended_waist', [])) - 5} 个")
    
    print(f"\nKOC策略: {combo.get('koc_strategy', {}).get('count', 'N/A')}个")

    tier_quota = combo.get("tier_quota", {})
    if tier_quota:
        print("\n分层配比:")
        for tier, info in tier_quota.items():
            print(f"  {tier}: {info.get('count')} | 预算占比 {int(float(info.get('budget_ratio', 0)) * 100)}%")

    template = combo.get("industry_template", {})
    if template:
        print("\n行业模板:")
        print(f"  行业: {template.get('industry')}")
        print(f"  目标: {template.get('core_objective')}")

    if combo.get("applied_skills"):
        print("\n已应用Skills:")
        for s in combo.get("applied_skills", []):
            print(f"  • {s}")
    
    return 0
