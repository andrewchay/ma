"""Workflow Commands"""
from __future__ import annotations

import json
import time


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


def run_full_workflow(args: list[str]) -> int:
    """运行完整营销工作流"""
    from agent_core.workflow.marketing_workflow import MarketingWorkflow
    
    # 解析参数
    joined = " ".join(args) if args else ""
    # 支持直接传入文件路径
    brief = _read_brief_from_arg(joined) if len(args) == 1 else joined
    
    if not brief:
        print("Usage: ma workflow <brief text or file path>")
        print("Example: ma workflow \"美妆品牌花西子新品口红上市，预算100万，目标种草年轻女性\"")
        print("Example: ma workflow brief.txt")
        return 1
    
    print("\n" + "=" * 60)
    print("🚀 启动端到端营销工作流")
    print("=" * 60)
    print(f"\n📋 Brief: {brief[:80]}...")
    print("\n开始执行，请稍候...\n")
    
    workflow = MarketingWorkflow()
    
    # 进度回调
    def on_progress(stage_name, result):
        summary = result.get("summary", "")
        print(f"  ✅ {stage_name}: {summary[:60]}...")
    
    try:
        start_time = time.time()
        context = workflow.run_with_progress(brief, progress_callback=on_progress)
        duration = time.time() - start_time
        
        print(f"\n{'=' * 60}")
        print(f"✅ 工作流执行完成! (耗时: {duration:.1f}秒)")
        print(f"{'=' * 60}\n")
        
        # 获取报告
        report_output = context.get_stage_output("report_generate")
        if report_output:
            report = report_output.get("report", {})
            
            # 项目信息
            project = report.get("project_info", {})
            print("📊 项目概览")
            print("-" * 40)
            print(f"  品牌: {project.get('brand', 'N/A')}")
            print(f"  行业: {project.get('industry', 'N/A')}")
            print(f"  预算: {project.get('budget', 'N/A')}万")
            print(f"  目标: {project.get('goal', 'N/A')}")
            
            # 策略摘要
            strategy = report.get("strategy", {})
            print("\n📱 平台策略")
            print("-" * 40)
            for platform in strategy.get("platform_strategy", []):
                print(f"  • {platform['name']}: {platform['goal']} ({platform['priority']}优先级)")
            
            # KOL推荐
            kol_rec = report.get("kol_recommendation", {})
            combo = kol_rec.get("kol_combo", {})
            print("\n👥 KOL组合推荐")
            print("-" * 40)
            print(f"  头部KOL: {len(combo.get('recommended_head', []))}位")
            print(f"  腰部KOL: {len(combo.get('recommended_waist', []))}位")
            
            # 建联计划
            outreach = report.get("outreach_plan", {})
            print(f"\n✉️ 建联计划: 已生成 {len(outreach.get('messages', []))} 份话术")
            
            # 下一步
            print("\n📋 下一步行动")
            print("-" * 40)
            for step in report.get("next_steps", [])[:5]:
                print(f"  {step}")
            
            # 保存报告
            report_file = f"workflow_report_{int(time.time())}.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n💾 完整报告已保存: {report_file}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 工作流执行失败: {str(e)}")
        return 1


def run_workflow_stage(args: list[str]) -> int:
    """运行工作流的单个阶段"""
    if not args:
        print("Usage: ma workflow-stage <stage_name> [params...]")
        print("Stages: brief_parse, strategy_generate, kol_match, outreach_prepare, creative_brief")
        return 1
    
    stage_name = args[0]
    # 这里可以实现单个阶段的执行
    print(f"执行阶段: {stage_name}")
    print("(此功能待实现)")
    return 0


def run_workflow_interactive(_: list[str]) -> int:
    """交互式工作流"""
    print("\n" + "=" * 60)
    print("🚀 Flow 复楼 - 交互式营销工作流")
    print("=" * 60)
    
    # 收集信息
    print("\n请回答以下问题，或直接输入完整brief:\n")
    
    brief_input = input("📋 请输入您的营销需求 (或完整brief): ").strip()
    
    if not brief_input:
        print("❌ 输入不能为空")
        return 1
    
    # 询问是否补充信息
    print("\n是否需要补充以下信息? (直接回车跳过)")
    brand = input("品牌名称: ").strip()
    budget = input("预算(万): ").strip()
    goal = input("营销目标(种草/曝光/转化): ").strip()
    
    # 构建完整brief
    full_brief = brief_input
    if brand:
        full_brief += f" 品牌:{brand}"
    if budget:
        full_brief += f" 预算{budget}万"
    if goal:
        full_brief += f" 目标{goal}"
    
    print(f"\n{'=' * 60}")
    print("开始执行工作流...")
    print(f"{'=' * 60}\n")
    
    # 运行工作流
    return run_full_workflow([full_brief])
