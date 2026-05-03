"""
数据验证模块 - 使用 Pydantic 进行请求数据验证
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator


class FilterConditionSchema(BaseModel):
    """筛选条件验证"""
    name: str = Field(..., min_length=1, max_length=50, description="条件名称")
    field: str = Field(..., min_length=1, max_length=50, description="字段名")
    operator: Literal['>', '<', '>=', '<=', '==', 'between'] = Field(..., description="操作符")
    value: float = Field(..., description="比较值")
    value2: Optional[float] = Field(None, description="第二个值（用于 between）")
    enabled: bool = Field(True, description="是否启用")


class StrategyCreateSchema(BaseModel):
    """创建策略请求验证"""
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    description: str = Field('', max_length=500, description="策略描述")
    conditions: List[FilterConditionSchema] = Field(..., min_items=1, description="筛选条件")
    strategy_type: Literal['builtin', 'user', 'ai'] = Field('user', description="策略类型")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_desc: bool = Field(True, description="是否降序")
    max_stocks: Optional[int] = Field(None, ge=1, le=1000, description="最大股票数")


class StrategyUpdateSchema(BaseModel):
    """更新策略请求验证"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    conditions: Optional[List[FilterConditionSchema]] = None
    sort_by: Optional[str] = None
    sort_desc: Optional[bool] = None
    max_stocks: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None


class StockCreateSchema(BaseModel):
    """创建股票请求验证"""
    code: str = Field(..., min_length=6, max_length=10, description="股票代码")
    name: str = Field(..., min_length=1, max_length=50, description="股票名称")
    exchange: Optional[Literal['SH', 'SZ', 'BJ']] = Field(None, description="交易所")
    industry: Optional[str] = Field(None, max_length=50, description="行业")

    @validator('code')
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError('股票代码必须是数字')
        return v


class StockBulkImportSchema(BaseModel):
    """批量导入股票请求验证"""
    stocks: List[StockCreateSchema] = Field(..., min_items=1, max_items=1000)


class HistoricalDataSchema(BaseModel):
    """历史数据验证"""
    date: str = Field(..., description="日期")
    open: Optional[float] = Field(None, ge=0, description="开盘价")
    high: Optional[float] = Field(None, ge=0, description="最高价")
    low: Optional[float] = Field(None, ge=0, description="最低价")
    close: float = Field(..., gt=0, description="收盘价")
    volume: Optional[int] = Field(None, ge=0, description="成交量")
    amount: Optional[float] = Field(None, ge=0, description="成交额")


class ConfigSchema(BaseModel):
    """配置验证"""
    key: str = Field(..., min_length=1, max_length=100, description="配置键")
    value: str = Field(..., description="配置值")
    description: Optional[str] = Field(None, max_length=500)


class AIStrategyGenerateSchema(BaseModel):
    """AI生成策略请求验证"""
    description: str = Field(..., min_length=10, max_length=1000, description="策略描述")
    ai_provider: Literal['anthropic', 'openai', 'mock'] = Field('anthropic', description="AI提供商")
    api_key: Optional[str] = Field(None, description="API密钥")
    model: Optional[str] = Field(None, description="模型名称")


class ScreeningExecuteSchema(BaseModel):
    """执行筛选请求验证"""
    strategy_id: int = Field(..., ge=1, description="策略ID")
    max_stocks: Optional[int] = Field(None, ge=1, le=1000)
    use_ai_analysis: bool = Field(False, description="是否使用AI分析")


class AIRatingSchema(BaseModel):
    """AI建议评分验证"""
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")


class PaginationParams(BaseModel):
    """分页参数验证"""
    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(20, ge=1, le=100, description="每页数量")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit
