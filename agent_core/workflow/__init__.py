"""Workflow module for MA Agent - 端到端工作流自动化"""
from __future__ import annotations

from agent_core.workflow.engine import WorkflowEngine, WorkflowContext
from agent_core.workflow.marketing_workflow import MarketingWorkflow

__all__ = [
    "WorkflowEngine",
    "WorkflowContext", 
    "MarketingWorkflow",
]
