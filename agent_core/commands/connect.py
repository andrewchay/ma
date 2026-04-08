"""ConnectBot Commands"""
from __future__ import annotations

import json


def run_outreach_generate(args: list[str]) -> int:
    """Generate outreach message command"""
    from agent_core.tools.connect_bot import outreach_generate_executor
    
    # 解析参数
    params = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            params[key] = value
    
    required = ["kol_name", "brand", "platform"]
    for r in required:
        if r not in params:
            print(f"Usage: ma outreach kol_name=<name> brand=<brand> platform=<platform> [style=<formal|casual|professional>]")
            return 1
    
    result = outreach_generate_executor(json.dumps(params))
    data = json.loads(result)
    
    print(f"\n📧 建联话术 ({data.get('style')})")
    print("=" * 60)
    print(f"主题: {data.get('subject')}")
    print()
    print(data.get('body'))
    
    return 0


def run_follow_up_generate(args: list[str]) -> int:
    """Generate follow-up message command"""
    from agent_core.tools.connect_bot import follow_up_generate_executor
    
    params = {"days_since": 3}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key == "days_since":
                params[key] = int(value)
            else:
                params[key] = value
    
    if "kol_name" not in params or "brand" not in params:
        print("Usage: ma follow-up kol_name=<name> brand=<brand> [days_since=<days>]")
        return 1
    
    result = follow_up_generate_executor(json.dumps(params))
    data = json.loads(result)
    
    print(f"\n📨 跟进话术 ({data.get('tone')})")
    print("=" * 60)
    print(f"距离上次联系: {data.get('days_since')}天")
    print()
    print(data.get('message'))
    
    return 0


def run_negotiation_advice(args: list[str]) -> int:
    """Generate negotiation advice command"""
    from agent_core.tools.connect_bot import negotiation_advice_executor
    
    params = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            params[key] = float(value) if "." in value else int(value)
    
    required = ["kol_price", "budget", "kol_engagement", "kol_followers"]
    for r in required:
        if r not in params:
            print(f"Usage: ma negotiation kol_price=<price> budget=<budget> kol_engagement=<rate> kol_followers=<count>")
            return 1
    
    result = negotiation_advice_executor(json.dumps(params))
    data = json.loads(result)
    
    print(f"\n💼 谈判建议")
    print("=" * 60)
    print(f"建议报价: {data.get('counter_offer')}万")
    print(f"单互动成本: {data.get('price_per_engagement')}元")
    print(f"预估CPE: {data.get('estimated_cpe')}元")
    
    print(f"\n💡 谈判要点:")
    for tip in data.get("tips", []):
        print(f"  • {tip}")
    
    print(f"\n🎯 谈判筹码:")
    for leverage in data.get("negotiation_leverage", []):
        if leverage:
            print(f"  • {leverage}")
    
    return 0
