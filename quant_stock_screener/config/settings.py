"""
配置管理模块

集中管理所有配置项，支持环境变量和配置文件
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


@dataclass
class FilterCondition:
    """筛选条件配置"""

    name: str  # 条件显示名称
    field: str  # 数据字段名
    operator: str  # 操作符: >, <, >=, <=, ==, between
    value: float  # 比较值
    value2: Optional[float] = None  # between 操作符的第二个值
    enabled: bool = True  # 是否启用


@dataclass
class StrategyConfig:
    """策略配置"""

    name: str
    description: str
    conditions: List[FilterCondition] = field(default_factory=list)
    max_stocks: Optional[int] = None
    sort_by: Optional[str] = None
    sort_desc: bool = True


@dataclass
class AIConfig:
    """AI/LLM 配置"""

    enabled: bool = False
    provider: str = "anthropic"  # anthropic, openai, mock
    api_key: Optional[str] = None
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 2000
    temperature: float = 0.7


@dataclass
class DatabaseConfig:
    """数据库配置"""

    url: str = "sqlite:///data/quant_screener.db"
    echo: bool = False
    pool_size: int = 5


@dataclass
class ServerConfig:
    """服务器配置"""

    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    secret_key: str = "change-me-in-production"


class Settings:
    """
    全局配置管理器

    使用方式:
        settings = Settings()
        settings.ai.api_key = "your-key"
    """

    def __init__(self):
        self.ai = AIConfig()
        self.database = DatabaseConfig()
        self.server = ServerConfig()

        # 股票列表文件路径
        self.stock_list_file: str = "stock_list.txt"

        # 输出配置
        self.output_format: str = "table"  # table, json, csv
        self.log_level: str = "INFO"

        # 自动加载环境变量
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # AI 配置
        if api_key := os.getenv("ANTHROPIC_API_KEY"):
            self.ai.api_key = api_key
            self.ai.enabled = True
            self.ai.provider = "anthropic"
        elif api_key := os.getenv("OPENAI_API_KEY"):
            self.ai.api_key = api_key
            self.ai.enabled = True
            self.ai.provider = "openai"

        if model := os.getenv("AI_MODEL"):
            self.ai.model = model

        # 数据库配置
        if db_url := os.getenv("DATABASE_URL"):
            self.database.url = db_url

        # 服务器配置
        if secret := os.getenv("SECRET_KEY"):
            self.server.secret_key = secret

        if debug := os.getenv("FLASK_DEBUG"):
            self.server.debug = debug.lower() == "true"

        if port := os.getenv("PORT"):
            self.server.port = int(port)

    @property
    def is_ai_available(self) -> bool:
        """检查 AI 功能是否可用"""
        return self.ai.enabled and self.ai.api_key is not None

    def get_condition_checker(self, condition: FilterCondition) -> Callable:
        """
        获取条件检查函数

        Args:
            condition: 筛选条件配置

        Returns:
            条件检查函数
        """
        operators = {
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
            "==": lambda x, y: x == y,
            "between": lambda x, y, z: y <= x <= z if z is not None else False,
        }

        op_func = operators.get(condition.operator)
        if op_func is None:
            raise ValueError(f"不支持的操作符: {condition.operator}")

        def checker(stock_data: Dict) -> bool:
            value = stock_data.get(condition.field)
            if value is None:
                return False

            if condition.operator == "between":
                return op_func(value, condition.value, condition.value2)
            return op_func(value, condition.value)

        return checker


# 全局配置实例
settings = Settings()
