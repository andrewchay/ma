"""Built-in commands registration"""
from __future__ import annotations

from agent_core.models import CommandModule
from agent_core.commands.strategy import run_strategy_parse, run_strategy_generate, run_industry_template
from agent_core.commands.match import run_kol_search, run_kol_combo
from agent_core.commands.connect import (
    run_outreach_generate,
    run_follow_up_generate,
    run_negotiation_advice,
)
from agent_core.commands.creative import (
    run_creative_brief,
    run_content_template,
    run_content_review,
)
from agent_core.commands.workflow import (
    run_full_workflow,
    run_workflow_interactive,
)


def run_status(_: list[str]) -> int:
    """Show agent status"""
    from pathlib import Path
    
    root = Path.cwd()
    print(f"\n🚀 Flow 复楼 MA Agent")
    print("=" * 40)
    print(f"Location: {root}")
    print()
    print("核心模块:")
    print("  ✅ StrategyIQ - 策略理解与生成")
    print("  ✅ MatchAI - KOL智能匹配")
    print("  ✅ ConnectBot - 智能建联")
    print("  ✅ CreativePilot - 创意内容指导")
    print("  ✅ Workflow - 端到端工作流")
    print()
    print("可用命令:")
    print("  ma strategy-parse <brief>")
    print("  ma strategy-generate [params]")
    print("  ma industry-template [params]")
    print("  ma kol-search [params]")
    print("  ma kol-combo [params]")
    print("  ma outreach [params]")
    print("  ma follow-up [params]")
    print("  ma negotiation [params]")
    print("  ma creative-brief [params]")
    print("  ma content-template [params]")
    print("  ma content-review [params]")
    print("  ma workflow <brief>          # 端到端工作流")
    print("  ma workflow-i                # 交互式工作流")
    return 0


def run_help(_: list[str]) -> int:
    """Show help"""
    print("""
🚀 Flow 复楼 MA Agent - 智能社交营销AI代理

使用方法: ma <command> [args...]

核心命令:

📊 StrategyIQ - 策略生成
  strategy-parse <brief>           解析brief并自动生成策略
    可选: --parse-only             仅解析不生成策略
  strategy-generate [params]       生成策略
    params: industry=<行业> budget=<预算> goal=<目标> skills=<skill1,skill2>
  industry-template [params]       查看行业模板
    params: industry=<行业> overseas=<true|false> 或 list=true

🎯 MatchAI - KOL匹配
  kol-search [params]              搜索KOL
    params: platform=<平台> category=<分类> min_engagement=<互动率> limit=<数量>
  kol-combo [params]               生成KOL组合
    params: budget=<预算> platforms=<平台1,平台2> category=<分类>

🤝 ConnectBot - 智能建联
  outreach [params]                生成建联话术
    params: kol_name=<KOL名> brand=<品牌> platform=<平台> style=<风格>
  follow-up [params]               生成跟进话术
    params: kol_name=<KOL名> brand=<品牌> days_since=<天数>
  negotiation [params]             谈判建议
    params: kol_price=<报价> budget=<预算> kol_engagement=<互动率> kol_followers=<粉丝数>

✨ CreativePilot - 创意指导
  creative-brief [params]          生成创意Brief
    params: brand=<品牌> product=<产品> platform=<平台>
  content-template [params]        生成内容模板
    params: brand=<品牌> product=<产品> template_type=<类型> platform=<平台>
  content-review [params]          审核内容
    params: content=<内容> brand=<品牌> platform=<平台>

🔄 Workflow - 端到端工作流
  workflow <brief>                 一键生成完整营销方案
                                   例: ma workflow "美妆品牌新品上市预算100万"
  workflow-i                       交互式工作流 (问答式)

其他命令:
  status                           查看状态
  help                             显示帮助

示例:
  ma workflow "美妆品牌花西子新品口红上市，预算100万，目标种草"
  ma strategy-parse "美妆品牌新品上市预算100万目标种草"
  ma kol-search platform=抖音 category=美妆 min_engagement=5 limit=5
  ma outreach kol_name=美妆达人 brand=花西子 platform=小红书
""")
    return 0


BUILTIN_COMMANDS: list[CommandModule] = [
    CommandModule(
        name="status",
        responsibility="Show agent status",
        source_hint="agent_core/commands/builtin.py",
        handler=run_status,
    ),
    CommandModule(
        name="help",
        responsibility="Show help information",
        source_hint="agent_core/commands/builtin.py",
        handler=run_help,
    ),
    CommandModule(
        name="strategy-parse",
        responsibility="Parse client brief",
        source_hint="agent_core/commands/strategy.py",
        handler=run_strategy_parse,
    ),
    CommandModule(
        name="strategy-generate",
        responsibility="Generate marketing strategy",
        source_hint="agent_core/commands/strategy.py",
        handler=run_strategy_generate,
    ),
    CommandModule(
        name="industry-template",
        responsibility="Show industry marketing template",
        source_hint="agent_core/commands/strategy.py",
        handler=run_industry_template,
    ),
    CommandModule(
        name="kol-search",
        responsibility="Search and filter KOLs",
        source_hint="agent_core/commands/match.py",
        handler=run_kol_search,
    ),
    CommandModule(
        name="kol-combo",
        responsibility="Generate KOL combination",
        source_hint="agent_core/commands/match.py",
        handler=run_kol_combo,
    ),
    CommandModule(
        name="outreach",
        responsibility="Generate outreach message",
        source_hint="agent_core/commands/connect.py",
        handler=run_outreach_generate,
    ),
    CommandModule(
        name="follow-up",
        responsibility="Generate follow-up message",
        source_hint="agent_core/commands/connect.py",
        handler=run_follow_up_generate,
    ),
    CommandModule(
        name="negotiation",
        responsibility="Provide negotiation advice",
        source_hint="agent_core/commands/connect.py",
        handler=run_negotiation_advice,
    ),
    CommandModule(
        name="creative-brief",
        responsibility="Generate creative brief",
        source_hint="agent_core/commands/creative.py",
        handler=run_creative_brief,
    ),
    CommandModule(
        name="content-template",
        responsibility="Generate content template",
        source_hint="agent_core/commands/creative.py",
        handler=run_content_template,
    ),
    CommandModule(
        name="content-review",
        responsibility="Review content",
        source_hint="agent_core/commands/creative.py",
        handler=run_content_review,
    ),
    CommandModule(
        name="workflow",
        responsibility="Run full marketing workflow end-to-end",
        source_hint="agent_core/commands/workflow.py",
        handler=run_full_workflow,
    ),
    CommandModule(
        name="workflow-i",
        responsibility="Run interactive marketing workflow",
        source_hint="agent_core/commands/workflow.py",
        handler=run_workflow_interactive,
    ),
]
