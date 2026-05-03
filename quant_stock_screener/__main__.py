"""
Quant Stock Screener - CLI entry point

Usage:
    python -m quant_stock_screener --serve     # Start Flask server
    python -m quant_stock_screener --screen    # Run stock screening
"""

import argparse
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_server(host: str, port: int, debug: bool):
    """Start the Flask API server"""
    from .web.app import create_app

    app = create_app()
    logger.info(f"Starting server at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


def run_screening(strategy_desc: str, output_format: str, max_stocks: int, use_ai: bool):
    """Run stock screening"""
    from .config.settings import Settings
    from .core.data_fetcher import DataFetcher, StockDataProcessor, StockListLoader
    from .core.strategy_engine import StrategyEngine, StrategyBuilder
    from .agents.coordinator import AgentCoordinator
    from .ai.llm_client import create_llm_client

    settings = Settings()
    stock_codes = StockListLoader.load_from_txt("stock_list.txt")

    if not stock_codes:
        logger.error("No stock list found")
        return

    logger.info(f"Loaded {len(stock_codes)} stocks")

    with DataFetcher() as fetcher:
        raw_data = fetcher.get_realtime_quotes(stock_codes)

    if not raw_data:
        logger.error("Failed to fetch stock data")
        return

    processed = []
    for stock in raw_data:
        item = {
            "code": stock.get("code", ""),
            "name": stock.get("name", ""),
            "price": stock.get("price", 0),
            "turnover_rate": StockDataProcessor.calculate_turnover_rate(
                stock.get("volume", 0), stock.get("circulating_shares", 0)
            ),
            "volume_ratio": stock.get("volume_ratio", 0),
            "chip_concentration": stock.get("chip_concentration", 0),
        }
        processed.append(item)

    if use_ai and settings.is_ai_available:
        llm_client = create_llm_client(
            settings.ai.provider, settings.ai.api_key, settings.ai.model
        )
        coordinator = AgentCoordinator(llm_client)
        strategy_dict = coordinator.generate_strategy(strategy_desc)
        conditions = strategy_dict.get("conditions", [])
    else:
        if strategy_desc:
            strategy = StrategyBuilder.create_custom(
                "custom", strategy_desc, [], sort_by="turnover_rate"
            )
        else:
            strategy = StrategyBuilder.create_momentum()
        conditions = [
            {
                "field": c.field,
                "operator": c.operator,
                "value": c.value,
                "value2": c.value2,
                "enabled": c.enabled,
            }
            for c in strategy.conditions
        ]

    engine = StrategyEngine()
    results = engine.execute(processed, conditions)

    if max_stocks:
        results = results[:max_stocks]

    if output_format == "json":
        import json
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif output_format == "csv":
        if results:
            print(",".join(results[0].keys()))
            for r in results:
                print(",".join(str(v) for v in r.values()))
    else:
        print(f"\n{'='*60}")
        print(f"Screening Results: {len(results)} stocks matched")
        print(f"{'='*60}")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r.get('code')} {r.get('name')} | Price: {r.get('price')} | Turnover: {r.get('turnover_rate')}%")


def main():
    parser = argparse.ArgumentParser(description="Quant Stock Screener v2.0")
    parser.add_argument("--serve", action="store_true", help="Start Flask API server")
    parser.add_argument("--screen", action="store_true", help="Run stock screening")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 5000)), help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--strategy-desc", type=str, help="Strategy description (natural language)")
    parser.add_argument("--output", choices=["table", "json", "csv"], default="table", help="Output format")
    parser.add_argument("--max-stocks", type=int, default=50, help="Max stocks to return")
    parser.add_argument("--use-ai", action="store_true", help="Use AI agent for strategy")

    args = parser.parse_args()

    if args.serve:
        run_server(args.host, args.port, args.debug)
    elif args.screen:
        run_screening(args.strategy_desc, args.output, args.max_stocks, args.use_ai)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
