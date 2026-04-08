"""评估记录器 - 记录所有工作流运行数据"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class EvalRecord:
    """评估记录 - 单次工作流运行的完整数据"""
    # 基本信息
    record_id: str
    timestamp: str
    version: str = "1.0"
    
    # 输入
    input_brief: str = ""
    input_clarifications: dict = field(default_factory=dict)
    input_params: dict = field(default_factory=dict)
    
    # 解析结果
    parsed_brand: str = ""
    parsed_industry: str = ""
    parsed_budget: str = ""
    parsed_goal: str = ""
    parsed_is_overseas: bool = False
    
    # 输出结果
    output_strategy: dict = field(default_factory=dict)
    output_kol_recommendations: list = field(default_factory=list)
    output_outreach_messages: list = field(default_factory=list)
    output_creative_briefs: dict = field(default_factory=dict)
    output_full_report: dict = field(default_factory=dict)
    
    # 执行元数据
    execution_time_ms: int = 0
    stages_completed: list = field(default_factory=list)
    stages_failed: list = field(default_factory=list)
    llm_calls_count: int = 0
    
    # 人工评估（待填写）
    human_rating: int | None = None  # 1-5星
    human_feedback: str = ""  # 文字反馈
    issues_found: list = field(default_factory=list)  # 发现的问题
    improvement_suggestions: list = field(default_factory=list)  # 改进建议
    is_flagged: bool = False  # 是否标记为需要关注
    
    # 标签（用于分类和检索）
    tags: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class EvalRecorder:
    """评估记录器 - 管理和存储评估记录"""
    
    def __init__(self, storage_dir: str | None = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path(__file__).parent.parent.parent / ".agent" / "evals"
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.records: dict[str, EvalRecord] = {}
        self._load_existing_records()
    
    def _load_existing_records(self):
        """加载已有的记录"""
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    record = EvalRecord(**data)
                    self.records[record.record_id] = record
            except Exception as e:
                print(f"Failed to load record {file_path}: {e}")
    
    def create_record(self, brief: str, **kwargs) -> EvalRecord:
        """创建新记录"""
        record = EvalRecord(
            record_id=str(uuid.uuid4())[:12],
            timestamp=datetime.now().isoformat(),
            input_brief=brief,
            input_params=kwargs,
        )
        self.records[record.record_id] = record
        return record
    
    def update_record(self, record_id: str, **updates) -> EvalRecord | None:
        """更新记录"""
        record = self.records.get(record_id)
        if not record:
            return None
        
        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)
        
        self._save_record(record)
        return record
    
    def _save_record(self, record: EvalRecord):
        """保存记录到文件"""
        file_path = self.storage_dir / f"{record.record_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(record.to_json())
    
    def add_human_feedback(
        self,
        record_id: str,
        rating: int,
        feedback: str = "",
        issues: list = None,
        suggestions: list = None,
    ) -> EvalRecord | None:
        """添加人工反馈"""
        record = self.records.get(record_id)
        if not record:
            return None
        
        record.human_rating = rating
        record.human_feedback = feedback
        if issues:
            record.issues_found = issues
        if suggestions:
            record.improvement_suggestions = suggestions
        
        # 如果评分低于3星，自动标记
        if rating < 3:
            record.is_flagged = True
        
        self._save_record(record)
        return record
    
    def get_record(self, record_id: str) -> EvalRecord | None:
        """获取单条记录"""
        return self.records.get(record_id)
    
    def get_all_records(self) -> list[EvalRecord]:
        """获取所有记录"""
        return list(self.records.values())
    
    def get_flagged_records(self) -> list[EvalRecord]:
        """获取被标记的记录"""
        return [r for r in self.records.values() if r.is_flagged]
    
    def get_records_by_brand(self, brand: str) -> list[EvalRecord]:
        """按品牌筛选记录"""
        return [r for r in self.records.values() if r.parsed_brand == brand]
    
    def get_records_by_rating(self, min_rating: int = 4) -> list[EvalRecord]:
        """按评分筛选记录"""
        return [
            r for r in self.records.values()
            if r.human_rating is not None and r.human_rating >= min_rating
        ]
    
    def export_to_file(self, output_path: str, records: list[EvalRecord] | None = None):
        """导出记录到文件"""
        if records is None:
            records = self.get_all_records()
        
        data = {
            "export_time": datetime.now().isoformat(),
            "total_records": len(records),
            "records": [r.to_dict() for r in records],
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def generate_summary_report(self) -> dict:
        """生成评估摘要报告"""
        all_records = self.get_all_records()
        
        if not all_records:
            return {"message": "No records found"}
        
        # 基础统计
        total = len(all_records)
        with_feedback = [r for r in all_records if r.human_rating is not None]
        flagged = len(self.get_flagged_records())
        
        # 评分统计
        ratings = [r.human_rating for r in with_feedback if r.human_rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # 行业分布
        industries = {}
        for r in all_records:
            ind = r.parsed_industry or "未知"
            industries[ind] = industries.get(ind, 0) + 1
        
        # 执行时间统计
        exec_times = [r.execution_time_ms for r in all_records if r.execution_time_ms > 0]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
        
        return {
            "total_records": total,
            "records_with_feedback": len(with_feedback),
            "flagged_records": flagged,
            "average_rating": round(avg_rating, 2),
            "rating_distribution": {
                "5_star": len([r for r in with_feedback if r.human_rating == 5]),
                "4_star": len([r for r in with_feedback if r.human_rating == 4]),
                "3_star": len([r for r in with_feedback if r.human_rating == 3]),
                "2_star": len([r for r in with_feedback if r.human_rating == 2]),
                "1_star": len([r for r in with_feedback if r.human_rating == 1]),
            },
            "industry_distribution": industries,
            "average_execution_time_ms": round(avg_exec_time, 2),
            "top_issues": self._get_top_issues(all_records),
        }
    
    def _get_top_issues(self, records: list[EvalRecord], top_n: int = 5) -> list[dict]:
        """获取最常见的问题"""
        issue_counts = {}
        for r in records:
            for issue in r.issues_found:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"issue": issue, "count": count} for issue, count in sorted_issues[:top_n]]


# 全局记录器实例
_default_recorder: EvalRecorder | None = None


def get_eval_recorder(storage_dir: str | None = None) -> EvalRecorder:
    """获取全局评估记录器"""
    global _default_recorder
    if _default_recorder is None:
        _default_recorder = EvalRecorder(storage_dir)
    return _default_recorder
