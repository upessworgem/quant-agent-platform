"""
Flask 应用工厂
"""

import os
import logging
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS

from ..api.routes import register_blueprints
from .middlewares import register_middlewares, register_error_handlers, handle_api_exception

logger = logging.getLogger(__name__)


def create_app(config_name: str = "default") -> Flask:
    """应用工厂函数"""

    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["JSON_AS_ASCII"] = False
    app.config["JSON_SORT_KEYS"] = False

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["*"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    register_blueprints(app)
    register_middlewares(app)
    register_error_handlers(app)
    handle_api_exception(app)
    _register_root_routes(app)
    _init_data(app)

    logger.info("Flask app created")
    return app


def _register_root_routes(app: Flask):
    @app.route("/")
    def index():
        return jsonify(
            {
                "name": "Quant Stock Screener API",
                "version": "2.0.0",
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "endpoints": {
                    "health": "/api/health",
                    "statistics": "/api/statistics",
                    "stocks": "/api/stocks",
                    "strategies": "/api/strategies",
                    "screening_results": "/api/screening-results",
                    "configs": "/api/configs",
                },
            }
        )

    @app.route("/docs")
    def docs():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Quant Stock Screener API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                h2 { color: #666; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f5f5f5; }
                code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
                .method-get { color: #00a854; font-weight: bold; }
                .method-post { color: #108ee9; font-weight: bold; }
                .method-put { color: #ff9800; font-weight: bold; }
                .method-delete { color: #f44336; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>Quant Stock Screener API v2.0</h1>
            <h2>Base URL</h2>
            <p><code>http://localhost:5000/api</code></p>
            <h2>Endpoints</h2>
            <h3>Stocks</h3>
            <table>
                <tr><th>Method</th><th>Path</th><th>Description</th></tr>
                <tr><td class="method-get">GET</td><td>/stocks</td><td>List stocks</td></tr>
                <tr><td class="method-get">GET</td><td>/stocks/:code</td><td>Get stock detail</td></tr>
                <tr><td class="method-post">POST</td><td>/stocks</td><td>Create stock</td></tr>
                <tr><td class="method-post">POST</td><td>/stocks/bulk</td><td>Bulk import</td></tr>
                <tr><td class="method-put">PUT</td><td>/stocks/:code</td><td>Update stock</td></tr>
                <tr><td class="method-delete">DELETE</td><td>/stocks/:code</td><td>Delete stock</td></tr>
                <tr><td class="method-get">GET</td><td>/stocks/:code/history</td><td>Historical data</td></tr>
            </table>
            <h3>Strategies</h3>
            <table>
                <tr><th>Method</th><th>Path</th><th>Description</th></tr>
                <tr><td class="method-get">GET</td><td>/strategies</td><td>List strategies</td></tr>
                <tr><td class="method-post">POST</td><td>/strategies</td><td>Create strategy</td></tr>
                <tr><td class="method-post">POST</td><td>/strategies/generate</td><td>AI generate strategy</td></tr>
                <tr><td class="method-post">POST</td><td>/strategies/:id/duplicate</td><td>Duplicate strategy</td></tr>
                <tr><td class="method-put">PUT</td><td>/strategies/:id</td><td>Update strategy</td></tr>
                <tr><td class="method-delete">DELETE</td><td>/strategies/:id</td><td>Delete strategy</td></tr>
            </table>
            <h3>Screening</h3>
            <table>
                <tr><th>Method</th><th>Path</th><th>Description</th></tr>
                <tr><td class="method-get">GET</td><td>/screening-results</td><td>List results</td></tr>
                <tr><td class="method-get">GET</td><td>/screening-results/:id</td><td>Get result detail</td></tr>
                <tr><td class="method-delete">DELETE</td><td>/screening-results/:id</td><td>Delete result</td></tr>
                <tr><td class="method-post">POST</td><td>/screening-results/:id/analyze</td><td>AI analyze result</td></tr>
                <tr><td class="method-post">POST</td><td>/screening/execute</td><td>Execute screening</td></tr>
            </table>
            <h3>System</h3>
            <table>
                <tr><th>Method</th><th>Path</th><th>Description</th></tr>
                <tr><td class="method-get">GET</td><td>/statistics</td><td>System statistics</td></tr>
                <tr><td class="method-get">GET</td><td>/configs</td><td>All configs</td></tr>
                <tr><td class="method-post">POST</td><td>/configs</td><td>Set config</td></tr>
                <tr><td class="method-get">GET</td><td>/health</td><td>Health check</td></tr>
            </table>
            <p style="margin-top: 40px; color: #999; text-align: center;">
                Quant Stock Screener &copy; 2024
            </p>
        </body>
        </html>
        """


def _init_data(app: Flask):
    """初始化基础数据"""
    from ..database.operations import Database
    from ..core.data_fetcher import StockListLoader

    with app.app_context():
        db = Database()
        stats = db.get_statistics()

        if stats["stocks_count"] == 0:
            logger.info("Database empty, importing stock list...")

            stocks = StockListLoader.load_from_txt("stock_list.txt")
            if stocks:
                stocks_data = [
                    {
                        "code": s["code"],
                        "name": s["name"],
                        "exchange": "SH" if s["code"].startswith("6") else "SZ",
                        "industry": None,
                    }
                    for s in stocks
                ]
                count = db.bulk_import_stocks(stocks_data)
                logger.info(f"Imported {count} stocks")
