"""
数据库操作模块 - 封装所有数据库访问
提供 CRUD 操作和查询方法
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

from sqlalchemy import create_engine, desc, asc, func
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy.exc import IntegrityError, NoResultFound

from models import (
    Base, Stock, StockHistoricalData, Strategy, ScreeningResult,
    ScreeningItem, AISuggestion, SystemConfig
)

logger = logging.getLogger(__name__)


class Database:
    """数据库管理类"""

    def __init__(self, db_url: str = "sqlite:///tdx_data.db"):
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        Base.metadata.create_all(self.engine)
        logger.info("数据库表已初始化")

    @contextmanager
    def session(self):
        """提供数据库会话上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ========== 股票基础信息操作 ==========

    def create_stock(self, code: str, name: str, exchange: str = None, industry: str = None) -> Stock:
        """创建股票记录"""
        with self.session() as session:
            stock = Stock(
                code=code,
                name=name,
                exchange=exchange,
                industry=industry
            )
            session.add(stock)
            session.flush()
            session.refresh(stock)
            logger.info(f"创建股票: {code} {name}")
            return stock

    def get_stock_by_code(self, code: str) -> Optional[Stock]:
        """根据代码获取股票"""
        with self.session() as session:
            return session.query(Stock).filter(Stock.code == code).first()

    def get_stock_by_id(self, stock_id: int) -> Optional[Stock]:
        """根据ID获取股票"""
        with self.session() as session:
            return session.query(Stock).filter(Stock.id == stock_id).first()

    def get_all_stocks(self, limit: int = None, offset: int = 0) -> List[Stock]:
        """获取所有股票"""
        with self.session() as session:
            query = session.query(Stock).order_by(Stock.code)
            if limit:
                query = query.limit(limit).offset(offset)
            return query.all()

    def update_stock(self, code: str, **kwargs) -> Optional[Stock]:
        """更新股票信息"""
        with self.session() as session:
            stock = session.query(Stock).filter(Stock.code == code).first()
            if stock:
                for key, value in kwargs.items():
                    if hasattr(stock, key):
                        setattr(stock, key, value)
                stock.updated_at = datetime.now()
                session.flush()
                session.refresh(stock)
                logger.info(f"更新股票: {code}")
            return stock

    def delete_stock(self, code: str) -> bool:
        """删除股票"""
        with self.session() as session:
            stock = session.query(Stock).filter(Stock.code == code).first()
            if stock:
                session.delete(stock)
                logger.info(f"删除股票: {code}")
                return True
            return False

    def bulk_import_stocks(self, stocks_data: List[Dict]) -> int:
        """批量导入股票"""
        count = 0
        with self.session() as session:
            for data in stocks_data:
                try:
                    stock = Stock(
                        code=data['code'],
                        name=data['name'],
                        exchange=data.get('exchange'),
                        industry=data.get('industry')
                    )
                    session.add(stock)
                    session.flush()
                    count += 1
                except IntegrityError:
                    session.rollback()
                    continue
            logger.info(f"批量导入 {count} 只股票")
            return count

    # ========== 历史数据操作 ==========

    def save_historical_data(self, stock_code: str, data: Dict) -> StockHistoricalData:
        """保存历史数据"""
        with self.session() as session:
            stock = session.query(Stock).filter(Stock.code == stock_code).first()
            if not stock:
                raise ValueError(f"股票不存在: {stock_code}")

            historical = StockHistoricalData(
                stock_id=stock.id,
                date=data.get('date', datetime.now()),
                open_price=data.get('open'),
                high_price=data.get('high'),
                low_price=data.get('low'),
                close_price=data.get('close'),
                volume=data.get('volume'),
                amount=data.get('amount'),
                turnover_rate=data.get('turnover_rate'),
                volume_ratio=data.get('volume_ratio'),
                chip_concentration=data.get('chip_concentration'),
                liutongguben=data.get('liutongguben'),
                pe_ratio=data.get('pe_ratio'),
                pb_ratio=data.get('pb_ratio'),
            )
            session.add(historical)
            session.flush()
            session.refresh(historical)
            return historical

    def get_historical_data(
        self,
        stock_code: str,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = None
    ) -> List[StockHistoricalData]:
        """获取历史数据"""
        with self.session() as session:
            stock = session.query(Stock).filter(Stock.code == stock_code).first()
            if not stock:
                return []

            query = session.query(StockHistoricalData).filter(
                StockHistoricalData.stock_id == stock.id
            )

            if start_date:
                query = query.filter(StockHistoricalData.date >= start_date)
            if end_date:
                query = query.filter(StockHistoricalData.date <= end_date)

            query = query.order_by(desc(StockHistoricalData.date))

            if limit:
                query = query.limit(limit)

            return query.all()

    def get_latest_data(self, stock_code: str) -> Optional[StockHistoricalData]:
        """获取最新数据"""
        with self.session() as session:
            stock = session.query(Stock).filter(Stock.code == stock_code).first()
            if not stock:
                return None

            return session.query(StockHistoricalData).filter(
                StockHistoricalData.stock_id == stock.id
            ).order_by(desc(StockHistoricalData.date)).first()

    def bulk_save_historical_data(self, stock_code: str, data_list: List[Dict]) -> int:
        """批量保存历史数据"""
        count = 0
        with self.session() as session:
            stock = session.query(Stock).filter(Stock.code == stock_code).first()
            if not stock:
                raise ValueError(f"股票不存在: {stock_code}")

            for data in data_list:
                try:
                    historical = StockHistoricalData(
                        stock_id=stock.id,
                        date=data.get('date'),
                        open_price=data.get('open'),
                        high_price=data.get('high'),
                        low_price=data.get('low'),
                        close_price=data.get('close'),
                        volume=data.get('volume'),
                        amount=data.get('amount'),
                    )
                    session.add(historical)
                    count += 1
                except IntegrityError:
                    session.rollback()
                    continue

            logger.info(f"保存 {stock_code} 的 {count} 条历史数据")
            return count

    # ========== 策略操作 ==========

    def create_strategy(
        self,
        name: str,
        description: str,
        conditions: List[Dict],
        strategy_type: str = 'user',
        sort_by: str = None,
        sort_desc: bool = True,
        max_stocks: int = None
    ) -> Strategy:
        """创建策略"""
        with self.session() as session:
            strategy = Strategy(
                name=name,
                description=description,
                strategy_type=strategy_type,
                conditions_json=json.dumps(conditions, ensure_ascii=False),
                sort_by=sort_by,
                sort_desc=sort_desc,
                max_stocks=max_stocks,
                is_active=True
            )
            session.add(strategy)
            session.flush()
            session.refresh(strategy)
            logger.info(f"创建策略: {name}")
            return strategy

    def get_strategy(self, strategy_id: int) -> Optional[Strategy]:
        """获取策略"""
        with self.session() as session:
            return session.query(Strategy).filter(Strategy.id == strategy_id).first()

    def get_all_strategies(self, active_only: bool = True) -> List[Strategy]:
        """获取所有策略"""
        with self.session() as session:
            query = session.query(Strategy)
            if active_only:
                query = query.filter(Strategy.is_active == True)
            return query.order_by(desc(Strategy.created_at)).all()

    def update_strategy(self, strategy_id: int, **kwargs) -> Optional[Strategy]:
        """更新策略"""
        with self.session() as session:
            strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
            if strategy:
                for key, value in kwargs.items():
                    if key == 'conditions':
                        strategy.conditions_json = json.dumps(value, ensure_ascii=False)
                    elif hasattr(strategy, key):
                        setattr(strategy, key, value)
                strategy.updated_at = datetime.now()
                session.flush()
                session.refresh(strategy)
                logger.info(f"更新策略: {strategy_id}")
            return strategy

    def delete_strategy(self, strategy_id: int) -> bool:
        """删除策略（软删除）"""
        return self.update_strategy(strategy_id, is_active=False) is not None

    def hard_delete_strategy(self, strategy_id: int) -> bool:
        """硬删除策略"""
        with self.session() as session:
            strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
            if strategy:
                session.delete(strategy)
                logger.info(f"硬删除策略: {strategy_id}")
                return True
            return False

    # ========== 筛选结果操作 ==========

    def create_screening_result(
        self,
        strategy_id: int,
        total_stocks: int = 0,
        matched_count: int = 0,
        execution_time_ms: int = None,
        status: str = 'success',
        error_message: str = None,
        ai_analysis: str = None
    ) -> ScreeningResult:
        """创建筛选结果记录"""
        with self.session() as session:
            result = ScreeningResult(
                strategy_id=strategy_id,
                total_stocks=total_stocks,
                matched_count=matched_count,
                execution_time_ms=execution_time_ms,
                status=status,
                error_message=error_message,
                ai_analysis=ai_analysis
            )
            session.add(result)
            session.flush()
            session.refresh(result)
            logger.info(f"创建筛选结果: {result.id}")
            return result

    def add_screening_item(
        self,
        result_id: int,
        stock_code: str,
        rank: int = 0,
        **indicators
    ) -> ScreeningItem:
        """添加筛选结果明细"""
        with self.session() as session:
            stock = session.query(Stock).filter(Stock.code == stock_code).first()
            if not stock:
                raise ValueError(f"股票不存在: {stock_code}")

            item = ScreeningItem(
                result_id=result_id,
                stock_id=stock.id,
                rank=rank,
                price=indicators.get('price'),
                turnover_rate=indicators.get('turnover_rate'),
                volume_ratio=indicators.get('volume_ratio'),
                chip_concentration=indicators.get('chip_concentration'),
                consecutive_up=indicators.get('consecutive_up'),
                snapshot_json=json.dumps(indicators, ensure_ascii=False)
            )
            session.add(item)
            session.flush()
            session.refresh(item)
            return item

    def get_screening_result(self, result_id: int) -> Optional[ScreeningResult]:
        """获取筛选结果"""
        with self.session() as session:
            return session.query(ScreeningResult).options(
                joinedload(ScreeningResult.items).joinedload(ScreeningItem.stock)
            ).filter(ScreeningResult.id == result_id).first()

    def get_screening_results(
        self,
        strategy_id: int = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 20
    ) -> List[ScreeningResult]:
        """获取筛选结果列表"""
        with self.session() as session:
            query = session.query(ScreeningResult)

            if strategy_id:
                query = query.filter(ScreeningResult.strategy_id == strategy_id)
            if start_date:
                query = query.filter(ScreeningResult.executed_at >= start_date)
            if end_date:
                query = query.filter(ScreeningResult.executed_at <= end_date)

            return query.order_by(desc(ScreeningResult.executed_at)).limit(limit).all()

    def delete_screening_result(self, result_id: int) -> bool:
        """删除筛选结果"""
        with self.session() as session:
            result = session.query(ScreeningResult).filter(ScreeningResult.id == result_id).first()
            if result:
                session.delete(result)
                logger.info(f"删除筛选结果: {result_id}")
                return True
            return False

    # ========== AI 建议操作 ==========

    def save_ai_suggestion(
        self,
        suggestion_type: str,
        input_data: str,
        output_data: str,
        ai_provider: str,
        ai_model: str,
        strategy_id: int = None,
        result_id: int = None
    ) -> AISuggestion:
        """保存 AI 建议"""
        with self.session() as session:
            suggestion = AISuggestion(
                suggestion_type=suggestion_type,
                input_data=input_data,
                output_data=output_data,
                ai_provider=ai_provider,
                ai_model=ai_model,
                strategy_id=strategy_id,
                result_id=result_id
            )
            session.add(suggestion)
            session.flush()
            session.refresh(suggestion)
            logger.info(f"保存 AI 建议: {suggestion.id}")
            return suggestion

    def get_ai_suggestions(
        self,
        suggestion_type: str = None,
        strategy_id: int = None,
        limit: int = 20
    ) -> List[AISuggestion]:
        """获取 AI 建议列表"""
        with self.session() as session:
            query = session.query(AISuggestion)

            if suggestion_type:
                query = query.filter(AISuggestion.suggestion_type == suggestion_type)
            if strategy_id:
                query = query.filter(AISuggestion.strategy_id == strategy_id)

            return query.order_by(desc(AISuggestion.created_at)).limit(limit).all()

    def rate_ai_suggestion(self, suggestion_id: int, rating: int) -> Optional[AISuggestion]:
        """给 AI 建议评分"""
        with self.session() as session:
            suggestion = session.query(AISuggestion).filter(AISuggestion.id == suggestion_id).first()
            if suggestion:
                suggestion.user_rating = rating
                session.flush()
                session.refresh(suggestion)
            return suggestion

    # ========== 系统配置操作 ==========

    def set_config(self, key: str, value: str, description: str = None) -> SystemConfig:
        """设置系统配置"""
        with self.session() as session:
            config = session.query(SystemConfig).filter(SystemConfig.key == key).first()
            if config:
                config.value = value
                if description:
                    config.description = description
            else:
                config = SystemConfig(key=key, value=value, description=description)
                session.add(config)

            session.flush()
            session.refresh(config)
            return config

    def get_config(self, key: str, default: str = None) -> Optional[str]:
        """获取系统配置"""
        with self.session() as session:
            config = session.query(SystemConfig).filter(SystemConfig.key == key).first()
            return config.value if config else default

    def get_all_configs(self) -> List[SystemConfig]:
        """获取所有配置"""
        with self.session() as session:
            return session.query(SystemConfig).all()

    def delete_config(self, key: str) -> bool:
        """删除配置"""
        with self.session() as session:
            config = session.query(SystemConfig).filter(SystemConfig.key == key).first()
            if config:
                session.delete(config)
                return True
            return False

    # ========== 统计查询 ==========

    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        with self.session() as session:
            return {
                'stocks_count': session.query(func.count(Stock.id)).scalar(),
                'strategies_count': session.query(func.count(Strategy.id)).filter(Strategy.is_active == True).scalar(),
                'screening_results_count': session.query(func.count(ScreeningResult.id)).scalar(),
                'historical_data_count': session.query(func.count(StockHistoricalData.id)).scalar(),
                'ai_suggestions_count': session.query(func.count(AISuggestion.id)).scalar(),
            }


# 全局数据库实例
db = Database()
