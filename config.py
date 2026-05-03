"""
配置中心模块 - 统一管理所有配置和策略定义
支持从文件、环境变量或 LLM 生成加载配置
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


@dataclass
class FilterCondition:
    """单个筛选条件"""
    name: str
    field: str
    operator: str  # '>', '<', '>=', '<=', '==', 'between'
    value: float
    value2: Optional[float] = None  # 用于 between 操作符
    enabled: bool = True


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    description: str
    conditions: List[FilterCondition]
    max_stocks: Optional[int] = None
    sort_by: Optional[str] = None
    sort_desc: bool = True


@dataclass
class AIConfig:
    """AI/LLM 配置"""
    enabled: bool = False
    provider: str = "anthropic"  # anthropic, openai, local
    api_key: Optional[str] = None
    model: str = "claude-sonnet-4-6"
    analyze_results: bool = True
    generate_strategy: bool = False
    natural_language_input: Optional[str] = None


@dataclass
class AppConfig:
    """应用全局配置"""
    stock_list_file: str = "stock_list.txt"
    output_format: str = "table"  # table, json, csv
    log_level: str = "INFO"
    save_results: bool = False
    results_file: Optional[str] = None


class ConfigManager:
    """配置管理器 - 解耦配置加载与业务逻辑"""

    def __init__(self):
        self.app = AppConfig()
        self.ai = AIConfig()
        self.strategy: Optional[StrategyConfig] = None
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        if api_key := os.getenv("ANTHROPIC_API_KEY"):
            self.ai.api_key = api_key
            self.ai.enabled = True
        if model := os.getenv("AI_MODEL"):
            self.ai.model = model
        if nl_input := os.getenv("STRATEGY_DESCRIPTION"):
            self.ai.natural_language_input = nl_input
            self.ai.generate_strategy = True

    def load_strategy_from_file(self, filepath: str) -> StrategyConfig:
        """从 JSON 文件加载策略"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            conditions = [
                FilterCondition(**c) for c in data.get('conditions', [])
            ]

            self.strategy = StrategyConfig(
                name=data.get('name', 'unnamed'),
                description=data.get('description', ''),
                conditions=conditions,
                max_stocks=data.get('max_stocks'),
                sort_by=data.get('sort_by'),
                sort_desc=data.get('sort_desc', True)
            )
            logger.info(f"已加载策略: {self.strategy.name}")
            return self.strategy

        except FileNotFoundError:
            logger.warning(f"策略文件不存在: {filepath}")
            return self._default_strategy()
        except Exception as e:
            logger.error(f"加载策略失败: {e}")
            return self._default_strategy()

    def _default_strategy(self) -> StrategyConfig:
        """默认策略（原 tdxPj.py 的硬编码条件）"""
        self.strategy = StrategyConfig(
            name="default",
            description="高换手率+高量比+筹码集中+连续上涨",
            conditions=[
                FilterCondition("换手率", "turnover_rate", ">", 15),
                FilterCondition("量比", "volume_ratio", ">", 1.5),
                FilterCondition("筹码集中度", "chip_concentration", "<", 20),
                FilterCondition("连续上涨", "consecutive_up", "==", 1),
            ]
        )
        return self.strategy

    def save_strategy_to_file(self, filepath: str):
        """保存策略到文件"""
        if self.strategy is None:
            raise ValueError("没有可保存的策略")

        data = {
            'name': self.strategy.name,
            'description': self.strategy.description,
            'conditions': [asdict(c) for c in self.strategy.conditions],
            'max_stocks': self.strategy.max_stocks,
            'sort_by': self.strategy.sort_by,
            'sort_desc': self.strategy.sort_desc,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"策略已保存: {filepath}")

    def update_strategy_from_llm(self, nl_description: str, llm_client) -> StrategyConfig:
        """
        使用 LLM 从自然语言描述生成策略
        这是 AI 介入的核心入口点
        """
        prompt = f"""
        请根据以下股票筛选策略描述，生成结构化的筛选条件。
        描述: {nl_description}

        可用字段:
        - price: 当前价格
        - turnover_rate: 换手率 (%)
        - volume_ratio: 量比
        - chip_concentration: 筹码集中度 (%)
        - consecutive_up: 连续上涨天数
        - market_cap: 流通市值
        - pe_ratio: 市盈率
        - pb_ratio: 市净率

        请返回 JSON 格式:
        {{
          "name": "策略名称",
          "description": "策略描述",
          "conditions": [
            {{"name": "显示名", "field": "字段名", "operator": ">", "value": 15, "enabled": true}}
          ],
          "sort_by": "可选排序字段",
          "sort_desc": true
        }}

        只返回 JSON，不要其他解释。
        """

        try:
            response = llm_client.generate(prompt)
            data = json.loads(response)

            conditions = [
                FilterCondition(**c) for c in data.get('conditions', [])
            ]

            self.strategy = StrategyConfig(
                name=data.get('name', 'llm_generated'),
                description=data.get('description', nl_description),
                conditions=conditions,
                sort_by=data.get('sort_by'),
                sort_desc=data.get('sort_desc', True)
            )

            logger.info(f"LLM 生成策略: {self.strategy.name}")
            return self.strategy

        except Exception as e:
            logger.error(f"LLM 生成策略失败: {e}")
            return self._default_strategy()

    def get_condition_checker(self, condition: FilterCondition) -> Callable:
        """
        获取条件检查函数 - 解耦条件定义与执行
        """
        operators = {
            '>': lambda x, y: x > y,
            '<': lambda x, y: x < y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y,
            'between': lambda x, y, z: y <= x <= z if z is not None else False,
        }

        op_func = operators.get(condition.operator)
        if op_func is None:
            raise ValueError(f"不支持的操作符: {condition.operator}")

        def checker(stock_data: Dict) -> bool:
            value = stock_data.get(condition.field)
            if value is None:
                return False

            if condition.operator == 'between':
                return op_func(value, condition.value, condition.value2)
            return op_func(value, condition.value)

        return checker


# 全局配置实例
config = ConfigManager()
