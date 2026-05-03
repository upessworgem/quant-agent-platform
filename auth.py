"""
认证模块 - JWT 认证和授权
"""

import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

from flask import request, jsonify
import jwt

logger = logging.getLogger(__name__)

# JWT 配置
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def generate_token(user_id: int, username: str, role: str = 'user') -> str:
    """
    生成 JWT Token

    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色

    Returns:
        JWT Token 字符串
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """
    验证 JWT Token

    Args:
        token: JWT Token 字符串

    Returns:
        解码后的 payload 或 None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token 已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"无效的 Token: {e}")
        return None


def get_token_from_header() -> Optional[str]:
    """从请求头获取 Token"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None


def login_required(f):
    """
    登录验证装饰器

    使用方法:
    @app.route('/api/protected')
    @login_required
    def protected_route():
        return jsonify({'message': 'Access granted'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()

        if not token:
            return jsonify({
                'code': 401,
                'message': 'Missing authentication token'
            }), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({
                'code': 401,
                'message': 'Invalid or expired token'
            }), 401

        # 将用户信息存储到 request 中
        request.current_user = payload

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """
    管理员权限装饰器

    使用方法:
    @app.route('/api/admin')
    @login_required
    @admin_required
    def admin_route():
        return jsonify({'message': 'Admin access'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({
                'code': 401,
                'message': 'Authentication required'
            }), 401

        if request.current_user.get('role') != 'admin':
            return jsonify({
                'code': 403,
                'message': 'Admin permission required'
            }), 403

        return f(*args, **kwargs)

    return decorated


def role_required(allowed_roles: list):
    """
    角色权限装饰器

    Args:
        allowed_roles: 允许的角色列表

    使用方法:
    @app.route('/api/editor')
    @login_required
    @role_required(['admin', 'editor'])
    def editor_route():
        return jsonify({'message': 'Editor access'})
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({
                    'code': 401,
                    'message': 'Authentication required'
                }), 401

            user_role = request.current_user.get('role')
            if user_role not in allowed_roles:
                return jsonify({
                    'code': 403,
                    'message': f'Role {user_role} not in allowed roles: {allowed_roles}'
                }), 403

            return f(*args, **kwargs)

        return decorated
    return decorator


class AuthService:
    """认证服务类"""

    def __init__(self, db):
        self.db = db

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """
        验证用户凭据

        Args:
            username: 用户名
            password: 密码

        Returns:
            用户信息字典或 None
        """
        # 这里应该查询数据库验证用户
        # 简化示例：使用硬编码用户
        users = {
            'admin': {
                'id': 1,
                'username': 'admin',
                'password': 'admin123',  # 实际应用中应该使用哈希密码
                'role': 'admin'
            },
            'user': {
                'id': 2,
                'username': 'user',
                'password': 'user123',
                'role': 'user'
            }
        }

        user = users.get(username)
        if user and user['password'] == password:
            return {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        return None

    def create_user(self, username: str, password: str, role: str = 'user') -> Optional[dict]:
        """
        创建新用户

        Args:
            username: 用户名
            password: 密码
            role: 角色

        Returns:
            创建的用户信息
        """
        # 这里应该插入数据库
        # 简化示例
        return {
            'id': 3,
            'username': username,
            'role': role
        }

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """根据 ID 获取用户"""
        # 这里应该查询数据库
        # 简化示例
        if user_id == 1:
            return {'id': 1, 'username': 'admin', 'role': 'admin'}
        elif user_id == 2:
            return {'id': 2, 'username': 'user', 'role': 'user'}
        return None
