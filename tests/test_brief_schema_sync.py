"""Brief 解析 Schema 同步测试。

如果以下任何一条失败，说明你在修改 Brief 解析字段时前后端没有同步更新。
修复步骤：
1. 更新 agent_core/models/brief.py 里的 BriefParseResult
2. 更新 agent_core/tools/strategy_iq.py 的解析逻辑
3. 更新 web_api.py 的字段映射
4. 更新 web/index.html 的 autoFillForm / showExtractedPreview
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from agent_core.models import BriefParseResult
from agent_core.tools.strategy_iq import _rule_based_parse, parse_brief


PROJECT_ROOT = Path(__file__).parent.parent


class TestBriefParseResultCompleteness(unittest.TestCase):
    """确保底层解析器返回的 dict 包含模型定义的所有字段。"""

    def test_rule_based_parse_returns_all_model_fields(self):
        result = _rule_based_parse("Nike Aero-Fit 系列，世界杯主题传播，预算100万")
        model_fields = BriefParseResult.get_all_field_names()
        self.assertTrue(
            model_fields.issubset(set(result.keys())),
            f"_rule_based_parse 返回值缺少字段: {model_fields - set(result.keys())}",
        )

    @patch("agent_core.llm.get_llm_client")
    def test_parse_brief_fallback_returns_all_model_fields(self, mock_get_client):
        """模拟 LLM 返回弱结果触发 fallback，依然保证字段完整。"""
        mock_client = MagicMock()
        # 弱结果会触发 _is_weak_parse_result -> fallback
        mock_client.complete.return_value = {
            "brand": "",
            "industry": "",
            "key_messages": [],
            "preferred_platforms": [],
        }
        mock_get_client.return_value = mock_client

        result = parse_brief("Nike Aero-Fit 世界杯")
        model_fields = BriefParseResult.get_all_field_names()
        self.assertTrue(
            model_fields.issubset(set(result.keys())),
            f"parse_brief fallback 返回值缺少字段: {model_fields - set(result.keys())}",
        )


class TestBackendSchemaSync(unittest.TestCase):
    """检查后端 web_api.py 是否正确引用了所有核心字段。"""

    def test_analyze_brief_endpoint_uses_expected_fields(self):
        web_api_path = PROJECT_ROOT / "web_api.py"
        self.assertTrue(web_api_path.exists(), "web_api.py 不存在")
        content = web_api_path.read_text(encoding="utf-8")

        # 提取 parsed.get("xxx") 或 parsed.get('xxx')
        referenced = set(re.findall(r'parsed\.get\(["\'](\w+)["\']', content))

        core_fields = {"brand", "product", "goal", "budget_amount", "theme", "key_messages"}
        missing = core_fields - referenced
        self.assertFalse(
            missing,
            f"web_api.py 的 /api/analyze-brief 缺少对核心字段的引用: {missing}\n"
            f"请确保每个核心字段都被显式映射到前端返回结构中。",
        )


class TestFrontendSchemaSync(unittest.TestCase):
    """检查前端 HTML/JS 是否正确消费了所有核心字段。"""

    def test_web_index_uses_expected_fields(self):
        html_path = PROJECT_ROOT / "web" / "index.html"
        self.assertTrue(html_path.exists(), "web/index.html 不存在")
        content = html_path.read_text(encoding="utf-8")

        # 提取 briefInfo.xxx
        referenced = set(re.findall(r'briefInfo\.(\w+)', content))

        # features 是 web_api.py 将 key_messages join 后的前端字段名
        core_fields = {"brand", "product", "goal", "budget", "theme", "features", "session_path"}
        missing = core_fields - referenced
        self.assertFalse(
            missing,
            f"web/index.html 缺少对核心字段的消费: {missing}\n"
            f"请更新 autoFillForm / showExtractedPreview 等函数。",
        )


if __name__ == "__main__":
    unittest.main()
