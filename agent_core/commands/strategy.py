"""StrategyIQ Commands"""
from __future__ import annotations

import json
import sys


def run_industry_template(args: list[str]) -> int:
    """Show industry template command"""
    from agent_core.industry_templates import get_industry_template, list_industry_templates

    params = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            params[key] = value

    if params.get("list") in {"1", "true", "yes"}:
        print("\n🏭 可用行业模板")
        print("=" * 40)
        for name in list_industry_templates():
            print(f"  • {name}")
        return 0

    industry = params.get("industry", "通用")
    is_overseas = str(params.get("overseas", "false")).lower() in {"1", "true", "yes"}
    data = get_industry_template(industry, is_overseas=is_overseas)

    print("\n🏭 行业模板")
    print("=" * 40)
    print(f"行业: {data.get('industry')}")
    print(f"场景: {'海外' if is_overseas else '国内'}")
    print(f"目标: {data.get('core_objective')}")

    print("\n📱 平台建议:")
    for p in data.get("platforms", []):
        print(f"  • {p['name']}: {p.get('goal')} ({p.get('content_format')})")

    print("\n🧱 内容支柱:")
    for pillar in data.get("content_pillars", []):
        print(f"  • {pillar}")

    print("\n👥 KOL分层预算占比:")
    for k, v in data.get("tier_mix", {}).items():
        print(f"  {k}: {int(v * 100)}%")

    print("\n📊 必追指标:")
    print(f"  {', '.join(data.get('must_track_metrics', []))}")
    return 0


def run_strategy_parse(args: list[str]) -> int:
    """Parse brief command"""
    from agent_core.tools.strategy_iq import strategy_parse_executor
    
    brief = " ".join(args) if args else ""
    if not brief:
        print("Usage: ma strategy-parse <brief text>")
        return 1
    
    result = strategy_parse_executor(json.dumps({"brief": brief}))
    data = json.loads(result)
    
    print("\n📋 Brief解析结果")
    print("=" * 40)
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    return 0


def run_strategy_generate(args: list[str]) -> int:
    """Generate strategy command"""
    from agent_core.tools.strategy_iq import strategy_generate_executor
    
    # 解析参数
    params = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            params[key] = value
    
    brief_data = {
        "industry": params.get("industry", "通用"),
        "budget": params.get("budget", "中等"),
        "goal": params.get("goal", "品牌曝光"),
        "target_audience": params.get("audience", "大众"),
    }
    
    result = strategy_generate_executor(json.dumps({"brief_data": brief_data}))
    data = json.loads(result)
    
    print("\n🎯 营销策略方案")
    print("=" * 40)
    
    print("\n📱 平台策略:")
    for platform in data.get("platform_strategy", []):
        print(f"  • {platform['name']}: {platform['goal']} ({platform['priority']}优先级)")
    
    print("\n👥 KOL组合策略:")
    kol = data.get("kol_strategy", {})
    head_count = kol.get('head_kol', {}).get('count', '0个')
    waist_count = kol.get('waist_kol', {}).get('count', '0个')
    koc_count = kol.get('koc', {}).get('count', '0个')
    print(f"  头部KOL: {head_count} - {kol.get('head_kol', {}).get('purpose', '')}")
    print(f"  腰部KOL: {waist_count} - {kol.get('waist_kol', {}).get('purpose', '')}")
    print(f"  KOC: {koc_count} - {kol.get('koc', {}).get('purpose', '')}")
    
    print("\n💰 预算分配:")
    for platform, ratio in data.get("budget_allocation", {}).items():
        print(f"  {platform}: {ratio}%")
    
    print("\n📊 KPI目标:")
    for level, kpi in data.get("kpis", {}).items():
        print(f"  {level}: {kpi}")

    tpl = data.get("industry_template", {})
    if tpl:
        print("\n🏭 行业模板:")
        print(f"  行业: {tpl.get('industry')}")
        print(f"  目标: {tpl.get('core_objective')}")
        print(f"  分层占比: {tpl.get('tier_mix')}")
    
    return 0
