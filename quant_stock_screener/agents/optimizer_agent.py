"""
策略优化 Agent

负责基于历史数据优化筛选策略
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class StrategyOptimizerAgent(BaseAgent):
    """
    策略优化 Agent

    分析历史表现，提供策略优化建议
    """

    def __init__(self, llm_client=None):
        super().__init__("strategy_optimizer", llm_client)

    def execute(
        self,
        current_strategy: Dict,
        backtest_results: Optional[Dict] = None,
        **kwargs,
    ) -> str:
        """
        生成策略优化建议

        Args:
            current_strategy: 当前策略配置
            backtest_results: 回测结果
            **kwargs: 其他参数

        Returns:
            优化建议文本
        """
        if not self.is_available:
            return "AI 优化建议不可用"

        prompt = self._build_optimization_prompt(current_strategy, backtest_results)
        suggestions = self._generate_response(prompt, max_tokens=2000)

        return suggestions or "优化建议生成失败"

    def _build_optimization_prompt(
        self, current_strategy: Dict, backtest_results: Optional[Dict]
    ) -> str:
        """
        构建优化提示词

        Args:
            current_strategy: 当前策略
            backtest_results: 回测结果

        Returns:
            格式化的提示词
        """
        backtest_info = ""
        if backtest_results:
            backtest_info = f"\n回测结果:\n{json.dumps(backtest_results, ensure_ascii=False, indent=2)}"

        return f"""你是一位量化交易策略优化专家。

当前策略配置:
{json.dumps(current_strategy, ensure_ascii=False, indent=2)}
{backtest_info}

请给出以下建议:

1. **参数调优**: 当前参数是否合理？如何调整？
2. **条件优化**: 应该增加或删除哪些条件？
3. **风险控制**: 如何更好地控制风险？
4. **预期收益**: 优化后的预期表现如何？

请用中文回答，给出具体可操作的建议。"""

    def suggest_parameter_adjustments(
        self, strategy_conditions: List[Dict], performance_metrics: Dict
    ) -> List[Dict]:
        """
        建议参数调整

        Args:
            strategy_conditions: 当前条件列表
            performance_metrics: 表现指标

        Returns:
            参数调整建议列表
        """
        if not self.is_available:
            return []

        prompt = f"""基于以下策略条件和表现指标，建议参数调整:

当前条件:
{json.dumps(strategy_conditions, ensure_ascii=False, indent=2)}

表现指标:
{json.dumps(performance_metrics, ensure_ascii=False, indent=2)}

返回 JSON 数组格式的建议:
[
  {{
    "condition_name": "条件名称",
    "current_value": 当前值,
    "suggested_value": 建议值,
    "reason": "调整原因"
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

    def generate_risk_assessment(
        self, strategy: Dict, market_conditions: Dict
    ) -> Dict:
        """
        生成风险评估报告

        Args:
            strategy: 策略配置
            market_conditions: 市场状况

        Returns:
            风险评估报告
        """
        if not self.is_available:
            return {"error": "AI 不可用"}

        prompt = f"""评估以下策略在当前市场条件下的风险:

策略:
{json.dumps(strategy, ensure_ascii=False, indent=2)}

市场条件:
{json.dumps(market_conditions, ensure_ascii=False, indent=2)}

返回 JSON 格式的风险评估:
{{
  "risk_level": "high/medium/low",
  "risk_factors": ["风险因素1", "风险因素2"],
  "mitigation": ["应对措施1", "应对措施2"],
  "confidence": 0.8
}}"""

        response = self._generate_response(prompt)
        if response is None:
            return {"error": "评估失败"}

        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {"error": "解析失败"}
