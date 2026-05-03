"""
中间件模块 - 错误处理、请求日志、认证等
"""

import time
import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


def register_middlewares(app):
    """注册所有中间件"""
    register_request_logger(app)
    register_error_handlers(app)
    register_cors_headers(app)


def register_request_logger(app):
    """注册请求日志中间件"""

    @app.before_request
    def before_request():
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        # 计算请求耗时
        duration = time.time() - getattr(request, 'start_time', time.time())

        # 记录日志
        logger.info(
            f"{request.method} {request.path} - {response.status_code} - {duration:.3f}s"
        )

        # 添加响应头
        response.headers['X-Response-Time'] = f"{duration:.3f}s"

        return response


def register_error_handlers(app):
    """注册错误处理器"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'code': 400,
            'message': 'Bad Request',
            'error': str(error.description if hasattr(error, 'description') else error),
            'timestamp': time.time()
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 404,
            'message': 'Not Found',
            'error': '请求的资源不存在',
            'timestamp': time.time()
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'code': 405,
            'message': 'Method Not Allowed',
            'error': '请求方法不被允许',
            'timestamp': time.time()
        }), 405

    @app.errorhandler(422)
    def validation_error(error):
        """Pydantic 验证错误"""
        return jsonify({
            'code': 422,
            'message': 'Validation Error',
            'error': str(error),
            'timestamp': time.time()
        }), 422

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal Server Error: {error}")
        return jsonify({
            'code': 500,
            'message': 'Internal Server Error',
            'error': '服务器内部错误',
            'timestamp': time.time()
        }), 500

    # 捕获所有未处理的异常
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.exception("Unhandled exception")
        return jsonify({
            'code': 500,
            'message': 'Internal Server Error',
            'error': str(error),
            'timestamp': time.time()
        }), 500


def register_cors_headers(app):
    """注册 CORS 响应头"""

    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response


def validate_request(schema_class):
    """请求数据验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            from pydantic import ValidationError

            try:
                # 根据请求方法获取数据
                if request.method == 'GET':
                    data = request.args.to_dict()
                    # 转换类型
                    for key, value in data.items():
                        if value.isdigit():
                            data[key] = int(value)
                        elif value.replace('.', '').isdigit():
                            data[key] = float(value)
                else:
                    data = request.get_json() or {}

                # 验证数据
                validated = schema_class(**data)
                # 将验证后的数据存储在 request 中
                request.validated_data = validated

                return f(*args, **kwargs)

            except ValidationError as e:
                return jsonify({
                    'code': 422,
                    'message': 'Validation Error',
                    'errors': e.errors()
                }), 422

        return decorated_function
    return decorator


class APIException(Exception):
    """API 异常基类"""
    def __init__(self, message, code=400, data=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data


def handle_api_exception(app):
    """处理 API 异常"""

    @app.errorhandler(APIException)
    def handle_exception(error):
        return jsonify({
            'code': error.code,
            'message': error.message,
            'data': error.data,
            'timestamp': time.time()
        }), error.code
