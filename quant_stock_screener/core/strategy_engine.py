"""
策略引擎模块

负责策略的执行、构建和管理
"""

import logging
from enum import Enum
from typing import Callable, Dict, List, Optional

from ..config.settings import FilterCondition, StrategyConfig, Settings

logger = logging.getLogger(__name__)


class ComparisonOperator(Enum):
    """比较操作符枚举"""

    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    BETWEEN = "between"


class StrategyEngine:
    """
    策略执行引擎

    负责评估和执行筛选策略
    """

    def __init__(self, settings: Settings):
        """
        初始化策略引擎

        Args:
            settings: 全局配置
        """
        self.settings = settings
        self._operators: Dict[str, Callable] = {
            ">": lambda x, y: x is not None and y is not None and x > y,
            "<": lambda x, y: x is not None and y is not None and x < y,
            ">=": lambda x, y: x is not None and y is not None and x >= y,
            "<=": lambda x, y: x is not None and y is not None and x <= y,
            "==": lambda x, y: x is not None and y is not None and x == y,
            "between": lambda x, y, z: (
                x is not None and y is not None and z is not None and y <= x <= z
            ),
        }

    def _get_field_value(self, data: Dict, field_path: str):
        """
        从数据中获取字段值，支持嵌套路径

        Args:
            data: 数据字典
            field_path: 字段路径，如 "finance.pe_ratio"

        Returns:
            字段值
        """
        if field_path in data:
            return data[field_path]

        # 处理嵌套路径
        parts = field_path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None

        return value

    def evaluate_condition(self, condition: FilterCondition, data: Dict) -> bool:
        """
        评估单个筛选条件

        Args:
            condition: 筛选条件
            data: 股票数据

        Returns:
            是否满足条件
        """
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

            if condition.operator == "between":
                return op_func(value, condition.value, condition.value2)
            else:
                return op_func(value, condition.value)

        except Exception as e:
            logger.warning(
                f"条件评估失败 {condition.field} {condition.operator} {condition.value}: {e}"
            )
            return False

    def evaluate_strategy(self, strategy: StrategyConfig, data: Dict) -> bool:
        """
        评估整个策略（所有条件必须满足）

        Args:
            strategy: 策略配置
            data: 股票数据

        Returns:
            是否满足策略
        """
        for condition in strategy.conditions:
            if not self.evaluate_condition(condition, data):
                return False
        return True

    def filter_stocks(
        self, strategy: StrategyConfig, stock_data_list: List[Dict]
    ) -> List[Dict]:
        """
        批量筛选股票

        Args:
            strategy: 策略配置
            stock_data_list: 股票数据列表

        Returns:
            满足条件的股票列表
        """
        results = []
        total_count = len(stock_data_list)

        for index, data in enumerate(stock_data_list):
            stock_code = data.get("code", "unknown")
            stock_name = data.get("name", "unknown")

            try:
                if self.evaluate_strategy(strategy, data):
                    # 添加匹配信息
                    result = data.copy()
                    result["_matched_strategy"] = strategy.name
                    results.append(result)
                    logger.debug(f"✓ {stock_name}({stock_code}) 匹配策略")

            except Exception as e:
                logger.warning(f"评估 {stock_name}({stock_code}) 时出错: {e}")
                continue

            # 进度日志
            if (index + 1) % 500 == 0:
                logger.info(f"已处理 {index + 1}/{total_count} 只股票...")

        # 排序
        if strategy.sort_by and results:
            results.sort(
                key=lambda x: x.get(strategy.sort_by, 0) or 0,
                reverse=strategy.sort_desc,
            )

        # 限制数量
        if strategy.max_stocks and len(results) > strategy.max_stocks:
            results = results[: strategy.max_stocks]

        logger.info(
            f"策略 {strategy.name} 筛选完成: {len(results)}/{total_count} 只匹配"
        )
        return results


class StrategyBuilder:
    """
    策略构建器

    提供常用策略的快速构建方法
    """

    @staticmethod
    def create_momentum_strategy(
        min_turnover: float = 15.0,
        min_volume_ratio: float = 1.5,
        max_chip_concentration: float = 20.0,
    ) -> StrategyConfig:
        """
        创建动量策略

        选择高换手率、高量比、筹码集中且连续上涨的股票

        Args:
            min_turnover: 最小换手率（%）
            min_volume_ratio: 最小量比
            max_chip_concentration: 最大筹码集中度（%）

        Returns:
            策略配置
        """
        return StrategyConfig(
            name="momentum",
            description="高换手+高量比+筹码集中+连续上涨",
            conditions=[
                FilterCondition("换手率", "turnover_rate", ">", min_turnover),
                FilterCondition("量比", "volume_ratio", ">", min_volume_ratio),
                FilterCondition(
                    "筹码集中度", "chip_concentration", "<", max_chip_concentration
                ),
                FilterCondition("连续上涨", "consecutive_up", "==", 1),
            ],
        )

    @staticmethod
    def create_value_strategy(
        max_pe_ratio: float = 20.0, min_roe: float = 10.0
    ) -> StrategyConfig:
        """
        创建价值投资策略

        选择低市盈率、高 ROE 的股票

        Args:
            max_pe_ratio: 最大市盈率
            min_roe: 最小 ROE

        Returns:
            策略配置
        """
        return StrategyConfig(
            name="value",
            description="低PE+高ROE价值投资",
            conditions=[
                FilterCondition("市盈率", "pe_ratio", "<", max_pe_ratio),
                FilterCondition("ROE", "roe", ">=", min_roe),
            ],
        )

    @staticmethod
    def create_breakout_strategy(
        min_volume_surge: float = 2.0, min_price_change: float = 5.0
    ) -> StrategyConfig:
        """
        创建突破策略

        选择放量突破的股票

        Args:
            min_volume_surge: 最小量比
            min_price_change: 最小涨幅（%）

        Returns:
            策略配置
        """
        return StrategyConfig(
            name="breakout",
            description="放量突破",
            conditions=[
                FilterCondition("量比", "volume_ratio", ">", min_volume_surge),
                FilterCondition("涨幅", "price_change_pct", ">", min_price_change),
            ],
        )

    @staticmethod
    def create_custom_strategy(
        name: str, description: str, conditions: List[Dict]
    ) -> StrategyConfig:
        """
        创建自定义策略

        Args:
            name: 策略名称
            description: 策略描述
            conditions: 条件列表，每个条件包含 name, field, operator, value

        Returns:
            策略配置
        """
        filter_conditions = [
            FilterCondition(
                name=c.get("name", ""),
                field=c.get("field", ""),
                operator=c.get("operator", ">"),
                value=c.get("value", 0),
                value2=c.get("value2"),
                enabled=c.get("enabled", True),
            )
            for c in conditions
        ]

        return StrategyConfig(
            name=name, description=description, conditions=filter_conditions
        )
