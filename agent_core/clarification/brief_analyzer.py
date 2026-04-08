"""Brief分析器 - 识别信息缺失"""
from __future__ import annotations

from typing import Any


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
