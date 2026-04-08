"""反馈分析器 - 分析用户反馈并驱动Agent迭代"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_core.eval.recorder import EvalRecorder, get_eval_recorder


@dataclass
class FeedbackInsight:
    """反馈洞察"""
    category: str
    issue_type: str
    frequency: int
    severity: str  # high, medium, low
    suggested_fix: str
    affected_modules: list[str]


class FeedbackAnalyzer:
    """反馈分析器 - 从用户反馈中提取洞察并建议改进"""
    
    # 问题模式映射
    ISSUE_PATTERNS = {
        "kol推荐不准确": ["kol", "推荐", "匹配", "达人", "博主"],
        "平台选择不合适": ["平台", "渠道", "小红书", "抖音", "b站"],
        "预算分配不合理": ["预算", "分配", "价格", "报价", "费用"],
        "内容方向不符合": ["内容", "创意", "方向", "brief", "脚本"],
        "时间规划有问题": ["时间", "周期", "排期", "timeline"],
        "缺少关键信息": ["缺少", "缺失", "没有", "不足", "空白"],
        "结果不准确": ["不准", "错误", "不对", "差", "不好"],
        "格式不清晰": ["格式", "排版", "乱", "看不清"],
    }
    
    def __init__(self, recorder: EvalRecorder | None = None):
        self.recorder = recorder or get_eval_recorder()
        self.insights: list[FeedbackInsight] = []
    
    def analyze_all_feedback(self) -> dict[str, Any]:
        """分析所有反馈数据"""
        records = self.recorder.get_all_records()
        
        if not records:
            return {"message": "暂无反馈数据"}
        
        # 基础统计
        total = len(records)
        with_feedback = [r for r in records if r.human_rating is not None]
        flagged = self.recorder.get_flagged_records()
        
        # 评分分布
        ratings = [r.human_rating for r in with_feedback if r.human_rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # 问题统计
        all_issues = []
        module_ratings = {}
        low_rating_feedback = []
        
        for r in records:
            # 收集问题
            all_issues.extend(r.issues_found)
            
            # 按模块统计评分
            module = r.input_params.get("module", "workflow")
            if module not in module_ratings:
                module_ratings[module] = []
            if r.human_rating:
                module_ratings[module].append(r.human_rating)
            
            # 收集低分反馈
            if r.human_rating and r.human_rating < 3:
                low_rating_feedback.append({
                    "record_id": r.record_id,
                    "rating": r.human_rating,
                    "feedback": r.human_feedback,
                    "issues": r.issues_found,
                    "brief": r.input_brief[:100] if r.input_brief else "",
                })
        
        # 问题分类
        issue_counter = Counter(all_issues)
        
        # 生成洞察
        self._generate_insights(low_rating_feedback, issue_counter)
        
        return {
            "total_records": total,
            "records_with_feedback": len(with_feedback),
            "flagged_records": len(flagged),
            "average_rating": round(avg_rating, 2),
            "rating_distribution": {
                "5_star": len([r for r in with_feedback if r.human_rating == 5]),
                "4_star": len([r for r in with_feedback if r.human_rating == 4]),
                "3_star": len([r for r in with_feedback if r.human_rating == 3]),
                "2_star": len([r for r in with_feedback if r.human_rating == 2]),
                "1_star": len([r for r in with_feedback if r.human_rating == 1]),
            },
            "top_issues": issue_counter.most_common(10),
            "module_performance": {
                module: {
                    "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
                    "count": len(ratings),
                }
                for module, ratings in module_ratings.items()
            },
            "low_rating_details": low_rating_feedback,
            "insights": [self._insight_to_dict(i) for i in self.insights],
        }
    
    def _generate_insights(
        self,
        low_rating_feedback: list[dict],
        issue_counter: Counter
    ):
        """基于反馈生成洞察"""
        self.insights = []
        
        # 分析问题文本
        for feedback_item in low_rating_feedback:
            feedback_text = feedback_item.get("feedback", "")
            issues = feedback_item.get("issues", [])
            
            # 检查反馈文本中的关键词
            for issue_type, keywords in self.ISSUE_PATTERNS.items():
                if any(kw in feedback_text.lower() for kw in keywords):
                    self._add_insight(issue_type, feedback_text, issues)
        
        # 基于常见问题生成洞察
        for issue, count in issue_counter.most_common(5):
            if count >= 1:
                self._add_insight_from_issue(issue, count)
    
    def _add_insight(self, issue_type: str, feedback_text: str, issues: list):
        """添加洞察"""
        suggested_fix = self._get_suggested_fix(issue_type, feedback_text)
        
        insight = FeedbackInsight(
            category="功能改进",
            issue_type=issue_type,
            frequency=1,
            severity="high" if "没有" in feedback_text or "缺少" in feedback_text else "medium",
            suggested_fix=suggested_fix,
            affected_modules=self._detect_modules(feedback_text),
        )
        self.insights.append(insight)
    
    def _add_insight_from_issue(self, issue: str, count: int):
        """从问题标签生成洞察"""
        fix_map = {
            "KOL推荐不准确": "优化KOL匹配算法，增加更多筛选维度",
            "平台选择不合适": "改进平台推荐逻辑，考虑更多因素",
            "预算分配不合理": "调整预算分配策略，提供更详细的说明",
            "内容方向不符合": "优化内容brief生成，增加品牌调性分析",
            "时间规划有问题": "改进时间线生成，考虑实际执行可行性",
            "缺少关键信息": "增强信息提取能力，主动询问缺失信息",
            "结果不准确": "优化LLM prompt，增加验证机制",
            "格式不清晰": "改进输出格式，提供更清晰的结构",
        }
        
        insight = FeedbackInsight(
            category="功能改进",
            issue_type=issue,
            frequency=count,
            severity="high" if count >= 2 else "medium",
            suggested_fix=fix_map.get(issue, "需要进一步分析"),
            affected_modules=["all"],
        )
        self.insights.append(insight)
    
    def _get_suggested_fix(self, issue_type: str, feedback_text: str) -> str:
        """基于问题类型和反馈文本生成建议修复方案"""
        fixes = {
            "kol": "增强KOL推荐模块，确保策略输出包含具体的KOL组合建议",
            "平台": "优化平台选择逻辑，增加平台适配度分析",
            "预算": "改进预算分配算法，提供更细致的预算拆分",
            "内容": "增强内容策略生成，提供更多创意方向",
            "时间": "优化时间线规划，考虑实际执行约束",
        }
        
        for key, fix in fixes.items():
            if key in feedback_text.lower():
                return fix
        
        return "需要进一步分析具体问题"
    
    def _detect_modules(self, feedback_text: str) -> list[str]:
        """检测反馈涉及的模块"""
        modules = []
        if "strategy" in feedback_text.lower() or "策略" in feedback_text:
            modules.append("StrategyIQ")
        if "kol" in feedback_text.lower() or "match" in feedback_text.lower():
            modules.append("MatchAI")
        if "connect" in feedback_text.lower() or "建联" in feedback_text or "话术" in feedback_text:
            modules.append("ConnectBot")
        if "creative" in feedback_text.lower() or "创意" in feedback_text or "内容" in feedback_text:
            modules.append("CreativePilot")
        if not modules:
            modules.append("workflow")
        return modules
    
    def _insight_to_dict(self, insight: FeedbackInsight) -> dict:
        """转换洞察为字典"""
        return {
            "category": insight.category,
            "issue_type": insight.issue_type,
            "frequency": insight.frequency,
            "severity": insight.severity,
            "suggested_fix": insight.suggested_fix,
            "affected_modules": insight.affected_modules,
        }
    
    def generate_iteration_plan(self) -> dict[str, Any]:
        """生成迭代计划"""
        analysis = self.analyze_all_feedback()
        insights = analysis.get("insights", [])
        
        if not insights:
            return {"message": "暂无足够反馈生成迭代计划"}
        
        # 按严重程度和频率排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_insights = sorted(
            insights,
            key=lambda x: (priority_order.get(x["severity"], 3), -x["frequency"])
        )
        
        # 生成行动计划
        actions = []
        for insight in sorted_insights[:5]:  # 取前5个
            actions.append({
                "priority": "高" if insight["severity"] == "high" else "中",
                "module": ", ".join(insight["affected_modules"]),
                "issue": insight["issue_type"],
                "action": insight["suggested_fix"],
                "expected_impact": "提升用户满意度",
            })
        
        return {
            "summary": f"基于 {analysis['records_with_feedback']} 条反馈生成",
            "current_avg_rating": analysis.get("average_rating", 0),
            "target_rating": 4.5,
            "top_issues": analysis.get("top_issues", []),
            "actions": actions,
        }


def analyze_feedback() -> dict[str, Any]:
    """便捷的反馈分析函数"""
    analyzer = FeedbackAnalyzer()
    return analyzer.analyze_all_feedback()


def get_iteration_plan() -> dict[str, Any]:
    """获取迭代计划"""
    analyzer = FeedbackAnalyzer()
    return analyzer.generate_iteration_plan()
