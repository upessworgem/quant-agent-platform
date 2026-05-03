"""
JWT 认证模块
"""

import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

from flask import request, jsonify
import jwt

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def generate_token(user_id: int, username: str, role: str = "user") -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def get_token_from_header() -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return jsonify({"code": 401, "message": "Missing authentication token"}), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({"code": 401, "message": "Invalid or expired token"}), 401

        request.current_user = payload
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, "current_user"):
            return jsonify({"code": 401, "message": "Authentication required"}), 401

        if request.current_user.get("role") != "admin":
            return jsonify({"code": 403, "message": "Admin permission required"}), 403

        return f(*args, **kwargs)

    return decorated


def role_required(allowed_roles: list):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, "current_user"):
                return jsonify({"code": 401, "message": "Authentication required"}), 401

            user_role = request.current_user.get("role")
            if user_role not in allowed_roles:
                return (
                    jsonify(
                        {
                            "code": 403,
                            "message": f"Role {user_role} not in allowed roles: {allowed_roles}",
                        }
                    ),
                    403,
                )

            return f(*args, **kwargs)

        return decorated

    return decorator


class AuthService:
    """认证服务"""

    def __init__(self, db):
        self.db = db

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        users = {
            "admin": {"id": 1, "username": "admin", "password": "admin123", "role": "admin"},
            "user": {"id": 2, "username": "user", "password": "user123", "role": "user"},
        }

        user = users.get(username)
        if user and user["password"] == password:
            return {"id": user["id"], "username": user["username"], "role": user["role"]}
        return None

    def create_user(self, username: str, password: str, role: str = "user") -> Optional[dict]:
        return {"id": 3, "username": username, "role": role}

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        if user_id == 1:
            return {"id": 1, "username": "admin", "role": "admin"}
        elif user_id == 2:
            return {"id": 2, "username": "user", "role": "user"}
        return None
