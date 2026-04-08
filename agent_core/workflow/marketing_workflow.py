"""营销工作流 - 端到端自动化营销方案生成"""
from __future__ import annotations

import json
import time
from typing import Any

from agent_core.workflow.engine import WorkflowEngine, WorkflowStage, WorkflowContext
from agent_core.tools.strategy_iq import parse_brief, generate_strategy
from agent_core.tools.match_ai import search_kols, generate_kol_combo_with_llm
from agent_core.tools.connect_bot import (
    generate_outreach_with_llm,
    generate_follow_up_with_llm,
    generate_negotiation_strategy_with_llm,
)
from agent_core.tools.creative_pilot import generate_creative_brief_with_llm


class BriefParseStage(WorkflowStage):
    """阶段1: 解析Brief"""
    
    def __init__(self):
        super().__init__(
            name="brief_parse",
            description="解析客户Brief，提取关键信息"
        )
    
    def execute(self, context: WorkflowContext) -> dict[str, Any]:
        brief_text = context.input_data.get("brief", "")
        if not brief_text:
            raise ValueError("Brief text is required")
        
        result = parse_brief(brief_text)
        return {
            "stage": "brief_parse",
            "parsed_brief": result,
            "summary": f"识别品牌: {result.get('brand', '未识别')}, "
                      f"行业: {result.get('industry', '未识别')}, "
                      f"预算: {result.get('budget', '未识别')}, "
                      f"目标: {result.get('goal', '未识别')}"
        }


class StrategyGenerateStage(WorkflowStage):
    """阶段2: 生成营销策略"""
    
    def __init__(self):
        super().__init__(
            name="strategy_generate",
            description="基于Brief生成完整营销策略"
        )
    
    def execute(self, context: WorkflowContext) -> dict[str, Any]:
        # 获取上一阶段的输出
        brief_data = context.get_stage_output("brief_parse")["parsed_brief"]
        
        # 生成策略
        strategy = generate_strategy(brief_data)
        
        return {
            "stage": "strategy_generate",
            "strategy": strategy,
            "summary": f"推荐平台: {', '.join([p['name'] for p in strategy.get('platform_strategy', [])])}; "
                      f"KOL组合: 头部{strategy.get('kol_strategy', {}).get('head_kol', {}).get('count', '0')} + "
                      f"腰部{strategy.get('kol_strategy', {}).get('waist_kol', {}).get('count', '0')} + "
                      f"KOC{strategy.get('kol_strategy', {}).get('koc', {}).get('count', '0')}"
        }


class KOLMatchStage(WorkflowStage):
    """阶段3: KOL匹配与推荐"""
    
    def __init__(self):
        super().__init__(
            name="kol_match",
            description="搜索并推荐匹配的KOL"
        )
    
    def _parse_budget(self, budget_value) -> float:
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
    
    def execute(self, context: WorkflowContext) -> dict[str, Any]:
        # 获取策略信息
        strategy = context.get_stage_output("strategy_generate")["strategy"]
        brief_data = context.get_stage_output("brief_parse")["parsed_brief"]
        
        platforms = [p["name"] for p in strategy.get("platform_strategy", [])]
        if not platforms:
            platforms = ["小红书", "抖音"]
        
        # 为每个平台搜索KOL
        platform_kols = {}
        all_kols = []
        
        for platform in platforms[:2]:  # 限制前2个平台
            kols = search_kols(
                platform=platform,
                category=brief_data.get("industry", "美妆"),
                brand=brief_data.get("brand", ""),
                product="产品",
                target_audience=brief_data.get("target_audience", ""),
                limit=5,
            )
            platform_kols[platform] = kols
            all_kols.extend(kols)
        
        # 生成组合方案
        budget = self._parse_budget(brief_data.get("budget_amount", 50))
        combo = generate_kol_combo_with_llm(
            budget=budget,
            platforms=platforms,
            category=brief_data.get("industry", "美妆"),
            brand=brief_data.get("brand", "品牌"),
            product="产品",
            goal=brief_data.get("goal", "种草"),
        )
        
        return {
            "stage": "kol_match",
            "platform_kols": platform_kols,
            "kol_combo": combo,
            "total_kols_found": len(all_kols),
            "summary": f"找到 {len(all_kols)} 位KOL; "
                      f"推荐头部: {len(combo.get('recommended_head', []))}位, "
                      f"腰部: {len(combo.get('recommended_waist', []))}位"
        }


class OutreachPrepareStage(WorkflowStage):
    """阶段4: 准备建联材料"""
    
    def __init__(self):
        super().__init__(
            name="outreach_prepare",
            description="生成建联话术和谈判策略"
        )
    
    def execute(self, context: WorkflowContext) -> dict[str, Any]:
        brief_data = context.get_stage_output("brief_parse")["parsed_brief"]
        kol_data = context.get_stage_output("kol_match")
        
        brand = brief_data.get("brand", "品牌")
        product = "产品"
        
        # 为推荐的头部和腰部KOL生成话术
        outreach_messages = []
        
        head_kols = kol_data.get("kol_combo", {}).get("recommended_head", [])
        waist_kols = kol_data.get("kol_combo", {}).get("recommended_waist", [])
        
        # 为前2个头部KOL生成话术
        for kol in head_kols[:2]:
            message = generate_outreach_with_llm(
                kol_name=kol.get("name", "KOL"),
                kol_profile=kol,
                brand=brand,
                brand_intro=f"致力于提供优质{product}",
                product=product,
                platform=kol.get("platform", "小红书"),
                style="professional",
                cooperation_type="内容合作",
                budget_range="面议",
            )
            outreach_messages.append({
                "kol": kol.get("name"),
                "platform": kol.get("platform", "小红书"),
                "type": "head",
                "message": message,
            })
        
        # 为前3个腰部KOL生成话术
        for kol in waist_kols[:3]:
            message = generate_outreach_with_llm(
                kol_name=kol.get("name", "KOL"),
                kol_profile=kol,
                brand=brand,
                brand_intro=f"致力于提供优质{product}",
                product=product,
                platform=kol.get("platform", "小红书"),
                style="casual",
                cooperation_type="内容合作",
                budget_range="面议",
            )
            outreach_messages.append({
                "kol": kol.get("name"),
                "platform": kol.get("platform", "小红书"),
                "type": "waist",
                "message": message,
            })
        
        return {
            "stage": "outreach_prepare",
            "outreach_messages": outreach_messages,
            "total_messages": len(outreach_messages),
            "summary": f"生成 {len(outreach_messages)} 份建联话术 "
                      f"(头部: {len([m for m in outreach_messages if m['type'] == 'head'])}, "
                      f"腰部: {len([m for m in outreach_messages if m['type'] == 'waist'])})"
        }


class CreativeBriefStage(WorkflowStage):
    """阶段5: 生成创意指导"""
    
    def __init__(self):
        super().__init__(
            name="creative_brief",
            description="生成创意Brief和内容指导"
        )
    
    def execute(self, context: WorkflowContext) -> dict[str, Any]:
        brief_data = context.get_stage_output("brief_parse")["parsed_brief"]
        strategy = context.get_stage_output("strategy_generate")["strategy"]
        
        brand = brief_data.get("brand", "品牌")
        product = "产品"
        platforms = [p["name"] for p in strategy.get("platform_strategy", [])]
        
        # 为每个平台生成创意Brief
        platform_briefs = {}
        for platform in platforms[:2]:
            brief = generate_creative_brief_with_llm(
                brand=brand,
                product=product,
                platform=platform,
                kol_style="真实分享",
                key_messages=brief_data.get("key_messages", []),
                must_include=["产品展示", "使用体验"],
                forbidden=["竞品对比", "绝对化用语"],
                target_audience=brief_data.get("target_audience", "年轻女性"),
                campaign_goal=brief_data.get("goal", "种草"),
                industry=brief_data.get("industry", "通用"),
            )
            platform_briefs[platform] = brief
        
        return {
            "stage": "creative_brief",
            "platform_briefs": platform_briefs,
            "summary": f"为 {len(platform_briefs)} 个平台生成创意Brief: {', '.join(platform_briefs.keys())}"
        }


class ReportGenerateStage(WorkflowStage):
    """阶段6: 生成执行报告"""
    
    def __init__(self):
        super().__init__(
            name="report_generate",
            description="生成完整执行方案报告"
        )
    
    def execute(self, context: WorkflowContext) -> dict[str, Any]:
        # 收集所有阶段的输出
        brief_data = context.get_stage_output("brief_parse")["parsed_brief"]
        strategy = context.get_stage_output("strategy_generate")["strategy"]
        kol_data = context.get_stage_output("kol_match")
        outreach = context.get_stage_output("outreach_prepare")
        creative = context.get_stage_output("creative_brief")
        
        # 生成完整报告
        report = {
            "project_info": {
                "brand": brief_data.get("brand", "未指定"),
                "product": "产品",
                "industry": brief_data.get("industry", "未指定"),
                "budget": brief_data.get("budget_amount", "未指定"),
                "goal": brief_data.get("goal", "未指定"),
                "timeline": brief_data.get("timeline", "未指定"),
            },
            "strategy": strategy,
            "kol_recommendation": {
                "platform_kols": kol_data.get("platform_kols", {}),
                "kol_combo": kol_data.get("kol_combo", {}),
            },
            "outreach_plan": {
                "messages": outreach.get("outreach_messages", []),
                "follow_up_schedule": [
                    {"day": 3, "action": "首次跟进"},
                    {"day": 7, "action": "二次跟进"},
                    {"day": 14, "action": "最终确认"},
                ],
            },
            "creative_guidelines": creative.get("platform_briefs", {}),
            "execution_timeline": strategy.get("timeline", []),
            "next_steps": [
                "1. 审核营销策略方案",
                "2. 确认KOL推荐名单",
                "3. 发送建联话术",
                "4. 跟进KOL反馈",
                "5. 签订合作协议",
                "6. 执行内容创作",
                "7. 监控投放效果",
            ],
        }
        
        return {
            "stage": "report_generate",
            "report": report,
            "summary": f"生成完整执行报告: 包含策略、KOL推荐({kol_data.get('total_kols_found', 0)}位)、"
                      f"建联话术({outreach.get('total_messages', 0)}份)、创意指导"
        }


class MarketingWorkflow:
    """营销工作流 - 端到端自动化"""
    
    def __init__(self):
        self.engine = WorkflowEngine("marketing_campaign")
        self._build_workflow()
    
    def _build_workflow(self):
        """构建标准营销工作流"""
        self.engine.add_stage(BriefParseStage())
        self.engine.add_stage(StrategyGenerateStage())
        self.engine.add_stage(KOLMatchStage())
        self.engine.add_stage(OutreachPrepareStage())
        self.engine.add_stage(CreativeBriefStage())
        self.engine.add_stage(ReportGenerateStage())
    
    def run(self, brief: str, **kwargs) -> WorkflowContext:
        """运行完整工作流"""
        input_data = {
            "brief": brief,
            **kwargs
        }
        return self.engine.execute(input_data)
    
    def run_with_progress(self, brief: str, progress_callback=None, **kwargs) -> WorkflowContext:
        """运行工作流并报告进度"""
        def on_complete(stage_name, result):
            if progress_callback:
                progress_callback(stage_name, result)
        
        self.engine.set_callbacks(on_complete=on_complete)
        return self.run(brief, **kwargs)


# 便捷函数
def run_marketing_workflow(brief: str, **kwargs) -> dict:
    """
    快速运行营销工作流
    
    Args:
        brief: 客户brief文本
        **kwargs: 其他参数
    
    Returns:
        完整执行报告
    """
    workflow = MarketingWorkflow()
    context = workflow.run(brief, **kwargs)
    
    # 获取最终报告
    report = context.get_stage_output("report_generate")
    
    return {
        "success": len(context.failed_stages) == 0,
        "duration": context.end_time - context.start_time if context.end_time else 0,
        "completed_stages": context.completed_stages,
        "failed_stages": context.failed_stages,
        "report": report.get("report") if report else None,
        "execution_log": context.execution_log,
    }
