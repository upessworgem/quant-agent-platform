"""
API 路由注册

将各子蓝图注册到 Flask 应用
"""

from flask import Flask

from .stocks import stocks_bp
from .strategies import strategies_bp
from .screening import screening_bp
from .auth_routes import auth_bp
from .system import system_bp


def register_blueprints(app: Flask):
    """注册所有 API 蓝图"""
    app.register_blueprint(stocks_bp)
    app.register_blueprint(strategies_bp)
    app.register_blueprint(screening_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(system_bp)
