"""澄清引擎 - 管理多轮澄清对话"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any
from datetime import datetime


@dataclass
class ClarificationQuestion:
    """澄清问题"""
    id: str
    field: str  # 字段名，如 "budget", "target_audience"
    question: str  # 问题文本
    reason: str  # 为什么需要这个问题
    priority: str  # 优先级: high/medium/low
    suggested_answer: str | None = None  # 建议的答案（如果有）
    user_answer: str | None = None  # 用户的实际回答
    is_resolved: bool = False


@dataclass
class ClarificationSession:
    """澄清会话"""
    session_id: str
    original_brief: str
    questions: list[ClarificationQuestion] = field(default_factory=list)
    resolved_questions: list[ClarificationQuestion] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "original_brief": self.original_brief,
            "questions": [asdict(q) for q in self.questions],
            "resolved_questions": [asdict(q) for q in self.resolved_questions],
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class ClarificationEngine:
    """澄清引擎 - 管理澄清流程"""
    
    # 关键字段定义
    CRITICAL_FIELDS = {
        "brand": {
            "question": "请确认品牌名称是什么？",
            "reason": "品牌名称是制定策略的基础",
            "priority": "high",
        },
        "budget": {
            "question": "本次投放的预算范围是多少（万元）？",
            "reason": "预算决定KOL层级选择和投放规模",
            "priority": "high",
        },
        "product": {
            "question": "具体推广的是什么产品？",
            "reason": "产品类型影响内容策略和平台选择",
            "priority": "high",
        },
        "goal": {
            "question": "本次营销的主要目标是什么？",
            "reason": "不同目标（曝光/种草/转化）需要不同的策略",
            "priority": "high",
            "options": ["品牌曝光", "产品种草", "销售转化", "用户增长"],
        },
        "target_audience": {
            "question": "目标受众是谁？",
            "reason": "受众特征影响KOL选择和内容方向",
            "priority": "medium",
        },
        "timeline": {
            "question": "期望的执行时间周期是？",
            "reason": "时间影响排期和节奏安排",
            "priority": "medium",
        },
        "is_overseas": {
            "question": "是国内投放还是海外投放？",
            "reason": "影响平台选择和KOL资源",
            "priority": "high",
            "options": ["国内", "海外"],
        },
    }
    
    def __init__(self):
        self.sessions: dict[str, ClarificationSession] = {}
    
    def analyze_brief(self, brief_text: str, parsed_result: dict) -> ClarificationSession:
        """
        分析Brief，识别需要澄清的问题
        
        Returns:
            ClarificationSession: 包含所有需要澄清的问题
        """
        session_id = str(uuid.uuid4())[:8]
        session = ClarificationSession(
            session_id=session_id,
            original_brief=brief_text,
        )
        
        # 检查每个关键字段
        for field, config in self.CRITICAL_FIELDS.items():
            value = parsed_result.get(field)
            
            # 判断是否需要澄清
            needs_clarification = self._check_needs_clarification(field, value)
            
            if needs_clarification:
                question = ClarificationQuestion(
                    id=f"{session_id}_{field}",
                    field=field,
                    question=config["question"],
                    reason=config["reason"],
                    priority=config["priority"],
                    suggested_answer=self._generate_suggestion(field, parsed_result),
                )
                session.questions.append(question)
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        session.questions.sort(key=lambda q: priority_order.get(q.priority, 3))
        
        self.sessions[session_id] = session
        return session
    
    def _check_needs_clarification(self, field: str, value: Any) -> bool:
        """检查字段是否需要澄清"""
        if value is None:
            return True
        if value == "未提及":
            return True
        if value == "":
            return True
        if field == "budget_amount" and value == "待商议":
            return True
        if field == "is_overseas" and value is None:
            return True
        return False
    
    def _generate_suggestion(self, field: str, parsed_result: dict) -> str | None:
        """基于已有信息生成建议答案"""
        if field == "budget":
            # 根据行业给预算建议
            industry = parsed_result.get("industry", "")
            suggestions = {
                "美妆": "建议100-300万",
                "3C": "建议200-500万",
                "快消": "建议50-150万",
            }
            return suggestions.get(industry)
        return None
    
    def answer_question(self, session_id: str, question_id: str, answer: str) -> ClarificationSession | None:
        """用户回答一个问题"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # 找到对应的问题
        for i, q in enumerate(session.questions):
            if q.id == question_id:
                q.user_answer = answer
                q.is_resolved = True
                session.resolved_questions.append(q)
                session.questions.pop(i)
                break
        
        # 检查是否所有问题都已解决
        if not session.questions:
            session.completed_at = datetime.now().isoformat()
        
        return session
    
    def get_enhanced_brief(self, session_id: str) -> dict:
        """获取增强后的Brief（包含用户澄清的信息）"""
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        enhanced = {
            "original_brief": session.original_brief,
            "clarifications": {},
        }
        
        for q in session.resolved_questions:
            enhanced["clarifications"][q.field] = q.user_answer
        
        return enhanced
    
    def get_pending_questions(self, session_id: str) -> list[ClarificationQuestion]:
        """获取待澄清的问题列表"""
        session = self.sessions.get(session_id)
        if not session:
            return []
        return session.questions
    
    def is_clarification_complete(self, session_id: str) -> bool:
        """检查澄清是否完成"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        return len(session.questions) == 0


class BriefAnalyzer:
    """Brief分析器 - 识别信息缺失"""
    
    @staticmethod
    def identify_missing_info(parsed_brief: dict) -> list[dict]:
        """识别缺失的关键信息"""
        missing = []
        
        critical_checks = [
            ("brand", "品牌名称", "无法确定品牌身份"),
            ("budget_amount", "预算金额", "无法推荐合适的KOL层级"),
            ("goal", "营销目标", "无法制定具体策略"),
            ("is_overseas", "投放区域", "无法确定国内还是海外平台"),
        ]
        
        for field, name, impact in critical_checks:
            value = parsed_brief.get(field)
            if value in [None, "未提及", "", "待商议"]:
                missing.append({
                    "field": field,
                    "name": name,
                    "impact": impact,
                    "severity": "high" if field in ["brand", "budget_amount"] else "medium",
                })
        
        return missing
    
    @staticmethod
    def generate_clarification_prompt(missing_info: list[dict]) -> str:
        """生成澄清提示"""
        if not missing_info:
            return "信息完整，可以开始制定策略。"
        
        prompt = "为了给您制定更精准的营销方案，请补充以下信息：\n\n"
        for item in missing_info:
            prompt += f"❓ **{item['name']}**\n"
            prompt += f"   影响：{item['impact']}\n\n"
        
        return prompt
