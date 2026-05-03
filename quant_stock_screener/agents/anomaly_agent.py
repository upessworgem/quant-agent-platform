"""
异常检测 Agent

负责检测数据异常和可疑模式
"""

import json
import logging
from typing import Any, Dict, List

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AnomalyDetectionAgent(BaseAgent):
    """
    异常检测 Agent

    检测股票数据中的异常模式和潜在问题
    """

    def __init__(self, llm_client=None):
        super().__init__("anomaly_detector", llm_client)

    def execute(self, stock_data: List[Dict], **kwargs) -> List[Dict]:
        """
        检测数据异常

        Args:
            stock_data: 股票数据列表
            **kwargs: 其他参数

        Returns:
            异常列表，每个异常包含 code, issue, severity
        """
        if not self.is_available or len(stock_data) < 5:
            return []

        # 取样本数据进行分析
        sample = stock_data[:20]

        prompt = self._build_detection_prompt(sample)
        response = self._generate_response(prompt)

        if response is None:
            return []

        return self._parse_anomalies(response)

    def _build_detection_prompt(self, sample: List[Dict]) -> str:
        """
        构建异常检测提示词

        Args:
            sample: 样本数据

        Returns:
            格式化的提示词
        """
        return f"""分析以下股票数据，识别任何异常或值得关注的模式:

数据样本:
{json.dumps(sample, ensure_ascii=False, indent=2)}

请识别:
1. **换手率异常**: 换手率极高或极低的股票
2. **量比异常**: 量比异常大的股票
3. **数据合理性**: 数据看起来不合理或可能是错误
4. **潜在风险**: 需要警惕的异常模式

返回 JSON 数组格式:
[
  {{
    "code": "股票代码",
    "name": "股票名称",
    "issue": "问题描述",
    "severity": "high/medium/low",
    "suggestion": "处理建议"
  }}
]

如果没有异常，返回空数组 []"""

    def _parse_anomalies(self, response: str) -> List[Dict]:
        """
        解析异常检测结果

        Args:
            response: LLM 响应

        Returns:
            异常列表
        """
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(
                    lines[1:-1] if lines[-1].startswith("```") else lines[1:]
                )

            anomalies = json.loads(cleaned)
            return anomalies if isinstance(anomalies, list) else []
        except json.JSONDecodeError as e:
            self.logger.error(f"解析异常检测结果失败: {e}")
            return []

    def detect_market_anomalies(self, market_data: Dict) -> List[Dict]:
        """
        检测市场整体异常

        Args:
            market_data: 市场整体数据

        Returns:
            市场异常列表
        """
        if not self.is_available:
            return []

        prompt = f"""分析以下市场数据，识别整体市场异常:

市场数据:
{json.dumps(market_data, ensure_ascii=False, indent=2)}

请识别:
1. 市场情绪异常 (过度乐观/悲观)
2. 板块轮动异常
3. 成交量异常
4. 其他需要注意的市场信号

返回 JSON 数组格式的异常列表。"""

        response = self._generate_response(prompt)
        if response is None:
            return []

        return self._parse_anomalies(response)
