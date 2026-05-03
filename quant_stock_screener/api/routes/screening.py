"""
筛选结果 API 路由
"""

import logging

from flask import Blueprint, request

from ..helpers import success_response, error_response

logger = logging.getLogger(__name__)

screening_bp = Blueprint("screening", __name__, url_prefix="/api")


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


@screening_bp.route("/screening-results", methods=["GET"])
def get_screening_results():
    """获取筛选结果列表"""
    try:
        db = _get_db()
        strategy_id = request.args.get("strategy_id", type=int)
        limit = request.args.get("limit", 20, type=int)
        page = request.args.get("page", 1, type=int)

        results = db.get_screening_results(strategy_id=strategy_id, limit=limit)
        return success_response(
            {
                "items": [r.to_dict() for r in results],
                "page": page,
                "limit": limit,
            }
        )
    except Exception as e:
        logger.error(f"Failed to get screening results: {e}")
        return error_response(str(e), 500)


@screening_bp.route("/screening-results/<int:result_id>", methods=["GET"])
def get_screening_result(result_id: int):
    """获取筛选结果详情"""
    try:
        db = _get_db()
        result = db.get_screening_result(result_id)
        if not result:
            return error_response(f"Result {result_id} not found", 404)

        result_dict = result.to_dict()
        result_dict["items"] = [item.to_dict() for item in result.items]
        return success_response(result_dict)
    except Exception as e:
        logger.error(f"Failed to get screening result: {e}")
        return error_response(str(e), 500)


@screening_bp.route("/screening-results/<int:result_id>", methods=["DELETE"])
def delete_screening_result(result_id: int):
    """删除筛选结果"""
    try:
        db = _get_db()
        success = db.delete_screening_result(result_id)
        if not success:
            return error_response(f"Result {result_id} not found", 404)
        return success_response(None, "Result deleted")
    except Exception as e:
        logger.error(f"Failed to delete screening result: {e}")
        return error_response(str(e), 500)


@screening_bp.route("/screening-results/<int:result_id>/analyze", methods=["POST"])
def analyze_screening_result(result_id: int):
    """使用 Agent 分析筛选结果"""
    try:
        db = _get_db()
        result = db.get_screening_result(result_id)
        if not result:
            return error_response(f"Result {result_id} not found", 404)

        stocks_data = [item.to_dict() for item in result.items]
        if not stocks_data:
            return error_response("No stock data to analyze")

        coordinator = _get_coordinator()
        if not coordinator.is_available:
            return error_response("AI service not available", 503)

        # 使用 Agent 进行结果分析
        analysis = coordinator.analyze_results(stocks_data)

        # 使用 Agent 检测异常
        anomalies = coordinator.detect_anomalies(stocks_data)

        return success_response(
            {
                "analysis": analysis,
                "anomalies": anomalies,
                "stocks_analyzed": len(stocks_data),
            },
            "AI analysis complete",
        )
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return error_response(str(e), 500)


@screening_bp.route("/screening/execute", methods=["POST"])
def execute_screening():
    """执行筛选"""
    try:
        db = _get_db()
        data = request.get_json() or {}
        strategy_id = data.get("strategy_id")

        if not strategy_id:
            return error_response("Missing strategy_id")

        strategy = db.get_strategy(strategy_id)
        if not strategy:
            return error_response(f"Strategy {strategy_id} not found", 404)

        result = db.create_screening_result(
            strategy_id=strategy_id, total_stocks=0, matched_count=0, status="pending"
        )
        return success_response(result.to_dict(), "Screening task created")
    except Exception as e:
        logger.error(f"Screening execution failed: {e}")
        return error_response(str(e), 500)
