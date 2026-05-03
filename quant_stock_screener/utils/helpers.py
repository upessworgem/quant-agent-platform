"""
通用辅助函数
"""

from datetime import datetime
from typing import Any, Dict, Optional

from flask import jsonify


def success_response(data: Any = None, message: str = "success") -> Dict:
    """标准成功响应"""
    return jsonify(
        {
            "code": 200,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
    )


def error_response(message: str, code: int = 400, data: Any = None) -> tuple:
    """标准错误响应"""
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


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """格式化日期时间"""
    return dt.isoformat() if dt else None
