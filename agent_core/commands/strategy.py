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


def _read_brief_from_arg(arg: str) -> str:
    """如果参数是文件路径则读取内容，否则直接返回文本。"""
    from pathlib import Path
    path = Path(arg)
    if path.is_file():
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: 无法读取文件 {arg}: {e}")
    return arg


def run_strategy_parse(args: list[str]) -> int:
    """Parse brief command (optionally auto-generate strategy)"""
    from agent_core.tools.strategy_iq import strategy_parse_executor, strategy_generate_executor

    parse_only = False
    brief_parts: list[str] = []
    for arg in args:
        if arg == "--parse-only" or arg == "parse_only=true":
            parse_only = True
            continue
        brief_parts.append(arg)

    brief = " ".join(brief_parts) if brief_parts else ""
    # 支持直接传入文件路径
    if len(brief_parts) == 1:
        brief = _read_brief_from_arg(brief_parts[0])

    if not brief:
        print("Usage: ma strategy-parse <brief text or file path> [--parse-only]")
        print("Example: ma strategy-parse brief.txt")
        return 1
    
    result = strategy_parse_executor(json.dumps({"brief": brief}))
    data = json.loads(result)
    
    print("\n📋 Brief解析结果")
    print("=" * 40)
    for key, value in data.items():
        print(f"  {key}: {value}")

    if not parse_only:
        strategy_result = strategy_generate_executor(json.dumps({"brief_data": data}))
        strategy = json.loads(strategy_result)

        print("\n🎯 自动生成策略")
        print("=" * 40)
        print("📱 平台策略:")
        for platform in strategy.get("platform_strategy", [])[:3]:
            print(f"  • {platform.get('name')}: {platform.get('goal')} ({platform.get('priority')}优先级)")

        kol = strategy.get("kol_strategy", {})
        print("\n👥 KOL组合:")
        print(f"  头部: {kol.get('head_kol', {}).get('count', '0个')}")
        print(f"  腰部: {kol.get('waist_kol', {}).get('count', '0个')}")
        print(f"  KOC: {kol.get('koc', {}).get('count', '0个')}")

        tpl = strategy.get("industry_template", {})
        if tpl:
            print("\n🏭 行业模板:")
            print(f"  行业: {tpl.get('industry')}")
            print(f"  目标: {tpl.get('core_objective')}")

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
    if "skills" in params:
        brief_data["skills"] = [s.strip() for s in params["skills"].split(",") if s.strip()]
    
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

    audience_research = data.get("audience_research", {})
    if audience_research:
        print("\n🔎 用户研究洞察:")
        for insight in audience_research.get("insights", [])[:2]:
            print(f"  • {insight}")

    competitor = data.get("competitor_analysis", {})
    if competitor:
        print("\n🧭 竞品传播分析:")
        for gap in competitor.get("white_space", [])[:2]:
            print(f"  • {gap}")

    framework = data.get("market_strategy_framework", {})
    if framework:
        print("\n🧠 市场策略分块框架:")
        user = framework.get("user_research", {})
        dims = user.get("profile_dimensions", [])
        if dims:
            print(f"  用户画像维度: {', '.join(dims)}")
        for s in user.get("scenario_insights", [])[:2]:
            print(f"  • 场景洞察: {s}")
        prod = framework.get("product_features", {})
        if prod.get("unique_attributes"):
            print(f"  产品独特属性: {', '.join(prod.get('unique_attributes', [])[:2])}")
        triple = framework.get("triple_positioning_options", [])
        if triple:
            print("  三定位方向:")
            for item in triple[:3]:
                print(f"    - {item.get('name', '定位')}: {item.get('logic', '')}")

    angle = data.get("communication_angle", {})
    if angle:
        print("\n🎬 传播主角度:")
        print(f"  Hero Message: {angle.get('hero_message', '')}")
        print(f"  Creative Hook: {angle.get('creative_hook', '')}")

    if data.get("applied_skills"):
        print("\n🧩 已应用Skills:")
        for s in data.get("applied_skills", []):
            print(f"  • {s}")

    tpl = data.get("industry_template", {})
    if tpl:
        print("\n🏭 行业模板:")
        print(f"  行业: {tpl.get('industry')}")
        print(f"  目标: {tpl.get('core_objective')}")
        print(f"  分层占比: {tpl.get('tier_mix')}")
    
    return 0
