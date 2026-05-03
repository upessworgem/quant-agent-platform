"""
API 路由模块

Flask Blueprint 拆分为独立的路由文件
"""

from .routes import register_blueprints

__all__ = ["register_blueprints"]
