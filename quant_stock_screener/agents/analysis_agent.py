"""
结果分析 Agent

负责分析筛选结果，生成投资建议
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ResultAnalysisAgent(BaseAgent):
    """
    结果分析 Agent

    对筛选结果进行深度分析，提供投资建议
    """

    def __init__(self, llm_client=None):
        super().__init__("result_analyzer", llm_client)

    def execute(
        self, results: List[Dict], market_context: Optional[str] = None, **kwargs
    ) -> str:
        """
        分析筛选结果

        Args:
            results: 筛选结果列表
            market_context: 市场背景信息
            **kwargs: 其他参数

        Returns:
            分析报告文本
        """
        if not self.is_available:
            return "AI 分析不可用"

        if not results:
            return "无筛选结果可分析"

        prompt = self._build_analysis_prompt(results, market_context)
        analysis = self._generate_response(prompt, max_tokens=3000)

        return analysis or "分析生成失败"

    def _build_analysis_prompt(
        self, results: List[Dict], market_context: Optional[str]
    ) -> str:
        """
        构建分析提示词

        Args:
            results: 筛选结果
            market_context: 市场背景

        Returns:
            格式化的提示词
        """
        # 提取关键指标
        results_summary = json.dumps(results[:20], ensure_ascii=False, indent=2)
        market_info = f"\n市场背景: {market_context}" if market_context else ""

        return f"""你是一位专业的股票分析师。请分析以下筛选出的股票，并提供投资建议。

筛选结果 (JSON 格式):
{results_summary}
{market_info}

请从以下几个角度分析:
1. **共同特征分析**: 这些股票有什么共同点？
2. **投资机会**: 哪些股票值得关注？为什么？
3. **风险提示**: 存在哪些潜在风险？
4. **仓位建议**: 建议的仓位分配策略
5. **操作策略**: 短期和中期的操作建议

请用中文回答，语言简洁专业，重点突出。"""

    def generate_stock_report(self, stock_data: Dict) -> str:
        """
        为单只股票生成分析报告

        Args:
            stock_data: 股票数据

        Returns:
            分析报告
        """
        if not self.is_available:
            return "AI 分析不可用"

        prompt = f"""请分析以下股票，并给出简要评价:

股票信息:
{json.dumps(stock_data, ensure_ascii=False, indent=2)}

请从以下角度分析:
1. 技术面: 量价关系、趋势判断
2. 基本面: 估值水平、盈利能力
3. 操作建议: 买入/持有/卖出，以及理由

简明扼要，不超过 200 字。"""

        return self._generate_response(prompt) or "分析生成失败"

    def compare_stocks(self, stocks: List[Dict]) -> str:
        """
        对比分析多只股票

        Args:
            stocks: 股票数据列表

        Returns:
            对比分析结果
        """
        if not self.is_available or len(stocks) < 2:
            return "需要至少两只股票进行对比"

        prompt = f"""请对比分析以下股票:

{json.dumps(stocks, ensure_ascii=False, indent=2)}

请从以下维度进行对比:
1. 估值水平 (PE, PB)
2. 成交活跃度 (换手率, 量比)
3. 技术形态 (筹码集中度, 趋势)
4. 综合评分和排名

返回简明的对比表格和结论。"""

        return self._generate_response(prompt) or "对比分析失败"
