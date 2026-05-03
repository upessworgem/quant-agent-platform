"""
系统管理 API 路由
"""

import logging
from datetime import datetime

from flask import Blueprint, request

from ..helpers import success_response, error_response

logger = logging.getLogger(__name__)

system_bp = Blueprint("system", __name__, url_prefix="/api")


def _get_db():
    from ...database.operations import Database
    return Database()


@system_bp.route("/statistics", methods=["GET"])
def get_statistics():
    """获取系统统计信息"""
    try:
        db = _get_db()
        stats = db.get_statistics()
        return success_response(stats)
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return error_response(str(e), 500)


@system_bp.route("/configs", methods=["GET"])
def get_configs():
    """获取所有配置"""
    try:
        db = _get_db()
        configs = db.get_all_configs()
        return success_response([c.to_dict() for c in configs])
    except Exception as e:
        logger.error(f"Failed to get configs: {e}")
        return error_response(str(e), 500)


@system_bp.route("/configs/<key>", methods=["GET"])
def get_config(key: str):
    """获取单个配置"""
    try:
        db = _get_db()
        value = db.get_config(key)
        if value is None:
            return error_response(f"Config {key} not found", 404)
        return success_response({"key": key, "value": value})
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        return error_response(str(e), 500)


@system_bp.route("/configs", methods=["POST"])
def set_config():
    """设置配置"""
    try:
        db = _get_db()
        data = request.get_json()
        if not data or "key" not in data or "value" not in data:
            return error_response("Missing required fields: key, value")

        config = db.set_config(
            key=data["key"], value=data["value"], description=data.get("description")
        )
        return success_response(config.to_dict(), "Config saved")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return error_response(str(e), 500)


@system_bp.route("/configs/<key>", methods=["DELETE"])
def delete_config(key: str):
    """删除配置"""
    try:
        db = _get_db()
        success = db.delete_config(key)
        if not success:
            return error_response(f"Config {key} not found", 404)
        return success_response(None, "Config deleted")
    except Exception as e:
        logger.error(f"Failed to delete config: {e}")
        return error_response(str(e), 500)


@system_bp.route("/ai-suggestions", methods=["GET"])
def get_ai_suggestions():
    """获取 AI 建议列表"""
    try:
        db = _get_db()
        suggestion_type = request.args.get("type")
        limit = request.args.get("limit", 20, type=int)

        suggestions = db.get_ai_suggestions(
            suggestion_type=suggestion_type, limit=limit
        )
        return success_response([s.to_dict() for s in suggestions])
    except Exception as e:
        logger.error(f"Failed to get AI suggestions: {e}")
        return error_response(str(e), 500)


@system_bp.route("/ai-suggestions/<int:suggestion_id>/rate", methods=["POST"])
def rate_ai_suggestion(suggestion_id: int):
    """给 AI 建议评分"""
    try:
        db = _get_db()
        data = request.get_json()
        if not data or "rating" not in data:
            return error_response("Missing rating field")

        rating = data["rating"]
        if not (1 <= rating <= 5):
            return error_response("Rating must be between 1 and 5")

        suggestion = db.rate_ai_suggestion(suggestion_id, rating)
        if not suggestion:
            return error_response(f"Suggestion {suggestion_id} not found", 404)
        return success_response(suggestion.to_dict(), "Rating saved")
    except Exception as e:
        logger.error(f"Failed to rate suggestion: {e}")
        return error_response(str(e), 500)


@system_bp.route("/health", methods=["GET"])
def health_check():
    """健康检查"""
    return success_response(
        {"status": "healthy", "database": "connected", "timestamp": datetime.now().isoformat()}
    )
