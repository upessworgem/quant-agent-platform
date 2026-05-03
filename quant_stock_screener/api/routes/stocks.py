"""
股票管理 API 路由
"""

import logging
from datetime import datetime

from flask import Blueprint, request

from ..helpers import success_response, error_response

logger = logging.getLogger(__name__)

stocks_bp = Blueprint("stocks", __name__, url_prefix="/api/stocks")


def _get_db():
    from ...database.operations import Database
    return Database()


@stocks_bp.route("", methods=["GET"])
def get_stocks():
    """获取股票列表"""
    try:
        db = _get_db()
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        search = request.args.get("search", "")
        exchange = request.args.get("exchange")
        industry = request.args.get("industry")

        offset = (page - 1) * limit
        stocks = db.get_all_stocks(limit=limit, offset=offset)

        result = []
        for stock in stocks:
            stock_dict = stock.to_dict()
            if search and search not in stock_dict["name"] and search not in stock_dict["code"]:
                continue
            if exchange and stock_dict.get("exchange") != exchange:
                continue
            if industry and stock_dict.get("industry") != industry:
                continue
            result.append(stock_dict)

        return success_response(
            {
                "items": result,
                "page": page,
                "limit": limit,
                "total": db.get_statistics()["stocks_count"],
            }
        )
    except Exception as e:
        logger.error(f"Failed to get stocks: {e}")
        return error_response(str(e), 500)


@stocks_bp.route("/<code>", methods=["GET"])
def get_stock(code: str):
    """获取单个股票详情"""
    try:
        db = _get_db()
        stock = db.get_stock_by_code(code)
        if not stock:
            return error_response(f"Stock {code} not found", 404)
        return success_response(stock.to_dict())
    except Exception as e:
        logger.error(f"Failed to get stock: {e}")
        return error_response(str(e), 500)


@stocks_bp.route("", methods=["POST"])
def create_stock():
    """创建股票"""
    try:
        db = _get_db()
        data = request.get_json()
        if not data or "code" not in data or "name" not in data:
            return error_response("Missing required fields: code, name")

        stock = db.create_stock(
            code=data["code"],
            name=data["name"],
            exchange=data.get("exchange"),
            industry=data.get("industry"),
        )
        return success_response(stock.to_dict(), "Stock created")
    except Exception as e:
        logger.error(f"Failed to create stock: {e}")
        return error_response(str(e), 500)


@stocks_bp.route("/<code>", methods=["PUT"])
def update_stock(code: str):
    """更新股票信息"""
    try:
        db = _get_db()
        data = request.get_json()
        if not data:
            return error_response("Request body cannot be empty")

        stock = db.update_stock(code, **data)
        if not stock:
            return error_response(f"Stock {code} not found", 404)
        return success_response(stock.to_dict(), "Stock updated")
    except Exception as e:
        logger.error(f"Failed to update stock: {e}")
        return error_response(str(e), 500)


@stocks_bp.route("/<code>", methods=["DELETE"])
def delete_stock(code: str):
    """删除股票"""
    try:
        db = _get_db()
        success = db.delete_stock(code)
        if not success:
            return error_response(f"Stock {code} not found", 404)
        return success_response(None, "Stock deleted")
    except Exception as e:
        logger.error(f"Failed to delete stock: {e}")
        return error_response(str(e), 500)


@stocks_bp.route("/bulk", methods=["POST"])
def bulk_import_stocks():
    """批量导入股票"""
    try:
        db = _get_db()
        data = request.get_json()
        if not data or "stocks" not in data:
            return error_response("Missing stocks field")

        count = db.bulk_import_stocks(data["stocks"])
        return success_response({"imported": count}, f"Imported {count} stocks")
    except Exception as e:
        logger.error(f"Bulk import failed: {e}")
        return error_response(str(e), 500)


@stocks_bp.route("/<code>/history", methods=["GET"])
def get_stock_history(code: str):
    """获取股票历史数据"""
    try:
        db = _get_db()
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        limit = request.args.get("limit", 30, type=int)

        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        history = db.get_historical_data(
            stock_code=code, start_date=start_date, end_date=end_date, limit=limit
        )
        return success_response([h.to_dict() for h in history])
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        return error_response(str(e), 500)


@stocks_bp.route("/<code>/history", methods=["POST"])
def save_stock_history(code: str):
    """保存股票历史数据"""
    try:
        db = _get_db()
        data = request.get_json()
        if not data:
            return error_response("Request body cannot be empty")

        if "data" in data:
            count = db.bulk_save_historical_data(code, data["data"])
            return success_response({"saved": count}, f"Saved {count} records")
        else:
            historical = db.save_historical_data(code, data)
            return success_response(historical.to_dict(), "Data saved")
    except Exception as e:
        logger.error(f"Failed to save history: {e}")
        return error_response(str(e), 500)
