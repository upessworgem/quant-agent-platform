#!/usr/bin/env python3
"""
Flask 应用入口 - Web API 服务
整合所有模块提供 RESTful 接口
"""

import os
import sys
import logging
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入配置和蓝图
from config import ConfigManager
from database import db
from api import api_bp, success_response
from middlewares import register_middlewares, handle_api_exception
from data_fetcher import StockListLoader


def create_app(config_name: str = 'default') -> Flask:
    """应用工厂函数"""

    app = Flask(__name__)

    # 配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JSON_AS_ASCII'] = False
    app.config['JSON_SORT_KEYS'] = False

    # 启用 CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 注册蓝图
    app.register_blueprint(api_bp)

    # 注册中间件
    register_middlewares(app)
    handle_api_exception(app)

    # 错误处理
    register_error_handlers(app)

    # 初始化数据
    init_data(app)

    logger.info("Flask 应用已创建")
    return app


def register_error_handlers(app: Flask):
    """注册错误处理器"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'code': 400,
            'message': 'Bad Request',
            'error': str(error.description if hasattr(error, 'description') else error),
            'timestamp': datetime.now().isoformat()
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 404,
            'message': 'Not Found',
            'error': '请求的资源不存在',
            'timestamp': datetime.now().isoformat()
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'code': 405,
            'message': 'Method Not Allowed',
            'error': '请求方法不被允许',
            'timestamp': datetime.now().isoformat()
        }), 405

    @app.errorhandler(422)
    def validation_error(error):
        """Pydantic 验证错误"""
        return jsonify({
            'code': 422,
            'message': 'Validation Error',
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        }), 422

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal Server Error: {error}")
        return jsonify({
            'code': 500,
            'message': 'Internal Server Error',
            'error': '服务器内部错误',
            'timestamp': datetime.now().isoformat()
        }), 500

    # 捕获所有未处理的异常
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.exception("Unhandled exception")
        return jsonify({
            'code': 500,
            'message': 'Internal Server Error',
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        }), 500


# 初始化数据
    init_data(app)

    logger.info("Flask 应用已创建")
    return app


def register_error_handlers(app: Flask):
    """注册错误处理器"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'code': 400,
            'message': 'Bad Request',
            'error': str(error.description if hasattr(error, 'description') else error),
            'timestamp': datetime.now().isoformat()
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 404,
            'message': 'Not Found',
            'error': '请求的资源不存在',
            'timestamp': datetime.now().isoformat()
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'code': 405,
            'message': 'Method Not Allowed',
            'error': '请求方法不被允许',
            'timestamp': datetime.now().isoformat()
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'code': 500,
            'message': 'Internal Server Error',
            'error': '服务器内部错误',
            'timestamp': datetime.now().isoformat()
        }), 500


def init_data(app: Flask):
    """初始化基础数据"""
    with app.app_context():
        # 检查是否需要导入股票列表
        stats = db.get_statistics()

        if stats['stocks_count'] == 0:
            logger.info("数据库为空，开始导入股票列表...")

            # 从文件加载股票列表
            stocks = StockListLoader.load_from_txt('stock_list.txt')

            if stocks:
                # 准备数据
                stocks_data = [
                    {
                        'code': s['code'],
                        'name': s['name'],
                        'exchange': s['code'].startswith('6') and 'SH' or 'SZ',
                        'industry': None
                    }
                    for s in stocks
                ]

                # 批量导入
                count = db.bulk_import_stocks(stocks_data)
                logger.info(f"成功导入 {count} 只股票")

                # 创建默认策略
                create_default_strategies()
            else:
                logger.warning("未能加载股票列表文件")


def create_default_strategies():
    """创建默认策略"""
    from strategy import StrategyBuilder

    # 动量策略
    momentum = StrategyBuilder.create_momentum_strategy()
    db.create_strategy(
        name=momentum.name,
        description=momentum.description,
        conditions=[
            {
                'name': c.name,
                'field': c.field,
                'operator': c.operator,
                'value': c.value,
                'enabled': c.enabled
            }
            for c in momentum.conditions
        ],
        strategy_type='builtin',
        sort_by=momentum.sort_by,
        sort_desc=momentum.sort_desc
    )

    logger.info(f"创建默认策略: {momentum.name}")


# ========== 根路由 ==========

def create_root_routes(app: Flask):
    """创建根路由"""

    @app.route('/')
    def index():
        """API 首页"""
        return jsonify({
            'name': '股票智能筛选系统 API',
            'version': '1.0.0',
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'health': '/api/health',
                'statistics': '/api/statistics',
                'stocks': '/api/stocks',
                'strategies': '/api/strategies',
                'screening_results': '/api/screening-results',
                'configs': '/api/configs',
            }
        })

    @app.route('/docs')
    def docs():
        """API 文档"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>股票筛选系统 API 文档</title>
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
            <h1>股票智能筛选系统 API 文档</h1>

            <h2>基础信息</h2>
            <p>Base URL: <code>http://localhost:5000/api</code></p>

            <h2>接口列表</h2>

            <h3>股票管理</h3>
            <table>
                <tr><th>方法</th><th>路径</th><th>说明</th></tr>
                <tr><td class="method-get">GET</td><td>/stocks</td><td>获取股票列表</td></tr>
                <tr><td class="method-get">GET</td><td>/stocks/:code</td><td>获取股票详情</td></tr>
                <tr><td class="method-post">POST</td><td>/stocks</td><td>创建股票</td></tr>
                <tr><td class="method-post">POST</td><td>/stocks/bulk</td><td>批量导入股票</td></tr>
                <tr><td class="method-put">PUT</td><td>/stocks/:code</td><td>更新股票</td></tr>
                <tr><td class="method-delete">DELETE</td><td>/stocks/:code</td><td>删除股票</td></tr>
                <tr><td class="method-get">GET</td><td>/stocks/:code/history</td><td>获取历史数据</td></tr>
                <tr><td class="method-post">POST</td><td>/stocks/:code/history</td><td>保存历史数据</td></tr>
            </table>

            <h3>策略管理</h3>
            <table>
                <tr><th>方法</th><th>路径</th><th>说明</th></tr>
                <tr><td class="method-get">GET</td><td>/strategies</td><td>获取策略列表</td></tr>
                <tr><td class="method-get">GET</td><td>/strategies/:id</td><td>获取策略详情</td></tr>
                <tr><td class="method-post">POST</td><td>/strategies</td><td>创建策略</td></tr>
                <tr><td class="method-post">POST</td><td>/strategies/generate</td><td>AI生成策略</td></tr>
                <tr><td class="method-post">POST</td><td>/strategies/:id/duplicate</td><td>复制策略</td></tr>
                <tr><td class="method-put">PUT</td><td>/strategies/:id</td><td>更新策略</td></tr>
                <tr><td class="method-delete">DELETE</td><td>/strategies/:id</td><td>删除策略</td></tr>
            </table>

            <h3>筛选结果</h3>
            <table>
                <tr><th>方法</th><th>路径</th><th>说明</th></tr>
                <tr><td class="method-get">GET</td><td>/screening-results</td><td>获取结果列表</td></tr>
                <tr><td class="method-get">GET</td><td>/screening-results/:id</td><td>获取结果详情</td></tr>
                <tr><td class="method-delete">DELETE</td><td>/screening-results/:id</td><td>删除结果</td></tr>
                <tr><td class="method-post">POST</td><td>/screening-results/:id/analyze</td><td>AI分析结果</td></tr>
                <tr><td class="method-post">POST</td><td>/screening/execute</td><td>执行筛选</td></tr>
            </table>

            <h3>系统配置</h3>
            <table>
                <tr><th>方法</th><th>路径</th><th>说明</th></tr>
                <tr><td class="method-get">GET</td><td>/statistics</td><td>获取统计信息</td></tr>
                <tr><td class="method-get">GET</td><td>/configs</td><td>获取所有配置</td></tr>
                <tr><td class="method-get">GET</td><td>/configs/:key</td><td>获取配置</td></tr>
                <tr><td class="method-post">POST</td><td>/configs</td><td>设置配置</td></tr>
                <tr><td class="method-delete">DELETE</td><td>/configs/:key</td><td>删除配置</td></tr>
                <tr><td class="method-get">GET</td><td>/health</td><td>健康检查</td></tr>
            </table>

            <h2>示例请求</h2>

            <h3>创建策略</h3>
            <pre><code>POST /api/strategies
Content-Type: application/json

{
    "name": "高换手策略",
    "description": "选择换手率大于15%的股票",
    "conditions": [
        {
            "name": "换手率",
            "field": "turnover_rate",
            "operator": ">",
            "value": 15,
            "enabled": true
        }
    ]
}</code></pre>

            <h3>AI生成策略</h3>
            <pre><code>POST /api/strategies/generate
Content-Type: application/json

{
    "description": "找出近期放量突破、换手率大于20%的股票",
    "ai_provider": "anthropic"
}</code></pre>

            <p style="margin-top: 40px; color: #999; text-align: center;">
                股票智能筛选系统 &copy; 2024
            </p>
        </body>
        </html>
        """


def init_app(app: Flask):
    """初始化应用"""
    create_root_routes(app)


# 创建应用实例
app = create_app()
init_app(app)


if __name__ == '__main__':
    # 开发模式运行
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'

    logger.info(f"启动 Flask 服务: http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
