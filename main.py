#!/usr/bin/env python3
"""
主入口模块 - 协调所有组件工作
解耦的架构设计：
- config: 配置管理
- data_fetcher: 数据获取
- strategy: 策略执行
- ai_analyzer: AI/LLM 分析 (可选)
"""

import os
import sys
import json
import logging
from typing import Optional, List, Dict
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config import ConfigManager, AppConfig, AIConfig
from data_fetcher import (
    DataFetcher, StockDataProcessor, StockListLoader,
    StockQuote, StockFinance, KLineData
)
from strategy import StrategyExecutor, StrategyBuilder
from ai_analyzer import AIAnalyzer, create_llm_client


class StockScreener:
    """
    股票筛选器主类 - 协调各模块工作
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.ai_analyzer: Optional[AIAnalyzer] = None
        self._init_ai()

    def _init_ai(self):
        """初始化 AI 模块（如果配置启用）"""
        if not self.config.ai.enabled:
            logger.info("AI 功能未启用")
            return

        try:
            llm_client = create_llm_client(
                provider=self.config.ai.provider,
                api_key=self.config.ai.api_key,
                model=self.config.ai.model
            )
            self.ai_analyzer = AIAnalyzer(llm_client)
            logger.info(f"AI 模块已初始化: {self.config.ai.provider}/{self.config.ai.model}")
        except Exception as e:
            logger.error(f"AI 模块初始化失败: {e}")
            self.ai_analyzer = None

    def run_interactive(self):
        """交互式运行模式"""
        print("\n" + "=" * 60)
        print("  股票智能筛选系统")
        print("=" * 60 + "\n")

        # 检查是否有自然语言输入
        if self.config.ai.natural_language_input and self.ai_analyzer:
            print(f"检测到策略描述: {self.config.ai.natural_language_input}")
            print("正在使用 AI 生成策略...")

            strategy_dict = self.ai_analyzer.generate_strategy_from_natural_language(
                self.config.ai.natural_language_input
            )

            if "error" not in strategy_dict:
                # 从 AI 返回的策略创建 StrategyConfig
                from config import FilterCondition, StrategyConfig
                self.config.strategy = StrategyConfig(
                    name=strategy_dict.get("name", "ai_generated"),
                    description=strategy_dict.get("description", ""),
                    conditions=[
                        FilterCondition(**c)
                        for c in strategy_dict.get("conditions", [])
                    ],
                    sort_by=strategy_dict.get("sort_by"),
                    sort_desc=strategy_dict.get("sort_desc", True),
                    max_stocks=strategy_dict.get("max_stocks")
                )
                print(f"✓ AI 生成策略: {self.config.strategy.name}")
                print(f"  描述: {self.config.strategy.description}")
                print(f"  条件数: {len(self.config.strategy.conditions)}")
            else:
                print(f"✗ AI 策略生成失败，使用默认策略")
                self.config._default_strategy()
        else:
            # 使用默认策略
            self.config._default_strategy()
            print(f"使用默认策略: {self.config.strategy.name}")

        # 执行筛选
        results = self.run_screening()

        # AI 分析结果
        if self.ai_analyzer and self.config.ai.analyze_results and results:
            print("\n" + "-" * 60)
            print("AI 正在分析筛选结果...")
            analysis = self.ai_analyzer.analyze_results(results)
            print("\n【AI 分析报告】\n")
            print(analysis)

        return results

    def run_screening(self, max_stocks: Optional[int] = None) -> List[Dict]:
        """
        执行股票筛选
        """
        strategy = self.config.strategy
        if strategy is None:
            logger.error("未配置策略")
            return []

        print(f"\n开始执行策略: {strategy.name}")
        print(f"描述: {strategy.description}")
        print("\n筛选条件:")
        for cond in strategy.conditions:
            if cond.enabled:
                print(f"  - {cond.name}: {cond.field} {cond.operator} {cond.value}")
        print()

        # 加载股票列表
        stocks = StockListLoader.load_from_txt(self.config.app.stock_list_file)
        if not stocks:
            logger.error("未能加载股票列表")
            return []

        if max_stocks:
            stocks = stocks[:max_stocks]
            logger.info(f"限制处理前 {max_stocks} 只股票")

        total = len(stocks)
        print(f"准备筛选 {total} 只股票...")
        print("(可能需要一些时间，请耐心等待)\n")

        # 获取数据并筛选
        results = []
        executor = StrategyExecutor(self.config)

        with DataFetcher() as fetcher:
            for i, stock_info in enumerate(stocks):
                code = stock_info['code']
                name = stock_info['name']

                try:
                    # 获取数据
                    quote = fetcher.get_quote(code)
                    if quote is None:
                        continue

                    finance = fetcher.get_finance(code)
                    if finance is None:
                        continue

                    kline = fetcher.get_kline(code, frequency=9, offset=10)

                    # 整合数据
                    data = StockDataProcessor.enrich_stock_data(
                        code=code,
                        name=name,
                        quote=quote,
                        finance=finance,
                        kline=kline
                    )

                    # 执行策略筛选
                    if executor.evaluate_strategy(strategy, data):
                        results.append(data)
                        print(f"✓ {name}({code}): 换手率{data['turnover_rate']:.2f}%, "
                              f"量比{data['volume_ratio']:.2f}, "
                              f"筹码{data['chip_concentration']:.2f}%")

                except Exception as e:
                    logger.warning(f"处理 {name}({code}) 时出错: {e}")
                    continue

                # 进度显示
                if (i + 1) % 100 == 0:
                    print(f"  ...已处理 {i + 1}/{total} 只 ({(i+1)/total*100:.1f}%)...")

        # 排序
        if strategy.sort_by:
            results.sort(
                key=lambda x: x.get(strategy.sort_by, 0) or 0,
                reverse=strategy.sort_desc
            )

        # 限制数量
        if strategy.max_stocks and len(results) > strategy.max_stocks:
            results = results[:strategy.max_stocks]

        # 输出结果
        print("\n" + "=" * 60)
        print(f"筛选完成！共找到 {len(results)} 只符合条件的股票")
        print("=" * 60)

        if results:
            print(f"\n{'名称':<10} {'代码':<10} {'价格':<8} {'换手率':<10} {'量比':<8} {'筹码集中度':<10}")
            print("-" * 60)
            for r in results:
                print(f"{r['name']:<10} {r['code']:<10} {r['price']:<8.2f} "
                      f"{r['turnover_rate']:<10.2f} {r['volume_ratio']:<8.2f} {r['chip_concentration']:<10.2f}")

            # 保存结果
            if self.config.app.save_results:
                self._save_results(results)
        else:
            print("没有找到符合条件的股票")

        return results

    def _save_results(self, results: List[Dict]):
        """保存结果到文件"""
        filepath = self.config.app.results_file or "results.json"
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存: {filepath}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")

    def quick_screen(self, **kwargs) -> List[Dict]:
        """
        快速筛选接口 - 程序化调用
        """
        # 可以在这里动态修改策略参数
        return self.run_screening(**kwargs)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="股票智能筛选系统")

    parser.add_argument(
        "--strategy-desc",
        type=str,
        help="用自然语言描述策略 (需要 AI 配置)"
    )

    parser.add_argument(
        "--max-stocks",
        type=int,
        default=None,
        help="最多处理的股票数量"
    )

    parser.add_argument(
        "--ai-provider",
        type=str,
        choices=["anthropic", "openai", "mock"],
        help="AI 提供商"
    )

    parser.add_argument(
        "--output",
        type=str,
        choices=["table", "json", "csv"],
        default="table",
        help="输出格式"
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="保存结果到文件"
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 初始化配置
    config = ConfigManager()

    # 命令行参数覆盖配置
    if args.strategy_desc:
        config.ai.natural_language_input = args.strategy_desc
        config.ai.generate_strategy = True
        config.ai.enabled = True

    if args.ai_provider:
        config.ai.provider = args.ai_provider
        config.ai.enabled = True

    if args.save:
        config.app.save_results = True

    config.app.output_format = args.output

    # 确保 API key
    if config.ai.enabled and not config.ai.api_key:
        if api_key := os.getenv("ANTHROPIC_API_KEY"):
            config.ai.api_key = api_key
        elif api_key := os.getenv("OPENAI_API_KEY"):
            config.ai.provider = "openai"
            config.ai.api_key = api_key
        else:
            print("警告: 未设置 AI API Key，AI 功能将不可用")
            print("请设置环境变量 ANTHROPIC_API_KEY 或 OPENAI_API_KEY")
            config.ai.enabled = False

    # 创建并运行筛选器
    screener = StockScreener(config)
    results = screener.run_interactive()

    return results


if __name__ == "__main__":
    main()
