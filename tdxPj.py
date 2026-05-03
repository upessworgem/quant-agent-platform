import mootdx
import numpy as np
from mootdx.quotes import Quotes
from mootdx.reader import Reader
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print(f"MOOTDX版本: {mootdx.__version__}")

# 读取股票列表
def read_stock_list(filepath='stock_list.txt'):
    stocks = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '----' in line:
                    parts = line.split('----')
                    if len(parts) >= 2:
                        name, code = parts[0], parts[1]
                        stocks.append({'name': name.strip(), 'code': code.strip()})
    except FileNotFoundError:
        logger.error(f'找不到股票列表文件: {filepath}')
    except Exception as e:
        logger.error(f'读取股票列表失败: {e}')
    return stocks

# 筛选股票
def filter_stocks(max_stocks=None):
    """
    筛选符合条件的股票

    Args:
        max_stocks: 最多处理的股票数量，None表示处理全部

    Returns:
        list: 符合条件的股票列表
    """
    # 读取股票列表
    stock_list = read_stock_list()
    if not stock_list:
        logger.error('未能读取股票列表')
        return []

    # 如果指定了max_stocks，则只处理前N只
    if max_stocks and max_stocks > 0:
        stock_list = stock_list[:max_stocks]

    print(f'读取到 {len(stock_list)} 只股票')
    
    # 初始化客户端
    client = Quotes.factory(market='std')
    
    # 筛选结果
    results = []
    
    # 测试全部股票
    test_stocks = stock_list
    print(f'开始筛选全部 {len(test_stocks)} 只股票...')
    print('(筛选条件较严格，可能需要一些时间...)')
    
    for stock_info in test_stocks:
        stock = stock_info['code']
        name = stock_info['name']
        
        try:
            # 获取实时行情
            data = client.quotes(symbol=stock)
            if data is None or data.empty:
                continue
            
            row = data.iloc[0]
            price = row['price']
            vol = row['vol']  # 成交量（手）
            
            # 获取财务数据
            finance_data = client.finance(symbol=stock)
            if finance_data is None or finance_data.empty:
                continue
            
            liutongguben = finance_data.iloc[0]['liutongguben']
            if liutongguben <= 0:
                continue
            
            # 计算换手率
            turnover_rate = vol * 100 / liutongguben * 100
            
            # 获取K线数据（用于量比、筹码集中度、连续上涨判断）
            kline_data = client.bars(symbol=stock, frequency=9, offset=10)
            if kline_data is None or len(kline_data) < 5:
                continue
            
            # 计算量比
            today_vol = vol
            prev_5_vol = kline_data['vol'].iloc[-6:-1].mean() if len(kline_data) >= 6 else kline_data['vol'].mean()
            volume_ratio = today_vol / prev_5_vol if prev_5_vol > 0 else 0
            
            # 判断连续两日上涨（动态获取最近两个交易日）
            if len(kline_data) < 3:
                continue

            # 取最近3天的收盘价（最近3个交易日）
            recent_close = kline_data['close'].tail(3).values
            if len(recent_close) < 3:
                continue

            # 判断连续两日上涨
            day1_to_day2_up = recent_close[1] > recent_close[0]  # 第1天到第2天上涨
            day2_to_day3_up = recent_close[2] > recent_close[1]  # 第2天到第3天上涨
            
            if not (day1_to_day2_up and day2_to_day3_up):
                continue
            
            # 计算筹码集中度（优化版本）
            prices = kline_data['close'].values
            volumes = kline_data['vol'].values * 100

            if len(prices) == 0 or volumes.sum() == 0:
                continue

            # 计算成交量加权平均价格
            vwap = np.average(prices, weights=volumes)

            # 计算筹码集中度（使用成交量加权的5%和95%分位数）
            sorted_indices = np.argsort(prices)
            sorted_prices = prices[sorted_indices]
            sorted_volumes = volumes[sorted_indices]

            # 计算累积成交量分布
            cumvol = np.cumsum(sorted_volumes)
            total_vol = cumvol[-1]

            # 找到5%和95%分位数对应的价格
            low_idx = np.searchsorted(cumvol, total_vol * 0.05)
            high_idx = np.searchsorted(cumvol, total_vol * 0.95)

            cost_low = sorted_prices[max(0, low_idx)]
            cost_high = sorted_prices[min(len(sorted_prices)-1, high_idx)]
            chip_concentration = (cost_high - cost_low) / vwap * 100 if vwap > 0 else 0
            
            # 调试：打印接近条件的股票
            debug = False
            if debug and (turnover_rate > 10 or volume_ratio > 1.2):
                print(f'  {name}({stock}): 换手率{round(turnover_rate,2)}%, 量比{round(volume_ratio,2)}, 筹码{round(chip_concentration,2)}%, 连涨{day1_to_day2_up and day2_to_day3_up}')
            
            # 筛选条件：
            # 1. 换手率 > 15%
            # 2. 量比 > 1.5
            # 3. 90%筹码集中度 < 20%
            # 4. 连续两日上涨
            if turnover_rate > 15 and volume_ratio > 1.5 and chip_concentration < 20 and (day1_to_day2_up and day2_to_day3_up):
                results.append({
                    'name': name,
                    'code': stock,
                    'turnover_rate': round(turnover_rate, 2),
                    'volume_ratio': round(volume_ratio, 2),
                    'chip_concentration': round(chip_concentration, 2),
                    'price': price
                })
                print(f'✓ {name}({stock}): 换手率{round(turnover_rate,2)}%, 量比{round(volume_ratio,2)}, 筹码{round(chip_concentration,2)}%')
            
        except Exception as e:
            logger.warning(f'处理股票 {name}({stock}) 时出错: {e}')
            continue

    try:
        client.close()
    except Exception as e:
        logger.error(f'关闭客户端连接时出错: {e}')

    return results

# 执行筛选
print('开始筛选股票...')
print('条件：换手率>15%, 量比>1.5, 90%筹码集中度<20%, 连续两日上涨(最近两个交易日)')
print()

results = filter_stocks()

print()
print(f'筛选完成，共找到 {len(results)} 只符合条件的股票')
print()

if results:
    print('结果列表：')
    print(f"{'名称':<10} {'代码':<10} {'换手率':<10} {'量比':<10} {'筹码集中度':<10}")
    print('-' * 60)
    for r in results:
        print(f"{r['name']:<10} {r['code']:<10} {r['turnover_rate']:<10}% {r['volume_ratio']:<10} {r['chip_concentration']:<10}%")
else:
    print('没有找到符合条件的股票')