"""
API 通用辅助函数
"""

from datetime import datetime
from typing import Any

from flask import jsonify


def success_response(data: Any = None, message: str = "success"):
    return jsonify(
        {
            "code": 200,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
    )


def error_response(message: str, code: int = 400, data: Any = None) -> tuple:
    return (
        jsonify(
            {
                "code": code,
                "message": message,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
        ),
        code,
    )
