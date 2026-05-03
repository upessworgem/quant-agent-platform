"""
AI/LLM 分析模块 - 解耦 AI 功能与核心业务逻辑
提供策略生成、结果分析、异常检测等 AI 能力
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import asdict

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端基类 - 支持多种 LLM 提供商"""

    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError


class AnthropicClient(LLMClient):
    """Anthropic Claude 客户端"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.error("anthropic 包未安装，请运行: pip install anthropic")
                raise
        return self._client

    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API 调用失败: {e}")
            raise


class OpenAIClient(LLMClient):
    """OpenAI GPT 客户端"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("openai 包未安装，请运行: pip install openai")
                raise
        return self._client

    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            raise


class MockLLMClient(LLMClient):
    """模拟 LLM 客户端 - 用于测试或无 AI 环境"""

    def generate(self, prompt: str, **kwargs) -> str:
        logger.warning("使用模拟 LLM 客户端，返回空响应")
        return json.dumps({
            "name": "mock_strategy",
            "description": "模拟策略",
            "conditions": []
        })


class AIAnalyzer:
    """
    AI 分析器 - 核心 AI 介入点
    解耦 AI 分析逻辑与股票筛选逻辑
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client
        self.analysis_history: List[Dict] = []

    def set_llm_client(self, client: LLMClient):
        """设置或更换 LLM 客户端"""
        self.llm = client

    def is_available(self) -> bool:
        """检查 AI 是否可用"""
        return self.llm is not None

    # ========== AI 介入点 1: 策略生成 ==========

    def generate_strategy_from_natural_language(self, description: str) -> Dict:
        """
        从自然语言描述生成策略配置
        这是主要的 AI 介入点
        """
        if not self.is_available():
            logger.warning("LLM 未配置，无法生成策略")
            return {"error": "LLM not available"}

        prompt = f"""你是一个专业的量化交易策略专家。

请根据以下描述，生成一个股票筛选策略的 JSON 配置:

描述: "{description}"

可用的技术指标字段:
- price: 当前价格 (元)
- turnover_rate: 换手率 (%)
- volume_ratio: 量比
- chip_concentration: 筹码集中度 (%), 越低表示筹码越集中
- consecutive_up: 是否连续上涨 (1=是, 0=否)
- volume: 成交量 (手)
- market_cap: 流通市值 (亿元)

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

        try:
            response = self.llm.generate(prompt)
            # 清理可能的 markdown 代码块
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

            strategy = json.loads(response)
            self.analysis_history.append({
                "type": "strategy_generation",
                "input": description,
                "output": strategy
            })
            logger.info(f"AI 生成策略: {strategy.get('name')}")
            return strategy

        except json.JSONDecodeError as e:
            logger.error(f"AI 返回无效 JSON: {e}")
            return {"error": "Invalid JSON from AI", "raw": response}
        except Exception as e:
            logger.error(f"策略生成失败: {e}")
            return {"error": str(e)}

    # ========== AI 介入点 2: 结果分析 ==========

    def analyze_results(self, results: List[Dict], market_context: Optional[str] = None) -> str:
        """
        分析筛选结果，生成投资建议
        第二个重要的 AI 介入点
        """
        if not self.is_available() or not results:
            return "AI 分析不可用或无结果"

        results_summary = json.dumps(results, ensure_ascii=False, indent=2)
        market_info = f"\n市场背景: {market_context}" if market_context else ""

        prompt = f"""你是一位专业的股票分析师。请分析以下筛选出的股票，并提供投资建议。

筛选结果 (JSON 格式):
{results_summary}
{market_info}

请从以下几个角度分析:
1. 这些股票的共同特征
2. 潜在的投资机会和风险
3. 建议的仓位控制和操作策略
4. 需要进一步关注的时间节点或事件

请用中文回答，语言简洁专业。"""

        try:
            analysis = self.llm.generate(prompt, max_tokens=3000)
            self.analysis_history.append({
                "type": "result_analysis",
                "input_count": len(results),
                "output": analysis
            })
            return analysis

        except Exception as e:
            logger.error(f"结果分析失败: {e}")
            return f"AI 分析失败: {e}"

    # ========== AI 介入点 3: 异常检测 ==========

    def detect_anomalies(self, stock_data: List[Dict]) -> List[Dict]:
        """
        检测数据中的异常模式
        第三个 AI 介入点
        """
        if not self.is_available() or len(stock_data) < 5:
            return []

        # 提取关键指标样本
        sample = [
            {
                "code": d.get("code"),
                "name": d.get("name"),
                "turnover_rate": d.get("turnover_rate"),
                "volume_ratio": d.get("volume_ratio"),
                "chip_concentration": d.get("chip_concentration"),
            }
            for d in stock_data[:20]  # 只取前20条避免 token 过多
        ]

        prompt = f"""分析以下股票数据，识别任何异常或值得关注的模式:

数据样本:
{json.dumps(sample, ensure_ascii=False, indent=2)}

请识别:
1. 换手率异常高的股票
2. 量比异常的股票
3. 数据看起来不合理或可能的错误
4. 任何值得人工复核的情况

返回 JSON 数组格式:
[{{
  "code": "股票代码",
  "issue": "问题描述",
  "severity": "high/medium/low"
}}]

如果没有异常，返回空数组 []"""

        try:
            response = self.llm.generate(prompt)
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

            anomalies = json.loads(response)
            return anomalies if isinstance(anomalies, list) else []

        except Exception as e:
            logger.error(f"异常检测失败: {e}")
            return []

    # ========== AI 介入点 4: 策略优化建议 ==========

    def suggest_strategy_improvements(self, current_strategy: Dict, backtest_results: Optional[Dict] = None) -> str:
        """
        基于回测结果给出策略优化建议
        第四个 AI 介入点
        """
        if not self.is_available():
            return "AI 不可用"

        backtest_info = ""
        if backtest_results:
            backtest_info = f"\n回测结果:\n{json.dumps(backtest_results, ensure_ascii=False, indent=2)}"

        prompt = f"""你是一位量化交易策略优化专家。

当前策略配置:
{json.dumps(current_strategy, ensure_ascii=False, indent=2)}
{backtest_info}

请给出以下建议:
1. 当前策略可能的改进方向
2. 应该增加或删除哪些筛选条件
3. 参数调优的建议
4. 风险提示

请用中文回答。"""

        try:
            suggestions = self.llm.generate(prompt, max_tokens=2000)
            return suggestions
        except Exception as e:
            logger.error(f"策略优化建议失败: {e}")
            return f"获取建议失败: {e}"

    def get_analysis_summary(self) -> Dict:
        """获取分析历史摘要"""
        return {
            "total_analyses": len(self.analysis_history),
            "by_type": {
                "strategy_generation": len([a for a in self.analysis_history if a["type"] == "strategy_generation"]),
                "result_analysis": len([a for a in self.analysis_history if a["type"] == "result_analysis"]),
            }
        }


# 工厂函数
def create_llm_client(provider: str, api_key: str, model: Optional[str] = None) -> LLMClient:
    """创建 LLM 客户端"""
    if provider == "anthropic":
        return AnthropicClient(api_key, model or "claude-sonnet-4-6")
    elif provider == "openai":
        return OpenAIClient(api_key, model or "gpt-4")
    elif provider == "mock":
        return MockLLMClient()
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")
