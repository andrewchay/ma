"""改进追踪器 - 追踪基于反馈的迭代效果"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from agent_core.eval.recorder import get_eval_recorder


@dataclass
class ImprovementIteration:
    """改进迭代记录"""
    iteration_id: str
    timestamp: str
    trigger_feedback_id: str
    issue_description: str
    affected_module: str
    changes_made: list[str]
    expected_improvement: str
    status: str = "implemented"  # implemented, testing, verified, reverted


class ImprovementTracker:
    """改进追踪器 - 管理基于反馈的Agent迭代"""
    
    def __init__(self, storage_dir: str | None = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path(__file__).parent.parent.parent / ".agent" / "improvements"
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.iterations: list[ImprovementIteration] = []
        self._load_iterations()
    
    def _load_iterations(self):
        """加载已有迭代记录"""
        iter_file = self.storage_dir / "iterations.json"
        if iter_file.exists():
            try:
                with open(iter_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.iterations = [
                        ImprovementIteration(**item) for item in data.get("iterations", [])
                    ]
            except Exception:
                pass
    
    def _save_iterations(self):
        """保存迭代记录"""
        iter_file = self.storage_dir / "iterations.json"
        with open(iter_file, "w", encoding="utf-8") as f:
            json.dump({
                "last_updated": datetime.now().isoformat(),
                "iterations": [
                    {
                        "iteration_id": it.iteration_id,
                        "timestamp": it.timestamp,
                        "trigger_feedback_id": it.trigger_feedback_id,
                        "issue_description": it.issue_description,
                        "affected_module": it.affected_module,
                        "changes_made": it.changes_made,
                        "expected_improvement": it.expected_improvement,
                        "status": it.status,
                    }
                    for it in self.iterations
                ],
            }, f, ensure_ascii=False, indent=2)
    
    def record_iteration(
        self,
        trigger_feedback_id: str,
        issue_description: str,
        affected_module: str,
        changes_made: list[str],
        expected_improvement: str,
    ) -> ImprovementIteration:
        """记录一次改进迭代"""
        iteration = ImprovementIteration(
            iteration_id=f"iter-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            trigger_feedback_id=trigger_feedback_id,
            issue_description=issue_description,
            affected_module=affected_module,
            changes_made=changes_made,
            expected_improvement=expected_improvement,
            status="implemented",
        )
        self.iterations.append(iteration)
        self._save_iterations()
        return iteration
    
    def get_iterations(self, module: str | None = None) -> list[ImprovementIteration]:
        """获取迭代记录"""
        if module:
            return [it for it in self.iterations if it.affected_module == module]
        return self.iterations
    
    def generate_improvement_report(self) -> dict[str, Any]:
        """生成改进报告"""
        total = len(self.iterations)
        by_module = {}
        by_status = {}
        
        for it in self.iterations:
            # 按模块统计
            if it.affected_module not in by_module:
                by_module[it.affected_module] = 0
            by_module[it.affected_module] += 1
            
            # 按状态统计
            if it.status not in by_status:
                by_status[it.status] = 0
            by_status[it.status] += 1
        
        return {
            "total_iterations": total,
            "by_module": by_module,
            "by_status": by_status,
            "recent_iterations": [
                {
                    "id": it.iteration_id,
                    "module": it.affected_module,
                    "issue": it.issue_description[:50] + "..." if len(it.issue_description) > 50 else it.issue_description,
                    "status": it.status,
                    "timestamp": it.timestamp,
                }
                for it in self.iterations[-5:]  # 最近5次
            ],
        }
    
    def verify_iteration(self, iteration_id: str, new_rating: float | None = None):
        """验证迭代效果"""
        for it in self.iterations:
            if it.iteration_id == iteration_id:
                if new_rating and new_rating >= 4.0:
                    it.status = "verified"
                elif new_rating and new_rating < 3.0:
                    it.status = "needs_rework"
                else:
                    it.status = "testing"
                self._save_iterations()
                return it
        return None


# 全局实例
_default_tracker: ImprovementTracker | None = None


def get_improvement_tracker() -> ImprovementTracker:
    """获取全局改进追踪器"""
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = ImprovementTracker()
    return _default_tracker


def record_feedback_driven_iteration(
    feedback_id: str,
    issue: str,
    module: str,
    changes: list[str],
    expected: str,
) -> ImprovementIteration:
    """便捷的记录迭代函数"""
    tracker = get_improvement_tracker()
    return tracker.record_iteration(
        trigger_feedback_id=feedback_id,
        issue_description=issue,
        affected_module=module,
        changes_made=changes,
        expected_improvement=expected,
    )
