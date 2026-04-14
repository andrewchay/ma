"""Brief解析结果的数据模型 —— 前后端字段的单一数据源。

任何新增/修改 Brief 解析字段时，必须：
1. 先更新 BriefParseResult
2. 再更新 `agent_core/tools/strategy_iq.py` 中的解析逻辑
3. 最后更新前端 `web/index.html` 的 autoFillForm/showExtractedPreview
4. 运行 `python -m pytest tests/test_brief_schema_sync.py` 确保通过
"""
from __future__ import annotations

from typing import Union

from pydantic import BaseModel, Field


class BriefParseResult(BaseModel):
    """Brief 解析后的标准输出结构。"""

    brand: str = Field(default="", description="品牌名称")
    product: str = Field(default="", description="产品名称/系列名称（如：Aero-Fit系列、新品口红等）")
    industry: str = Field(default="", description="行业类别（美妆/3C/快消/母婴/时尚/食品等）")
    goal: str = Field(default="", description="营销目标（品牌曝光/产品认知/种草/转化/销售）")
    budget: str = Field(default="", description="预算级别（高/中高/中等/低）")
    budget_amount: Union[str, int] = Field(default="", description="预算金额数值或'待商议'")
    timeline: str = Field(default="", description="执行周期")
    target_audience: str = Field(default="", description="目标受众描述")
    key_messages: list[str] = Field(default_factory=list, description="关键传播信息列表")
    theme: str = Field(default="", description="传播主题/借势热点（如：世界杯主题、春节营销等）")
    preferred_platforms: list[str] = Field(default_factory=list, description="首选平台列表")
    constraints: str = Field(default="", description="特殊要求或限制")
    is_overseas: bool = Field(default=False, description="是否海外投放")

    @classmethod
    def get_prompt_schema_text(cls) -> str:
        """为 LLM prompt 生成 JSON schema 说明文本。"""
        return """{
    "brand": "品牌名称",
    "product": "产品名称/系列名称（如：Aero-Fit系列、新品口红等）",
    "industry": "行业类别（美妆/3C/快消/母婴/时尚/食品等）",
    "goal": "营销目标（品牌曝光/产品认知/种草/转化/销售）",
    "budget": "预算级别（高/中高/中等/低），根据金额判断：>100万=高，50-100万=中高，20-50万=中等，<20万=低",
    "budget_amount": "预算金额数值或待商议",
    "timeline": "执行周期",
    "target_audience": "目标受众描述",
    "key_messages": ["关键传播信息1", "关键传播信息2"],
    "theme": "传播主题/借势热点（如：世界杯主题、春节营销等）",
    "preferred_platforms": ["首选平台1", "首选平台2"],
    "constraints": "特殊要求或限制",
    "is_overseas": false
}"""

    @classmethod
    def get_all_field_names(cls) -> set[str]:
        return set(cls.model_fields.keys())
