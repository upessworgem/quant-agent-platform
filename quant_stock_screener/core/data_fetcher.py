"""
数据获取模块

封装股票数据获取逻辑，支持多种数据源
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class StockQuote:
    """股票实时行情"""

    code: str
    name: str
    price: float
    open_price: float
    high_price: float
    low_price: float
    prev_close: float
    volume: int  # 成交量（手）
    amount: float  # 成交额


@dataclass
class StockFinance:
    """股票财务数据"""

    code: str
    circulating_shares: float  # 流通股本
    total_assets: Optional[float] = None
    net_assets: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None


@dataclass
class KLineData:
    """K 线数据"""

    code: str
    dates: List
    opens: List[float]
    highs: List[float]
    lows: List[float]
    closes: List[float]
    volumes: List[int]


class DataFetcher:
    """
    数据获取器

    封装通达信数据接口，提供统一的数据访问层
    """

    def __init__(self, market: str = "std"):
        """
        初始化数据获取器

        Args:
            market: 市场类型，std=标准
        """
        self.market = market
        self._client = None
        self._connect()

    def _connect(self):
        """建立数据源连接"""
        try:
            from mootdx.quotes import Quotes

            self._client = Quotes.factory(market=self.market)
            logger.info(f"已连接到数据源: {self.market}")
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

    def get_quote(self, stock_code: str) -> Optional[StockQuote]:
        """
        获取股票实时行情

        Args:
            stock_code: 股票代码

        Returns:
            股票行情数据，失败返回 None
        """
        try:
            data = self._client.quotes(symbol=stock_code)
            if data is None or data.empty:
                return None

            row = data.iloc[0]
            return StockQuote(
                code=stock_code,
                name=str(row.get("name", "")),
                price=float(row.get("price", 0)),
                open_price=float(row.get("open", 0)),
                high_price=float(row.get("high", 0)),
                low_price=float(row.get("low", 0)),
                prev_close=float(row.get("last_close", 0)),
                volume=int(row.get("vol", 0)),
                amount=float(row.get("amount", 0)),
            )
        except Exception as e:
            logger.warning(f"获取 {stock_code} 行情失败: {e}")
            return None

    def get_finance(self, stock_code: str) -> Optional[StockFinance]:
        """
        获取股票财务数据

        Args:
            stock_code: 股票代码

        Returns:
            财务数据，失败返回 None
        """
        try:
            data = self._client.finance(symbol=stock_code)
            if data is None or data.empty:
                return None

            row = data.iloc[0]
            return StockFinance(
                code=stock_code,
                circulating_shares=float(row.get("liutongguben", 0)),
                total_assets=row.get("total_assets"),
                net_assets=row.get("net_assets"),
                pe_ratio=row.get("pe_ratio"),
                pb_ratio=row.get("pb_ratio"),
            )
        except Exception as e:
            logger.warning(f"获取 {stock_code} 财务数据失败: {e}")
            return None

    def get_kline(
        self, stock_code: str, frequency: int = 9, count: int = 10
    ) -> Optional[KLineData]:
        """
        获取 K 线数据

        Args:
            stock_code: 股票代码
            frequency: K 线周期，9=日线
            count: 获取数量

        Returns:
            K 线数据，失败返回 None
        """
        try:
            data = self._client.bars(
                symbol=stock_code, frequency=frequency, offset=count
            )
            if data is None or len(data) < 3:
                return None

            return KLineData(
                code=stock_code,
                dates=data.index.tolist(),
                opens=data["open"].tolist(),
                highs=data["high"].tolist(),
                lows=data["low"].tolist(),
                closes=data["close"].tolist(),
                volumes=data["vol"].tolist(),
            )
        except Exception as e:
            logger.warning(f"获取 {stock_code} K线数据失败: {e}")
            return None


class StockDataProcessor:
    """
    股票数据处理器

    纯计算逻辑，无外部依赖，易于测试
    """

    @staticmethod
    def calculate_turnover_rate(volume: int, circulating_shares: float) -> float:
        """
        计算换手率

        Args:
            volume: 成交量（手）
            circulating_shares: 流通股本（股）

        Returns:
            换手率（%）
        """
        if circulating_shares <= 0:
            return 0.0
        # volume 是手，circulating_shares 是股，需要统一单位
        return (volume * 100 / circulating_shares) * 100

    @staticmethod
    def calculate_volume_ratio(
        current_volume: int, previous_volumes: List[int]
    ) -> float:
        """
        计算量比

        Args:
            current_volume: 当日成交量
            previous_volumes: 前几日成交量列表

        Returns:
            量比
        """
        if not previous_volumes or len(previous_volumes) == 0:
            return 0.0

        avg_volume = np.mean(previous_volumes)
        if avg_volume <= 0:
            return 0.0

        return current_volume / avg_volume

    @staticmethod
    def check_consecutive_up(closes: List[float], days: int = 2) -> bool:
        """
        检查是否连续上涨

        Args:
            closes: 收盘价列表
            days: 连续上涨天数

        Returns:
            是否连续上涨
        """
        if len(closes) < days + 1:
            return False

        recent_closes = closes[-(days + 1) :]
        for i in range(1, len(recent_closes)):
            if recent_closes[i] <= recent_closes[i - 1]:
                return False

        return True

    @staticmethod
    def calculate_chip_concentration(
        prices: List[float], volumes: List[float]
    ) -> float:
        """
        计算筹码集中度

        使用成交量加权的 5%-95% 分位差与 VWAP 的比值

        Args:
            prices: 价格列表
            volumes: 成交量列表

        Returns:
            筹码集中度（%），越低表示筹码越集中
        """
        if len(prices) == 0 or len(volumes) == 0 or sum(volumes) == 0:
            return float("inf")

        prices = np.array(prices)
        volumes = np.array(volumes)

        # 计算 VWAP（成交量加权平均价）
        vwap = np.average(prices, weights=volumes)
        if vwap <= 0:
            return float("inf")

        # 按价格排序
        sorted_indices = np.argsort(prices)
        sorted_prices = prices[sorted_indices]
        sorted_volumes = volumes[sorted_indices]

        # 计算累积成交量分布
        cumulative_volume = np.cumsum(sorted_volumes)
        total_volume = cumulative_volume[-1]

        # 找到 5% 和 95% 分位对应的价格
        low_index = np.searchsorted(cumulative_volume, total_volume * 0.05)
        high_index = np.searchsorted(cumulative_volume, total_volume * 0.95)

        cost_low = sorted_prices[max(0, low_index)]
        cost_high = sorted_prices[min(len(sorted_prices) - 1, high_index)]

        # 筹码集中度 = (高价 - 低价) / VWAP * 100
        concentration = ((cost_high - cost_low) / vwap) * 100
        return concentration

    @staticmethod
    def enrich_stock_data(
        stock_code: str,
        stock_name: str,
        quote: StockQuote,
        finance: StockFinance,
        kline: KLineData,
    ) -> Dict:
        """
        整合数据并计算所有技术指标

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            quote: 实时行情
            finance: 财务数据
            kline: K 线数据

        Returns:
            包含所有指标的数据字典
        """
        # 基础数据
        data = {
            "code": stock_code,
            "name": stock_name,
            "price": quote.price,
            "open": quote.open_price,
            "high": quote.high_price,
            "low": quote.low_price,
            "volume": quote.volume,
            "amount": quote.amount,
            "circulating_shares": finance.circulating_shares if finance else 0,
        }

        # 计算换手率
        if finance and finance.circulating_shares > 0:
            data["turnover_rate"] = StockDataProcessor.calculate_turnover_rate(
                quote.volume, finance.circulating_shares
            )
        else:
            data["turnover_rate"] = 0.0

        # 计算量比和连续上涨
        if kline and len(kline.volumes) >= 5:
            # 量比：今日成交量 / 前5日平均成交量
            prev_volumes = (
                kline.volumes[-6:-1]
                if len(kline.volumes) >= 6
                else kline.volumes[:-1]
            )
            data["volume_ratio"] = StockDataProcessor.calculate_volume_ratio(
                quote.volume, prev_volumes
            )

            # 连续上涨判断
            data["consecutive_up"] = (
                1 if StockDataProcessor.check_consecutive_up(kline.closes, days=2) else 0
            )

            # 筹码集中度
            data["chip_concentration"] = StockDataProcessor.calculate_chip_concentration(
                kline.closes, kline.volumes
            )
        else:
            data["volume_ratio"] = 0.0
            data["consecutive_up"] = 0
            data["chip_concentration"] = float("inf")

        # 添加财务指标
        if finance:
            data["pe_ratio"] = finance.pe_ratio
            data["pb_ratio"] = finance.pb_ratio
        else:
            data["pe_ratio"] = None
            data["pb_ratio"] = None

        return data


class StockListLoader:
    """股票列表加载器"""

    @staticmethod
    def load_from_txt(filepath: str = "stock_list.txt") -> List[Dict]:
        """
        从文本文件加载股票列表

        Args:
            filepath: 文件路径，每行格式为 "股票名称----股票代码"

        Returns:
            股票列表
        """
        stocks = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "----" in line:
                        parts = line.split("----")
                        if len(parts) >= 2:
                            stocks.append(
                                {"name": parts[0].strip(), "code": parts[1].strip()}
                            )
            logger.info(f"从 {filepath} 加载了 {len(stocks)} 只股票")
        except FileNotFoundError:
            logger.error(f"找不到股票列表文件: {filepath}")
        except Exception as e:
            logger.error(f"加载股票列表失败: {e}")

        return stocks
