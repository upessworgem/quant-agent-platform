"""
数据获取模块 - 解耦数据获取与业务逻辑
封装 mootdx 接口，提供统一的数据访问层
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StockQuote:
    """股票实时行情数据"""
    code: str
    name: str
    price: float
    open: float
    high: float
    low: float
    prev_close: float
    volume: int  # 成交量（手）
    amount: float  # 成交额


@dataclass
class StockFinance:
    """股票财务数据"""
    code: str
    liutongguben: float  # 流通股本
    total_assets: Optional[float] = None
    net_assets: Optional[float] = None


@dataclass
class KLineData:
    """K线数据"""
    code: str
    dates: List
    opens: List[float]
    highs: List[float]
    lows: List[float]
    closes: List[float]
    volumes: List[int]  # 成交量（手）


class DataFetcher:
    """
    数据获取器 - 封装所有数据源访问
    解耦具体的数据源实现（mootdx）与业务逻辑
    """

    def __init__(self, market: str = 'std'):
        self.market = market
        self._client = None
        self._reader = None
        self._connect()

    def _connect(self):
        """建立连接"""
        try:
            from mootdx.quotes import Quotes
            from mootdx.reader import Reader
            self._client = Quotes.factory(market=self.market)
            self._reader = Reader.factory(market=self.market)
            logger.info(f"已连接到市场: {self.market}")
        except Exception as e:
            logger.error(f"连接数据源失败: {e}")
            raise

    def close(self):
        """关闭连接"""
        if self._client:
            try:
                self._client.close()
                logger.info("数据源连接已关闭")
            except Exception as e:
                logger.warning(f"关闭连接时出错: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ========== 基础数据获取 ==========

    def get_quote(self, code: str) -> Optional[StockQuote]:
        """获取实时行情"""
        try:
            data = self._client.quotes(symbol=code)
            if data is None or data.empty:
                return None

            row = data.iloc[0]
            return StockQuote(
                code=code,
                name=row.get('name', ''),
                price=float(row.get('price', 0)),
                open=float(row.get('open', 0)),
                high=float(row.get('high', 0)),
                low=float(row.get('low', 0)),
                prev_close=float(row.get('last_close', 0)),
                volume=int(row.get('vol', 0)),
                amount=float(row.get('amount', 0))
            )
        except Exception as e:
            logger.warning(f"获取 {code} 行情失败: {e}")
            return None

    def get_finance(self, code: str) -> Optional[StockFinance]:
        """获取财务数据"""
        try:
            data = self._client.finance(symbol=code)
            if data is None or data.empty:
                return None

            row = data.iloc[0]
            return StockFinance(
                code=code,
                liutongguben=float(row.get('liutongguben', 0)),
                total_assets=row.get('total_assets'),
                net_assets=row.get('net_assets')
            )
        except Exception as e:
            logger.warning(f"获取 {code} 财务数据失败: {e}")
            return None

    def get_kline(self, code: str, frequency: int = 9, offset: int = 10) -> Optional[KLineData]:
        """
        获取K线数据
        frequency: 9=日线, 5=5分钟线等
        offset: 获取多少条数据
        """
        try:
            data = self._client.bars(symbol=code, frequency=frequency, offset=offset)
            if data is None or len(data) < 3:
                return None

            return KLineData(
                code=code,
                dates=data.index.tolist(),
                opens=data['open'].tolist(),
                highs=data['high'].tolist(),
                lows=data['low'].tolist(),
                closes=data['close'].tolist(),
                volumes=data['vol'].tolist()
            )
        except Exception as e:
            logger.warning(f"获取 {code} K线数据失败: {e}")
            return None

    # ========== 批量数据获取 ==========

    def get_quotes_batch(self, codes: List[str]) -> Dict[str, StockQuote]:
        """批量获取行情"""
        results = {}
        for code in codes:
            quote = self.get_quote(code)
            if quote:
                results[code] = quote
        return results

    def get_finance_batch(self, codes: List[str]) -> Dict[str, StockFinance]:
        """批量获取财务数据"""
        results = {}
        for code in codes:
            finance = self.get_finance(code)
            if finance:
                results[code] = finance
        return results


class StockDataProcessor:
    """
    股票数据处理器 - 计算技术指标
    纯计算逻辑，无外部依赖，易于测试
    """

    @staticmethod
    def calculate_turnover_rate(volume: int, liutongguben: float) -> float:
        """计算换手率 (%)"""
        if liutongguben <= 0:
            return 0
        # volume 是手，liutongguben 是股，需要统一单位
        return volume * 100 / liutongguben * 100

    @staticmethod
    def calculate_volume_ratio(today_vol: int, prev_volumes: List[int]) -> float:
        """计算量比"""
        if not prev_volumes or len(prev_volumes) == 0:
            return 0
        avg_vol = np.mean(prev_volumes)
        if avg_vol <= 0:
            return 0
        return today_vol / avg_vol

    @staticmethod
    def check_consecutive_up(closes: List[float], days: int = 2) -> bool:
        """检查是否连续上涨指定天数"""
        if len(closes) < days + 1:
            return False
        recent = closes[-(days + 1):]
        for i in range(1, len(recent)):
            if recent[i] <= recent[i - 1]:
                return False
        return True

    @staticmethod
    def calculate_chip_concentration(prices: List[float], volumes: List[float]) -> float:
        """
        计算筹码集中度 (%)
        使用成交量加分的 5%-95% 分位差与 VWAP 的比值
        """
        if len(prices) == 0 or len(volumes) == 0 or sum(volumes) == 0:
            return float('inf')

        prices = np.array(prices)
        volumes = np.array(volumes)

        # 计算 VWAP
        vwap = np.average(prices, weights=volumes)
        if vwap <= 0:
            return float('inf')

        # 按价格排序
        sorted_indices = np.argsort(prices)
        sorted_prices = prices[sorted_indices]
        sorted_volumes = volumes[sorted_indices]

        # 累积成交量
        cumvol = np.cumsum(sorted_volumes)
        total_vol = cumvol[-1]

        # 5% 和 95% 分位
        low_idx = np.searchsorted(cumvol, total_vol * 0.05)
        high_idx = np.searchsorted(cumvol, total_vol * 0.95)

        cost_low = sorted_prices[max(0, low_idx)]
        cost_high = sorted_prices[min(len(sorted_prices) - 1, high_idx)]

        concentration = (cost_high - cost_low) / vwap * 100
        return concentration

    @staticmethod
    def enrich_stock_data(
        code: str,
        name: str,
        quote: StockQuote,
        finance: StockFinance,
        kline: KLineData
    ) -> Dict:
        """
        整合数据并计算所有指标
        返回 enriched data dict
        """
        # 基础数据
        data = {
            'code': code,
            'name': name,
            'price': quote.price,
            'open': quote.open,
            'high': quote.high,
            'low': quote.low,
            'volume': quote.volume,
            'amount': quote.amount,
            'liutongguben': finance.liutongguben if finance else 0,
        }

        # 计算指标
        if finance and finance.liutongguben > 0:
            data['turnover_rate'] = StockDataProcessor.calculate_turnover_rate(
                quote.volume, finance.liutongguben
            )
        else:
            data['turnover_rate'] = 0

        if kline and len(kline.volumes) >= 5:
            # 量比：今日 vs 前5日平均
            prev_volumes = kline.volumes[-6:-1] if len(kline.volumes) >= 6 else kline.volumes[:-1]
            data['volume_ratio'] = StockDataProcessor.calculate_volume_ratio(
                quote.volume, prev_volumes
            )

            # 连续上涨
            data['consecutive_up'] = 1 if StockDataProcessor.check_consecutive_up(
                kline.closes, days=2
            ) else 0

            # 筹码集中度
            data['chip_concentration'] = StockDataProcessor.calculate_chip_concentration(
                kline.closes, kline.volumes
            )
        else:
            data['volume_ratio'] = 0
            data['consecutive_up'] = 0
            data['chip_concentration'] = float('inf')

        return data


class StockListLoader:
    """股票列表加载器"""

    @staticmethod
    def load_from_txt(filepath: str = "stock_list.txt") -> List[Dict]:
        """从文本文件加载股票列表"""
        stocks = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '----' in line:
                        parts = line.split('----')
                        if len(parts) >= 2:
                            stocks.append({
                                'name': parts[0].strip(),
                                'code': parts[1].strip()
                            })
            logger.info(f"从 {filepath} 加载了 {len(stocks)} 只股票")
        except FileNotFoundError:
            logger.error(f"找不到股票列表文件: {filepath}")
        except Exception as e:
            logger.error(f"加载股票列表失败: {e}")
        return stocks

    @staticmethod
    def load_from_csv(filepath: str) -> List[Dict]:
        """从 CSV 加载股票列表"""
        stocks = []
        try:
            import csv
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stocks.append({
                        'name': row.get('name', ''),
                        'code': row.get('code', '')
                    })
            logger.info(f"从 {filepath} 加载了 {len(stocks)} 只股票")
        except Exception as e:
            logger.error(f"加载 CSV 失败: {e}")
        return stocks
