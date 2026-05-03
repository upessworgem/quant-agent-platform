"""
策略模块 - 解耦策略定义与执行逻辑
支持灵活的条件组合和 AI 生成的策略
"""

import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from config import FilterCondition, StrategyConfig, ConfigManager

logger = logging.getLogger(__name__)


class Operator(Enum):
    """比较操作符"""
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    BETWEEN = "between"


class StrategyExecutor:
    """
    策略执行器 - 执行筛选逻辑
    完全解耦于数据源和 AI 模块
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self._operators: Dict[str, Callable] = {
            '>': lambda x, y: x is not None and y is not None and x > y,
            '<': lambda x, y: x is not None and y is not None and x < y,
            '>=': lambda x, y: x is not None and y is not None and x >= y,
            '<=': lambda x, y: x is not None and y is not None and x <= y,
            '==': lambda x, y: x is not None and y is not None and x == y,
            'between': lambda x, y, z: x is not None and y is not None and z is not None and y <= x <= z,
        }

    def _get_field_value(self, data: Dict, field: str) -> Any:
        """从数据中获取字段值，支持嵌套路径"""
        if field in data:
            return data[field]

        # 处理嵌套路径如 "finance.liutongguben"
        parts = field.split('.')
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value

    def evaluate_condition(self, condition: FilterCondition, data: Dict) -> bool:
        """评估单个条件"""
        if not condition.enabled:
            return True

        value = self._get_field_value(data, condition.field)
        if value is None:
            return False

        try:
            op_func = self._operators.get(condition.operator)
            if op_func is None:
                logger.warning(f"不支持的操作符: {condition.operator}")
                return False

            if condition.operator == 'between':
                return op_func(value, condition.value, condition.value2)
            else:
                return op_func(value, condition.value)

        except Exception as e:
            logger.warning(f"条件评估失败 {condition.field} {condition.operator} {condition.value}: {e}")
            return False

    def evaluate_strategy(self, strategy: StrategyConfig, data: Dict) -> bool:
        """评估整个策略（所有条件必须满足）"""
        for condition in strategy.conditions:
            if not self.evaluate_condition(condition, data):
                return False
        return True

    def filter_stocks(
        self,
        strategy: StrategyConfig,
        stock_data_list: List[Dict]
    ) -> List[Dict]:
        """
        批量筛选股票
        返回满足所有条件的股票列表
        """
        results = []
        total = len(stock_data_list)

        for i, data in enumerate(stock_data_list):
            code = data.get('code', 'unknown')
            name = data.get('name', 'unknown')

            try:
                if self.evaluate_strategy(strategy, data):
                    # 添加匹配的策略信息到结果
                    result = data.copy()
                    result['_matched_strategy'] = strategy.name
                    results.append(result)
                    logger.debug(f"✓ {name}({code}) 匹配策略 {strategy.name}")

            except Exception as e:
                logger.warning(f"评估 {name}({code}) 时出错: {e}")
                continue

            # 进度日志
            if (i + 1) % 500 == 0:
                logger.info(f"已处理 {i + 1}/{total} 只股票...")

        # 排序
        if strategy.sort_by and results:
            reverse = strategy.sort_desc
            results.sort(
                key=lambda x: x.get(strategy.sort_by, 0) or 0,
                reverse=reverse
            )

        # 限制数量
        if strategy.max_stocks and len(results) > strategy.max_stocks:
            results = results[:strategy.max_stocks]

        logger.info(f"策略 {strategy.name} 筛选完成: {len(results)}/{total} 只匹配")
        return results


class StrategyBuilder:
    """
    策略构建器 - 辅助创建策略
    """

    @staticmethod
    def create_momentum_strategy(
        min_turnover: float = 15,
        min_volume_ratio: float = 1.5,
        max_chip_concentration: float = 20
    ) -> StrategyConfig:
        """创建动量策略（原 tdxPj.py 的默认策略）"""
        return StrategyConfig(
            name="momentum",
            description="高换手+高量比+筹码集中+连续上涨",
            conditions=[
                FilterCondition("换手率", "turnover_rate", ">", min_turnover),
                FilterCondition("量比", "volume_ratio", ">", min_volume_ratio),
                FilterCondition("筹码集中度", "chip_concentration", "<", max_chip_concentration),
                FilterCondition("连续上涨", "consecutive_up", "==", 1),
            ]
        )

    @staticmethod
    def create_value_strategy(
        max_pe: float = 20,
        min_roe: float = 10
    ) -> StrategyConfig:
        """创建价值投资策略"""
        return StrategyConfig(
            name="value",
            description="低PE+高ROE",
            conditions=[
                FilterCondition("市盈率", "pe_ratio", "<", max_pe),
                FilterCondition("ROE", "roe", ">=", min_roe),
            ]
        )

    @staticmethod
    def create_breakout_strategy(
        min_volume_surge: float = 2.0,
        min_price_change: float = 5
    ) -> StrategyConfig:
        """创建突破策略"""
        return StrategyConfig(
            name="breakout",
            description="放量突破",
            conditions=[
                FilterCondition("量比", "volume_ratio", ">", min_volume_surge),
                FilterCondition("涨幅", "price_change_pct", ">", min_price_change),
            ]
        )


class CompositeStrategy:
    """
    组合策略 - 支持多策略组合（AND/OR 逻辑）
    """

    def __init__(self):
        self.strategies: List[StrategyConfig] = []
        self.mode: str = "OR"  # "AND" 或 "OR"

    def add_strategy(self, strategy: StrategyConfig):
        """添加子策略"""
        self.strategies.append(strategy)

    def evaluate(self, data: Dict, executor: StrategyExecutor) -> bool:
        """评估组合策略"""
        if not self.strategies:
            return True

        results = [
            executor.evaluate_strategy(s, data)
            for s in self.strategies
        ]

        if self.mode == "AND":
            return all(results)
        else:  # OR
            return any(results)


class StrategyBacktester:
    """
    策略回测器 - 简单的回测功能
    """

    def __init__(self, executor: StrategyExecutor):
        self.executor = executor

    def backtest(
        self,
        strategy: StrategyConfig,
        historical_data: List[Dict]
    ) -> Dict:
        """
        执行简单回测
        返回回测统计信息
        """
        matched = self.executor.filter_stocks(strategy, historical_data)

        total = len(historical_data)
        matched_count = len(matched)

        return {
            "total_stocks": total,
            "matched_count": matched_count,
            "match_rate": matched_count / total if total > 0 else 0,
            "avg_turnover_rate": sum(s.get('turnover_rate', 0) for s in matched) / matched_count if matched_count > 0 else 0,
            "avg_volume_ratio": sum(s.get('volume_ratio', 0) for s in matched) / matched_count if matched_count > 0 else 0,
        }
