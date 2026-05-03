"""
Agent 协调器

负责协调多个 Agent 协作完成复杂任务
"""

import logging
from typing import Any, Dict, List, Optional

from .strategy_agent import StrategyGenerationAgent
from .analysis_agent import ResultAnalysisAgent
from .anomaly_agent import AnomalyDetectionAgent
from .optimizer_agent import StrategyOptimizerAgent

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """
    Agent 协调器

    协调多个 Agent 协作，实现复杂的 AI 驱动工作流
    """

    def __init__(self, llm_client=None):
        """
        初始化协调器

        Args:
            llm_client: LLM 客户端实例
        """
        self.llm_client = llm_client

        # 初始化所有 Agent
        self.strategy_agent = StrategyGenerationAgent(llm_client)
        self.analysis_agent = ResultAnalysisAgent(llm_client)
        self.anomaly_agent = AnomalyDetectionAgent(llm_client)
        self.optimizer_agent = StrategyOptimizerAgent(llm_client)

        self.logger = logging.getLogger("agent.coordinator")

    def set_llm_client(self, llm_client):
        """设置 LLM 客户端并更新所有 Agent"""
        self.llm_client = llm_client
        self.strategy_agent.set_llm_client(llm_client)
        self.analysis_agent.set_llm_client(llm_client)
        self.anomaly_agent.set_llm_client(llm_client)
        self.optimizer_agent.set_llm_client(llm_client)

    @property
    def is_available(self) -> bool:
        """检查协调器是否可用"""
        return self.llm_client is not None

    def get_all_agents_status(self) -> List[Dict]:
        """获取所有 Agent 的状态"""
        return [
            self.strategy_agent.get_status(),
            self.analysis_agent.get_status(),
            self.anomaly_agent.get_status(),
            self.optimizer_agent.get_status(),
        ]

    # ========== 完整工作流 ==========

    def full_screening_workflow(
        self,
        natural_language_input: str,
        stock_data: List[Dict],
        market_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        完整的筛选工作流

        1. 从自然语言生成策略
        2. 执行筛选（需要外部调用）
        3. 检测异常
        4. 分析结果

        Args:
            natural_language_input: 自然语言策略描述
            stock_data: 股票数据
            market_context: 市场背景

        Returns:
            工作流结果
        """
        results = {
            "strategy": None,
            "anomalies": [],
            "analysis": None,
            "errors": [],
        }

        # 步骤 1: 生成策略
        self.logger.info("步骤 1: 生成筛选策略")
        strategy = self.strategy_agent.execute(natural_language_input)
        if "error" in strategy:
            results["errors"].append(f"策略生成失败: {strategy['error']}")
            return results
        results["strategy"] = strategy

        # 步骤 2: 检测数据异常
        self.logger.info("步骤 2: 检测数据异常")
        anomalies = self.anomaly_agent.execute(stock_data)
        results["anomalies"] = anomalies

        if anomalies:
            high_severity = [a for a in anomalies if a.get("severity") == "high"]
            if high_severity:
                results["errors"].append(f"发现 {len(high_severity)} 个高严重度异常")

        # 步骤 3: 分析结果（如果有筛选结果）
        # 注意：实际筛选需要外部执行，这里只分析原始数据
        self.logger.info("步骤 3: 生成数据洞察")
        analysis = self.analysis_agent.execute(
            stock_data[:50],  # 只分析前 50 条
            market_context=market_context,
        )
        results["analysis"] = analysis

        return results

    def optimize_strategy_workflow(
        self,
        current_strategy: Dict,
        historical_results: List[Dict],
        market_conditions: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        策略优化工作流

        1. 分析历史表现
        2. 生成优化建议
        3. 评估风险

        Args:
            current_strategy: 当前策略
            historical_results: 历史筛选结果
            market_conditions: 市场条件

        Returns:
            优化建议
        """
        results = {
            "suggestions": None,
            "parameter_adjustments": [],
            "risk_assessment": None,
        }

        # 计算历史表现指标
        performance_metrics = self._calculate_performance(historical_results)

        # 生成优化建议
        self.logger.info("生成策略优化建议")
        suggestions = self.optimizer_agent.execute(
            current_strategy, backtest_results=performance_metrics
        )
        results["suggestions"] = suggestions

        # 参数调整建议
        self.logger.info("生成参数调整建议")
        adjustments = self.optimizer_agent.suggest_parameter_adjustments(
            current_strategy.get("conditions", []), performance_metrics
        )
        results["parameter_adjustments"] = adjustments

        # 风险评估
        if market_conditions:
            self.logger.info("生成风险评估")
            risk = self.optimizer_agent.generate_risk_assessment(
                current_strategy, market_conditions
            )
            results["risk_assessment"] = risk

        return results

    def _calculate_performance(self, results: List[Dict]) -> Dict:
        """
        计算历史表现指标

        Args:
            results: 历史结果列表

        Returns:
            表现指标字典
        """
        if not results:
            return {}

        total = len(results)
        successful = len([r for r in results if r.get("status") == "success"])
        avg_matched = (
            sum(r.get("matched_count", 0) for r in results) / total if total > 0 else 0
        )

        return {
            "total_screenings": total,
            "success_rate": successful / total if total > 0 else 0,
            "avg_matched_stocks": avg_matched,
        }

    # ========== 单独 Agent 调用 ==========

    def generate_strategy(self, description: str) -> Dict:
        """调用策略生成 Agent"""
        return self.strategy_agent.execute(description)

    def analyze_results(
        self, results: List[Dict], context: Optional[str] = None
    ) -> str:
        """调用结果分析 Agent"""
        return self.analysis_agent.execute(results, context)

    def detect_anomalies(self, data: List[Dict]) -> List[Dict]:
        """调用异常检测 Agent"""
        return self.anomaly_agent.execute(data)

    def get_optimization_suggestions(
        self, strategy: Dict, backtest: Optional[Dict] = None
    ) -> str:
        """调用策略优化 Agent"""
        return self.optimizer_agent.execute(strategy, backtest)
