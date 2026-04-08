"""营销工作流 V2 - 集成澄清机制和Eval记录"""
from __future__ import annotations

import time
from typing import Any, Callable

from agent_core.workflow.engine import WorkflowEngine, WorkflowStage, WorkflowContext
from agent_core.clarification.engine import ClarificationEngine, ClarificationSession
from agent_core.eval.recorder import EvalRecorder, EvalRecord, get_eval_recorder
from agent_core.tools.strategy_iq import parse_brief, generate_strategy
from agent_core.tools.match_ai import search_kols, generate_kol_combo_with_llm
from agent_core.tools.connect_bot import generate_outreach_with_llm
from agent_core.tools.creative_pilot import generate_creative_brief_with_llm


class ClarificationStage(WorkflowStage):
    """阶段0: 检查并处理信息澄清"""
    
    def __init__(self, clarification_engine: ClarificationEngine):
        super().__init__(
            name="clarification",
            description="检查Brief完整性，识别需要澄清的问题"
        )
        self.clarification_engine = clarification_engine
        self.user_callback: Callable | None = None
    
    def set_user_callback(self, callback: Callable):
        """设置用户交互回调"""
        self.user_callback = callback
    
    def execute(self, context: WorkflowContext) -> dict[str, Any]:
        brief_text = context.input_data.get("brief", "")
        
        # 解析Brief
        parsed = parse_brief(brief_text)
        
        # 分析需要澄清的问题
        session = self.clarification_engine.analyze_brief(brief_text, parsed)
        
        # 如果有需要澄清的问题
        if session.questions:
            context.log("clarification", "needs_clarification", {
                "question_count": len(session.questions),
                "questions": [{"field": q.field, "question": q.question} for q in session.questions]
            })
            
            # 如果有用户回调，进行交互式澄清
            if self.user_callback:
                for question in session.questions:
                    # 调用用户回调获取答案
                    answer = self.user_callback(question)
                    if answer:
                        self.clarification_engine.answer_question(
                            session.session_id, question.id, answer
                        )
            else:
                # 无回调模式：返回需要澄清的信息，暂停工作流
                return {
                    "stage": "clarification",
                    "status": "pending",
                    "session_id": session.session_id,
                    "questions": [
                        {
                            "id": q.id,
                            "field": q.field,
                            "question": q.question,
                            "reason": q.reason,
                            "priority": q.priority,
                        }
                        for q in session.questions
                    ],
                    "message": f"需要澄清 {len(session.questions)} 个问题才能继续",
                }
        
        # 获取增强后的Brief
        enhanced_brief = self.clarification_engine.get_enhanced_brief(session.session_id)
        
        # 合并原始解析结果和澄清结果
        final_parsed = {**parsed, **enhanced_brief.get("clarifications", {})}
        
        return {
            "stage": "clarification",
            "status": "completed",
            "session_id": session.session_id,
            "original_parsed": parsed,
            "clarifications": enhanced_brief.get("clarifications", {}),
            "final_parsed": final_parsed,
        }


class MarketingWorkflowV2:
    """营销工作流 V2 - 支持澄清和Eval记录"""
    
    def __init__(self):
        self.engine = WorkflowEngine("marketing_campaign_v2")
        self.clarification_engine = ClarificationEngine()
        self.eval_recorder = get_eval_recorder()
        self.current_record: EvalRecord | None = None
        self._build_workflow()
    
    def _build_workflow(self):
        """构建工作流"""
        # 添加澄清阶段
        clarification_stage = ClarificationStage(self.clarification_engine)
        self.engine.add_stage(clarification_stage)
        
        # 添加其他阶段（复用V1的逻辑）
        from agent_core.workflow.marketing_workflow import (
            BriefParseStage,
            StrategyGenerateStage,
            KOLMatchStage,
            OutreachPrepareStage,
            CreativeBriefStage,
            ReportGenerateStage,
        )
        
        self.engine.add_stage(BriefParseStage())
        self.engine.add_stage(StrategyGenerateStage())
        self.engine.add_stage(KOLMatchStage())
        self.engine.add_stage(OutreachPrepareStage())
        self.engine.add_stage(CreativeBriefStage())
        self.engine.add_stage(ReportGenerateStage())
    
    def run(
        self,
        brief: str,
        clarifications: dict[str, str] | None = None,
        user_callback: Callable | None = None,
        **kwargs
    ) -> WorkflowContext:
        """
        运行工作流
        
        Args:
            brief: 原始Brief
            clarifications: 预填写的澄清答案 {field: answer}
            user_callback: 用户交互回调函数(question) -> answer
            **kwargs: 其他参数
        """
        start_time = time.time()
        
        # 创建Eval记录
        self.current_record = self.eval_recorder.create_record(brief, **kwargs)
        
        # 准备输入
        input_data = {
            "brief": brief,
            "clarifications": clarifications or {},
            **kwargs
        }
        
        # 设置回调
        def on_stage_complete(stage_name, result):
            # 更新Eval记录
            if self.current_record:
                self.current_record.stages_completed.append(stage_name)
                # 根据阶段更新记录
                self._update_record_from_stage(stage_name, result)
        
        def on_stage_fail(stage_name, error):
            if self.current_record:
                self.current_record.stages_failed.append(stage_name)
        
        self.engine.set_callbacks(on_stage_complete, on_stage_fail)
        
        # 执行工作流
        try:
            context = self.engine.execute(input_data)
            
            # 计算执行时间
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # 更新记录
            if self.current_record:
                self.current_record.execution_time_ms = execution_time_ms
                self.eval_recorder._save_record(self.current_record)
            
            return context
            
        except Exception as e:
            # 记录失败
            if self.current_record:
                self.current_record.execution_time_ms = int((time.time() - start_time) * 1000)
                self.eval_recorder._save_record(self.current_record)
            raise
    
    def _update_record_from_stage(self, stage_name: str, result: dict):
        """根据阶段结果更新Eval记录"""
        if not self.current_record:
            return
        
        if stage_name == "clarification":
            if result.get("status") == "completed":
                final = result.get("final_parsed", {})
                self.current_record.parsed_brand = final.get("brand", "")
                self.current_record.parsed_industry = final.get("industry", "")
                self.current_record.parsed_budget = str(final.get("budget_amount", ""))
                self.current_record.parsed_goal = final.get("goal", "")
                self.current_record.parsed_is_overseas = final.get("is_overseas", False)
                self.current_record.input_clarifications = result.get("clarifications", {})
        
        elif stage_name == "strategy_generate":
            self.current_record.output_strategy = result.get("strategy", {})
        
        elif stage_name == "kol_match":
            self.current_record.output_kol_recommendations = result.get("platform_kols", {})
        
        elif stage_name == "outreach_prepare":
            self.current_record.output_outreach_messages = result.get("outreach_messages", [])
        
        elif stage_name == "creative_brief":
            self.current_record.output_creative_briefs = result.get("platform_briefs", {})
        
        elif stage_name == "report_generate":
            self.current_record.output_full_report = result.get("report", {})
    
    def get_record_id(self) -> str | None:
        """获取当前记录ID"""
        return self.current_record.record_id if self.current_record else None


def run_marketing_workflow_v2(
    brief: str,
    clarifications: dict[str, str] | None = None,
    require_clarification: bool = True,
) -> dict:
    """
    快速运行营销工作流V2
    
    Args:
        brief: 客户brief文本
        clarifications: 预填写的澄清答案
        require_clarification: 是否需要澄清步骤
    
    Returns:
        包含执行结果和记录ID的字典
    """
    workflow = MarketingWorkflowV2()
    
    try:
        context = workflow.run(brief, clarifications=clarifications)
        
        # 获取最终报告
        report_output = context.get_stage_output("report_generate")
        
        return {
            "success": len(context.failed_stages) == 0,
            "record_id": workflow.get_record_id(),
            "duration": context.end_time - context.start_time if context.end_time else 0,
            "completed_stages": context.completed_stages,
            "failed_stages": context.failed_stages,
            "report": report_output.get("report") if report_output else None,
        }
        
    except Exception as e:
        return {
            "success": False,
            "record_id": workflow.get_record_id(),
            "error": str(e),
        }
