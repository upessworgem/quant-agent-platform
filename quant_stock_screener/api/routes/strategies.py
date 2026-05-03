"""
策略管理 API 路由
"""

import json
import logging

from flask import Blueprint, request

from ..helpers import success_response, error_response

logger = logging.getLogger(__name__)

strategies_bp = Blueprint("strategies", __name__, url_prefix="/api/strategies")


def _get_db():
    from ...database.operations import Database
    return Database()


def _get_coordinator():
    from ...agents.coordinator import AgentCoordinator
    from ...config.settings import Settings
    from ...ai.llm_client import create_llm_client

    settings = Settings()
    if settings.is_ai_available:
        client = create_llm_client(
            settings.ai.provider, settings.ai.api_key, settings.ai.model
        )
        return AgentCoordinator(client)
    return AgentCoordinator()


@strategies_bp.route("", methods=["GET"])
def get_strategies():
    """获取策略列表"""
    try:
        db = _get_db()
        active_only = request.args.get("active_only", "true").lower() == "true"
        strategies = db.get_all_strategies(active_only=active_only)
        return success_response([s.to_dict() for s in strategies])
    except Exception as e:
        logger.error(f"Failed to get strategies: {e}")
        return error_response(str(e), 500)


@strategies_bp.route("/<int:strategy_id>", methods=["GET"])
def get_strategy(strategy_id: int):
    """获取单个策略"""
    try:
        db = _get_db()
        strategy = db.get_strategy(strategy_id)
        if not strategy:
            return error_response(f"Strategy {strategy_id} not found", 404)
        return success_response(strategy.to_dict())
    except Exception as e:
        logger.error(f"Failed to get strategy: {e}")
        return error_response(str(e), 500)


@strategies_bp.route("", methods=["POST"])
def create_strategy():
    """创建策略"""
    try:
        db = _get_db()
        data = request.get_json()
        if not data or "name" not in data or "conditions" not in data:
            return error_response("Missing required fields: name, conditions")

        strategy = db.create_strategy(
            name=data["name"],
            description=data.get("description", ""),
            conditions=data["conditions"],
            strategy_type=data.get("strategy_type", "user"),
            sort_by=data.get("sort_by"),
            sort_desc=data.get("sort_desc", True),
            max_stocks=data.get("max_stocks"),
        )
        return success_response(strategy.to_dict(), "Strategy created")
    except Exception as e:
        logger.error(f"Failed to create strategy: {e}")
        return error_response(str(e), 500)


@strategies_bp.route("/<int:strategy_id>", methods=["PUT"])
def update_strategy(strategy_id: int):
    """更新策略"""
    try:
        db = _get_db()
        data = request.get_json()
        if not data:
            return error_response("Request body cannot be empty")

        strategy = db.update_strategy(strategy_id, **data)
        if not strategy:
            return error_response(f"Strategy {strategy_id} not found", 404)
        return success_response(strategy.to_dict(), "Strategy updated")
    except Exception as e:
        logger.error(f"Failed to update strategy: {e}")
        return error_response(str(e), 500)


@strategies_bp.route("/<int:strategy_id>", methods=["DELETE"])
def delete_strategy(strategy_id: int):
    """删除策略（软删除）"""
    try:
        db = _get_db()
        success = db.delete_strategy(strategy_id)
        if not success:
            return error_response(f"Strategy {strategy_id} not found", 404)
        return success_response(None, "Strategy deleted")
    except Exception as e:
        logger.error(f"Failed to delete strategy: {e}")
        return error_response(str(e), 500)


@strategies_bp.route("/<int:strategy_id>/duplicate", methods=["POST"])
def duplicate_strategy(strategy_id: int):
    """复制策略"""
    try:
        db = _get_db()
        original = db.get_strategy(strategy_id)
        if not original:
            return error_response(f"Strategy {strategy_id} not found", 404)

        new_strategy = db.create_strategy(
            name=f"{original.name} (copy)",
            description=original.description,
            conditions=json.loads(original.conditions_json),
            strategy_type="user",
            sort_by=original.sort_by,
            sort_desc=original.sort_desc,
            max_stocks=original.max_stocks,
        )
        return success_response(new_strategy.to_dict(), "Strategy duplicated")
    except Exception as e:
        logger.error(f"Failed to duplicate strategy: {e}")
        return error_response(str(e), 500)


@strategies_bp.route("/generate", methods=["POST"])
def generate_strategy_with_ai():
    """使用 Agent 生成策略"""
    try:
        db = _get_db()
        data = request.get_json()
        if not data or "description" not in data:
            return error_response("Missing required field: description")

        coordinator = _get_coordinator()
        if not coordinator.is_available:
            return error_response("AI service not available", 503)

        # 使用 Agent 生成策略
        strategy_dict = coordinator.generate_strategy(data["description"])

        if "error" in strategy_dict:
            return error_response(strategy_dict["error"], 500)

        # 保存到数据库
        strategy = db.create_strategy(
            name=strategy_dict.get("name", "AI Generated Strategy"),
            description=strategy_dict.get("description", data["description"]),
            conditions=strategy_dict.get("conditions", []),
            strategy_type="ai",
            sort_by=strategy_dict.get("sort_by"),
            sort_desc=strategy_dict.get("sort_desc", True),
            max_stocks=strategy_dict.get("max_stocks"),
        )

        # 保存 AI 建议记录
        db.save_ai_suggestion(
            suggestion_type="strategy_generation",
            input_data=data["description"],
            output_data=json.dumps(strategy_dict, ensure_ascii=False),
            ai_provider=data.get("ai_provider", "unknown"),
            ai_model=data.get("model", "default"),
            strategy_id=strategy.id,
        )

        return success_response(strategy.to_dict(), "AI strategy generated")
    except Exception as e:
        logger.error(f"AI strategy generation failed: {e}")
        return error_response(str(e), 500)
