"""工作流引擎 - 定义和执行工作流"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class WorkflowContext:
    """工作流上下文 - 存储工作流执行过程中的数据"""
    # 输入数据
    input_data: dict[str, Any] = field(default_factory=dict)
    
    # 各阶段输出
    stage_outputs: dict[str, Any] = field(default_factory=dict)
    
    # 执行状态
    current_stage: str = ""
    completed_stages: list[str] = field(default_factory=list)
    failed_stages: list[str] = field(default_factory=list)
    
    # 执行元数据
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    execution_log: list[dict] = field(default_factory=list)
    
    def log(self, stage: str, action: str, data: Any = None):
        """记录执行日志"""
        self.execution_log.append({
            "timestamp": time.time(),
            "stage": stage,
            "action": action,
            "data": data,
        })
    
    def set_stage_output(self, stage: str, output: Any):
        """设置阶段输出"""
        self.stage_outputs[stage] = output
        self.completed_stages.append(stage)
    
    def get_stage_output(self, stage: str) -> Any:
        """获取阶段输出"""
        return self.stage_outputs.get(stage)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "input_data": self.input_data,
            "stage_outputs": self.stage_outputs,
            "completed_stages": self.completed_stages,
            "failed_stages": self.failed_stages,
            "duration": self.end_time - self.start_time if self.end_time else None,
            "execution_log": self.execution_log,
        }


class WorkflowStage(ABC):
    """工作流阶段基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, context: WorkflowContext) -> dict[str, Any]:
        """执行阶段任务"""
        pass
    
    def __call__(self, context: WorkflowContext) -> dict[str, Any]:
        """调用执行"""
        context.current_stage = self.name
        context.log(self.name, "started")
        
        try:
            result = self.execute(context)
            context.set_stage_output(self.name, result)
            context.log(self.name, "completed", result)
            return result
        except Exception as e:
            context.failed_stages.append(self.name)
            context.log(self.name, "failed", str(e))
            raise


class WorkflowEngine:
    """工作流引擎 - 管理和执行工作流"""
    
    def __init__(self, name: str):
        self.name = name
        self.stages: list[WorkflowStage] = []
        self.on_stage_complete: Callable | None = None
        self.on_stage_fail: Callable | None = None
    
    def add_stage(self, stage: WorkflowStage) -> "WorkflowEngine":
        """添加工作流阶段"""
        self.stages.append(stage)
        return self
    
    def set_callbacks(
        self,
        on_complete: Callable | None = None,
        on_fail: Callable | None = None,
    ) -> "WorkflowEngine":
        """设置回调函数"""
        self.on_stage_complete = on_complete
        self.on_stage_fail = on_fail
        return self
    
    def execute(self, input_data: dict[str, Any]) -> WorkflowContext:
        """执行工作流"""
        context = WorkflowContext(input_data=input_data)
        
        for stage in self.stages:
            try:
                result = stage(context)
                if self.on_stage_complete:
                    self.on_stage_complete(stage.name, result)
            except Exception as e:
                if self.on_stage_fail:
                    self.on_stage_fail(stage.name, str(e))
                # 继续执行或停止，根据配置
                raise
        
        context.end_time = time.time()
        return context
    
    def execute_async(self, input_data: dict[str, Any]) -> "WorkflowExecution":
        """异步执行工作流"""
        return WorkflowExecution(self, input_data)


class WorkflowExecution:
    """工作流执行句柄（支持异步）"""
    
    def __init__(self, engine: WorkflowEngine, input_data: dict[str, Any]):
        self.engine = engine
        self.input_data = input_data
        self.context: WorkflowContext | None = None
        self._cancelled = False
    
    def run(self) -> WorkflowContext:
        """运行工作流"""
        if self._cancelled:
            raise RuntimeError("Workflow was cancelled")
        self.context = self.engine.execute(self.input_data)
        return self.context
    
    def cancel(self):
        """取消工作流"""
        self._cancelled = True
    
    def get_progress(self) -> dict:
        """获取执行进度"""
        if not self.context:
            return {"status": "not_started", "progress": 0}
        
        total = len(self.engine.stages)
        completed = len(self.context.completed_stages)
        
        return {
            "status": "completed" if self.context.end_time else "running",
            "progress": completed / total if total > 0 else 0,
            "current_stage": self.context.current_stage,
            "completed_stages": self.context.completed_stages,
        }
