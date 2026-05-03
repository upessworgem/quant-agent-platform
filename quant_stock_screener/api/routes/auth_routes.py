"""
认证 API 路由
"""

import logging

from flask import Blueprint, request

from ..helpers import success_response, error_response

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    """用户登录"""
    try:
        from ...web.auth import AuthService, generate_token
        from ...database.operations import Database

        db = Database()
        data = request.get_json()
        if not data or "username" not in data or "password" not in data:
            return error_response("Missing username or password")

        auth_service = AuthService(db)
        user = auth_service.authenticate(data["username"], data["password"])

        if not user:
            return error_response("Invalid credentials", 401)

        token = generate_token(user["id"], user["username"], user["role"])
        return success_response({"token": token, "user": user}, "Login successful")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return error_response(str(e), 500)


@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    """获取当前用户信息"""
    try:
        from ...web.auth import verify_token, AuthService
        from ...database.operations import Database

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return error_response("No auth token provided", 401)

        payload = verify_token(token)
        if not payload:
            return error_response("Invalid or expired token", 401)

        db = Database()
        auth_service = AuthService(db)
        user = auth_service.get_user_by_id(payload["user_id"])

        if not user:
            return error_response("User not found", 404)
        return success_response(user)
    except Exception as e:
        logger.error(f"Get user failed: {e}")
        return error_response(str(e), 500)


@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    """刷新 Token"""
    try:
        from ...web.auth import generate_token, verify_token

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return error_response("No auth token provided", 401)

        payload = verify_token(token)
        if not payload:
            return error_response("Invalid or expired token", 401)

        new_token = generate_token(
            payload["user_id"], payload["username"], payload["role"]
        )
        return success_response({"token": new_token}, "Token refreshed")
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        return error_response(str(e), 500)
