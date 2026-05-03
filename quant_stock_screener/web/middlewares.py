"""
Flask 中间件模块
"""

import time
import logging
from functools import wraps

from flask import request, jsonify

logger = logging.getLogger(__name__)


def register_middlewares(app):
    register_request_logger(app)
    register_cors_headers(app)


def register_request_logger(app):
    @app.before_request
    def before_request():
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        duration = time.time() - getattr(request, "start_time", time.time())
        logger.info(f"{request.method} {request.path} - {response.status_code} - {duration:.3f}s")
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        return response


def register_cors_headers(app):
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify({"code": 400, "message": "Bad Request", "error": str(error)}),
            400,
        )

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"code": 404, "message": "Not Found", "error": "Resource not found"}),
            404,
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        return (
            jsonify({"code": 405, "message": "Method Not Allowed"}),
            405,
        )

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal Server Error: {error}")
        return (
            jsonify({"code": 500, "message": "Internal Server Error"}),
            500,
        )

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.exception("Unhandled exception")
        return (
            jsonify({"code": 500, "message": "Internal Server Error", "error": str(error)}),
            500,
        )


def validate_request(schema_class):
    """请求数据验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from pydantic import ValidationError

            try:
                if request.method == "GET":
                    data = request.args.to_dict()
                    for key, value in data.items():
                        if value.isdigit():
                            data[key] = int(value)
                        elif value.replace(".", "").isdigit():
                            data[key] = float(value)
                else:
                    data = request.get_json() or {}

                validated = schema_class(**data)
                request.validated_data = validated
                return f(*args, **kwargs)
            except ValidationError as e:
                return jsonify({"code": 422, "message": "Validation Error", "errors": e.errors()}), 422

        return decorated_function
    return decorator


class APIException(Exception):
    def __init__(self, message, code=400, data=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data


def handle_api_exception(app):
    @app.errorhandler(APIException)
    def handle_exception(error):
        return (
            jsonify({"code": error.code, "message": error.message, "data": error.data}),
            error.code,
        )
