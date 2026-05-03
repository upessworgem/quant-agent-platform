"""
数据模型模块 - 定义所有数据库表结构
使用 SQLAlchemy ORM
"""

from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, asdict
import json

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    Boolean, Text, ForeignKey, Table, Index
)
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.sql import func

Base = declarative_base()


# 关联表：筛选结果与股票的中间表
screening_result_stocks = Table(
    'screening_result_stocks',
    Base.metadata,
    Column('result_id', Integer, ForeignKey('screening_results.id'), primary_key=True),
    Column('stock_id', Integer, ForeignKey('stocks.id'), primary_key=True)
)


class Stock(Base):
    """股票基础信息表"""
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True, unique=True)
    name = Column(String(50), nullable=False)
    exchange = Column(String(10), nullable=True)  # SH, SZ, BJ
    industry = Column(String(50), nullable=True)  # 行业
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    historical_data = relationship("StockHistoricalData", back_populates="stock", cascade="all, delete-orphan")
    screening_items = relationship("ScreeningItem", back_populates="stock", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'exchange': self.exchange,
            'industry': self.industry,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class StockHistoricalData(Base):
    """股票历史数据表 - 用于缓存和回测"""
    __tablename__ = 'stock_historical_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)

    # 基础行情
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer)  # 成交量（手）
    amount = Column(Float)    # 成交额

    # 计算指标（可选缓存）
    turnover_rate = Column(Float)       # 换手率
    volume_ratio = Column(Float)        # 量比
    chip_concentration = Column(Float)  # 筹码集中度

    # 财务数据
    liutongguben = Column(Float)  # 流通股本
    pe_ratio = Column(Float)      # 市盈率
    pb_ratio = Column(Float)      # 市净率

    created_at = Column(DateTime, default=func.now())

    # 关联
    stock = relationship("Stock", back_populates="historical_data")

    # 索引
    __table_args__ = (
        Index('idx_stock_date', 'stock_id', 'date', unique=True),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'stock_id': self.stock_id,
            'code': self.stock.code if self.stock else None,
            'name': self.stock.name if self.stock else None,
            'date': self.date.isoformat() if self.date else None,
            'open': self.open_price,
            'high': self.high_price,
            'low': self.low_price,
            'close': self.close_price,
            'volume': self.volume,
            'amount': self.amount,
            'turnover_rate': self.turnover_rate,
            'volume_ratio': self.volume_ratio,
            'chip_concentration': self.chip_concentration,
            'liutongguben': self.liutongguben,
            'pe_ratio': self.pe_ratio,
            'pb_ratio': self.pb_ratio,
        }


class Strategy(Base):
    """策略配置表"""
    __tablename__ = 'strategies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # 策略类型: builtin(内置), user(用户创建), ai(LLM生成)
    strategy_type = Column(String(20), default='user')

    # 策略条件（JSON 存储）
    conditions_json = Column(Text, nullable=False)

    # 排序配置
    sort_by = Column(String(50), nullable=True)
    sort_desc = Column(Boolean, default=True)
    max_stocks = Column(Integer, nullable=True)

    # 元数据
    is_active = Column(Boolean, default=True)
    created_by = Column(String(50), default='system')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    screening_results = relationship("ScreeningResult", back_populates="strategy")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'strategy_type': self.strategy_type,
            'conditions': json.loads(self.conditions_json) if self.conditions_json else [],
            'sort_by': self.sort_by,
            'sort_desc': self.sort_desc,
            'max_stocks': self.max_stocks,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ScreeningResult(Base):
    """筛选执行结果表"""
    __tablename__ = 'screening_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False)

    # 执行信息
    executed_at = Column(DateTime, default=func.now())
    total_stocks = Column(Integer, default=0)      # 处理的总股票数
    matched_count = Column(Integer, default=0)     # 匹配的数量
    execution_time_ms = Column(Integer)            # 执行耗时（毫秒）

    # 执行状态
    status = Column(String(20), default='success') # success, partial, failed
    error_message = Column(Text, nullable=True)

    # AI 分析结果（可选）
    ai_analysis = Column(Text, nullable=True)

    # 关联
    strategy = relationship("Strategy", back_populates="screening_results")
    items = relationship("ScreeningItem", back_populates="result", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy.name if self.strategy else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'total_stocks': self.total_stocks,
            'matched_count': self.matched_count,
            'execution_time_ms': self.execution_time_ms,
            'status': self.status,
            'error_message': self.error_message,
            'ai_analysis': self.ai_analysis,
        }


class ScreeningItem(Base):
    """筛选结果明细表 - 每只股票的具体数据"""
    __tablename__ = 'screening_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(Integer, ForeignKey('screening_results.id'), nullable=False)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)

    # 排名
    rank = Column(Integer, default=0)

    # 当时的指标值
    price = Column(Float)
    turnover_rate = Column(Float)
    volume_ratio = Column(Float)
    chip_concentration = Column(Float)
    consecutive_up = Column(Boolean)

    # 原始数据快照（JSON）
    snapshot_json = Column(Text)

    # 关联
    result = relationship("ScreeningResult", back_populates="items")
    stock = relationship("Stock")

    def to_dict(self):
        return {
            'id': self.id,
            'result_id': self.result_id,
            'stock_id': self.stock_id,
            'code': self.stock.code if self.stock else None,
            'name': self.stock.name if self.stock else None,
            'rank': self.rank,
            'price': self.price,
            'turnover_rate': self.turnover_rate,
            'volume_ratio': self.volume_ratio,
            'chip_concentration': self.chip_concentration,
            'consecutive_up': self.consecutive_up,
            'snapshot': json.loads(self.snapshot_json) if self.snapshot_json else None,
        }


class AISuggestion(Base):
    """AI 建议记录表"""
    __tablename__ = 'ai_suggestions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    suggestion_type = Column(String(50), nullable=False)  # strategy, analysis, improvement

    # 关联
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=True)
    result_id = Column(Integer, ForeignKey('screening_results.id'), nullable=True)

    # 输入输出
    input_data = Column(Text)
    output_data = Column(Text)

    # AI 配置
    ai_provider = Column(String(20))
    ai_model = Column(String(50))

    # 用户反馈
    user_rating = Column(Integer, nullable=True)  # 1-5 评分
    is_applied = Column(Boolean, default=False)   # 用户是否采纳

    created_at = Column(DateTime, default=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'suggestion_type': self.suggestion_type,
            'strategy_id': self.strategy_id,
            'result_id': self.result_id,
            'input': self.input_data,
            'output': self.output_data,
            'ai_provider': self.ai_provider,
            'ai_model': self.ai_model,
            'user_rating': self.user_rating,
            'is_applied': self.is_applied,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = 'system_config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
