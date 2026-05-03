"""
Pydantic 数据验证 Schema
"""

from typing import List, Optional, Literal

from pydantic import BaseModel, Field, validator


class FilterConditionSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    field: str = Field(..., min_length=1, max_length=50)
    operator: Literal[">", "<", ">=", "<=", "==", "between"]
    value: float
    value2: Optional[float] = None
    enabled: bool = True


class StrategyCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    conditions: List[FilterConditionSchema] = Field(..., min_items=1)
    strategy_type: Literal["builtin", "user", "ai"] = "user"
    sort_by: Optional[str] = None
    sort_desc: bool = True
    max_stocks: Optional[int] = Field(None, ge=1, le=1000)


class StrategyUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    conditions: Optional[List[FilterConditionSchema]] = None
    sort_by: Optional[str] = None
    sort_desc: Optional[bool] = None
    max_stocks: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None


class StockCreateSchema(BaseModel):
    code: str = Field(..., min_length=6, max_length=10)
    name: str = Field(..., min_length=1, max_length=50)
    exchange: Optional[Literal["SH", "SZ", "BJ"]] = None
    industry: Optional[str] = Field(None, max_length=50)

    @validator("code")
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError("Stock code must be numeric")
        return v


class StockBulkImportSchema(BaseModel):
    stocks: List[StockCreateSchema] = Field(..., min_items=1, max_items=1000)


class HistoricalDataSchema(BaseModel):
    date: str
    open: Optional[float] = Field(None, ge=0)
    high: Optional[float] = Field(None, ge=0)
    low: Optional[float] = Field(None, ge=0)
    close: float = Field(..., gt=0)
    volume: Optional[int] = Field(None, ge=0)
    amount: Optional[float] = Field(None, ge=0)


class ConfigSchema(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: str
    description: Optional[str] = Field(None, max_length=500)


class AIStrategyGenerateSchema(BaseModel):
    description: str = Field(..., min_length=10, max_length=1000)
    ai_provider: Literal["anthropic", "openai", "mock"] = "anthropic"
    api_key: Optional[str] = None
    model: Optional[str] = None


class ScreeningExecuteSchema(BaseModel):
    strategy_id: int = Field(..., ge=1)
    max_stocks: Optional[int] = Field(None, ge=1, le=1000)
    use_ai_analysis: bool = False


class AIRatingSchema(BaseModel):
    rating: int = Field(..., ge=1, le=5)


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit
