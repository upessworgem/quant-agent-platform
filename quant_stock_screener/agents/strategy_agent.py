"""
策略生成 Agent

负责从自然语言描述生成筛选策略
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class StrategyGenerationAgent(BaseAgent):
    """
    策略生成 Agent

    将用户的自然语言需求转化为结构化的筛选策略
    """

    def __init__(self, llm_client=None):
        super().__init__("strategy_generator", llm_client)

    def execute(self, natural_language_input: str, **kwargs) -> Dict[str, Any]:
        """
        从自然语言生成策略

        Args:
            natural_language_input: 用户的自然语言描述
            **kwargs: 其他参数

        Returns:
            策略配置字典，包含 name, description, conditions 等
        """
        if not self.is_available:
            return {"error": "LLM client not available"}

        prompt = self._build_prompt(natural_language_input)
        response = self._generate_response(prompt)

        if response is None:
            return {"error": "Failed to generate response"}

        return self._parse_response(response)

    def _build_prompt(self, user_input: str) -> str:
        """
        构建策略生成提示词

        Args:
            user_input: 用户输入

        Returns:
            格式化的提示词
        """
        return f"""你是一个专业的量化交易策略专家。

请根据以下描述，生成一个股票筛选策略的 JSON 配置。

描述: "{user_input}"

可用的技术指标字段:
- price: 当前价格 (元)
- turnover_rate: 换手率 (%)
- volume_ratio: 量比
- chip_concentration: 筹码集中度 (%), 越低表示筹码越集中
- consecutive_up: 是否连续上涨 (1=是, 0=否)
- volume: 成交量 (手)
- market_cap: 流通市值 (亿元)
- pe_ratio: 市盈率
- pb_ratio: 市净率

操作符选项: >, <, >=, <=, ==, between

请返回严格的 JSON 格式:
{{
  "name": "策略英文标识名",
  "description": "策略中文描述",
  "conditions": [
    {{
      "name": "显示名称",
      "field": "字段名",
      "operator": "操作符",
      "value": 数值,
      "value2": null,
      "enabled": true
    }}
  ],
  "sort_by": "用于排序的字段",
  "sort_desc": true,
  "max_stocks": null
}}

重要:
1. 只返回 JSON，不要 markdown 代码块
2. 不要添加任何解释文字
3. 确保 JSON 格式正确"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        解析 LLM 响应

        Args:
            response: LLM 响应文本

        Returns:
            解析后的策略字典
        """
        try:
            # 清理可能的 markdown 代码块
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(
                    lines[1:-1] if lines[-1].startswith("```") else lines[1:]
                )

            strategy = json.loads(cleaned)
            self.logger.info(f"成功生成策略: {strategy.get('name')}")
            return strategy

        except json.JSONDecodeError as e:
            self.logger.error(f"解析 JSON 失败: {e}")
            return {"error": "Invalid JSON response", "raw": response}

    def generate_strategy_suggestions(
        self, current_conditions: List[Dict], market_context: str = ""
    ) -> List[Dict]:
        """
        基于现有条件生成优化建议

        Args:
            current_conditions: 当前筛选条件
            market_context: 市场背景信息

        Returns:
            建议列表
        """
        if not self.is_available:
            return []

        prompt = f"""你是一个量化策略优化专家。

当前策略条件:
{json.dumps(current_conditions, ensure_ascii=False, indent=2)}

{f'市场背景: {market_context}' if market_context else ''}

请提供 3-5 条优化建议，包括:
1. 可以添加的条件
2. 参数调整建议
3. 风险控制建议

返回 JSON 数组格式:
[
  {{
    "type": "add_condition/adjust_param/risk_control",
    "suggestion": "建议内容",
    "reason": "原因"
  }}
]"""

        response = self._generate_response(prompt)
        if response is None:
            return []

        try:
            suggestions = json.loads(response.strip())
            return suggestions if isinstance(suggestions, list) else []
        except json.JSONDecodeError:
            return []
