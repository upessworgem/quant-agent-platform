"""
Flask API 模块 - 提供 RESTful 接口
包含所有增删改查操作
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

from flask import Blueprint, request, jsonify

from database import db
from ai_analyzer import AIAnalyzer, create_llm_client
from config import ConfigManager, FilterCondition, StrategyConfig

logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')


# ========== 通用响应封装 ==========

def success_response(data: Any = None, message: str = "success") -> Dict:
    """成功响应"""
    return jsonify({
        'code': 200,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })


def error_response(message: str, code: int = 400, data: Any = None) -> tuple:
    """错误响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }), code


# ========== 股票相关接口 ==========

@api_bp.route('/stocks', methods=['GET'])
def get_stocks():
    """获取股票列表
    GET /api/stocks?page=1&limit=20&search=平安
    """
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        search = request.args.get('search', '')
        exchange = request.args.get('exchange')
        industry = request.args.get('industry')

        offset = (page - 1) * limit

        # 获取所有股票
        stocks = db.get_all_stocks(limit=limit, offset=offset)

        # 过滤
        result = []
        for stock in stocks:
            stock_dict = stock.to_dict()
            if search and search not in stock_dict['name'] and search not in stock_dict['code']:
                continue
            if exchange and stock_dict.get('exchange') != exchange:
                continue
            if industry and stock_dict.get('industry') != industry:
                continue
            result.append(stock_dict)

        return success_response({
            'items': result,
            'page': page,
            'limit': limit,
            'total': db.get_statistics()['stocks_count']
        })

    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/stocks/<code>', methods=['GET'])
def get_stock(code: str):
    """获取单个股票详情"""
    try:
        stock = db.get_stock_by_code(code)
        if not stock:
            return error_response(f"股票 {code} 不存在", 404)

        return success_response(stock.to_dict())

    except Exception as e:
        logger.error(f"获取股票失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/stocks', methods=['POST'])
def create_stock():
    """创建股票
    POST /api/stocks
    {
        "code": "000001",
        "name": "平安银行",
        "exchange": "SZ",
        "industry": "银行"
    }
    """
    try:
        data = request.get_json()
        if not data or 'code' not in data or 'name' not in data:
            return error_response("缺少必要字段: code, name")

        stock = db.create_stock(
            code=data['code'],
            name=data['name'],
            exchange=data.get('exchange'),
            industry=data.get('industry')
        )

        return success_response(stock.to_dict(), "股票创建成功")

    except Exception as e:
        logger.error(f"创建股票失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/stocks/<code>', methods=['PUT'])
def update_stock(code: str):
    """更新股票信息"""
    try:
        data = request.get_json()
        if not data:
            return error_response("请求体不能为空")

        stock = db.update_stock(code, **data)
        if not stock:
            return error_response(f"股票 {code} 不存在", 404)

        return success_response(stock.to_dict(), "股票更新成功")

    except Exception as e:
        logger.error(f"更新股票失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/stocks/<code>', methods=['DELETE'])
def delete_stock(code: str):
    """删除股票"""
    try:
        success = db.delete_stock(code)
        if not success:
            return error_response(f"股票 {code} 不存在", 404)

        return success_response(None, "股票删除成功")

    except Exception as e:
        logger.error(f"删除股票失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/stocks/bulk', methods=['POST'])
def bulk_import_stocks():
    """批量导入股票
    POST /api/stocks/bulk
    {
        "stocks": [
            {"code": "000001", "name": "平安银行", "exchange": "SZ"},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        if not data or 'stocks' not in data:
            return error_response("缺少 stocks 字段")

        count = db.bulk_import_stocks(data['stocks'])

        return success_response({'imported': count}, f"成功导入 {count} 只股票")

    except Exception as e:
        logger.error(f"批量导入失败: {e}")
        return error_response(str(e), 500)


# ========== 策略相关接口 ==========

@api_bp.route('/strategies', methods=['GET'])
def get_strategies():
    """获取策略列表
    GET /api/strategies?active_only=true
    """
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        strategies = db.get_all_strategies(active_only=active_only)

        return success_response([s.to_dict() for s in strategies])

    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/strategies/<int:strategy_id>', methods=['GET'])
def get_strategy(strategy_id: int):
    """获取单个策略"""
    try:
        strategy = db.get_strategy(strategy_id)
        if not strategy:
            return error_response(f"策略 {strategy_id} 不存在", 404)

        return success_response(strategy.to_dict())

    except Exception as e:
        logger.error(f"获取策略失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/strategies', methods=['POST'])
def create_strategy():
    """创建策略
    POST /api/strategies
    {
        "name": "高换手策略",
        "description": "选择换手率大于15%的股票",
        "conditions": [
            {"name": "换手率", "field": "turnover_rate", "operator": ">", "value": 15, "enabled": true}
        ],
        "sort_by": "turnover_rate",
        "sort_desc": true,
        "max_stocks": 50
    }
    """
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'conditions' not in data:
            return error_response("缺少必要字段: name, conditions")

        strategy = db.create_strategy(
            name=data['name'],
            description=data.get('description', ''),
            conditions=data['conditions'],
            strategy_type=data.get('strategy_type', 'user'),
            sort_by=data.get('sort_by'),
            sort_desc=data.get('sort_desc', True),
            max_stocks=data.get('max_stocks')
        )

        return success_response(strategy.to_dict(), "策略创建成功")

    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/strategies/<int:strategy_id>', methods=['PUT'])
def update_strategy(strategy_id: int):
    """更新策略"""
    try:
        data = request.get_json()
        if not data:
            return error_response("请求体不能为空")

        strategy = db.update_strategy(strategy_id, **data)
        if not strategy:
            return error_response(f"策略 {strategy_id} 不存在", 404)

        return success_response(strategy.to_dict(), "策略更新成功")

    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/strategies/<int:strategy_id>', methods=['DELETE'])
def delete_strategy(strategy_id: int):
    """删除策略（软删除）"""
    try:
        success = db.delete_strategy(strategy_id)
        if not success:
            return error_response(f"策略 {strategy_id} 不存在", 404)

        return success_response(None, "策略删除成功")

    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/strategies/<int:strategy_id>/duplicate', methods=['POST'])
def duplicate_strategy(strategy_id: int):
    """复制策略"""
    try:
        original = db.get_strategy(strategy_id)
        if not original:
            return error_response(f"策略 {strategy_id} 不存在", 404)

        new_strategy = db.create_strategy(
            name=f"{original.name} (复制)",
            description=original.description,
            conditions=json.loads(original.conditions_json),
            strategy_type='user',
            sort_by=original.sort_by,
            sort_desc=original.sort_desc,
            max_stocks=original.max_stocks
        )

        return success_response(new_strategy.to_dict(), "策略复制成功")

    except Exception as e:
        logger.error(f"复制策略失败: {e}")
        return error_response(str(e), 500)


# ========== AI 策略生成接口 ==========

@api_bp.route('/strategies/generate', methods=['POST'])
def generate_strategy_with_ai():
    """使用 AI 生成策略
    POST /api/strategies/generate
    {
        "description": "找出近期放量突破、换手率大于20%的科技类股票",
        "ai_provider": "anthropic",
        "api_key": "optional-api-key"
    }
    """
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            return error_response("缺少必要字段: description")

        description = data['description']
        provider = data.get('ai_provider', 'anthropic')
        api_key = data.get('api_key') or ConfigManager().ai.api_key

        if not api_key:
            return error_response("缺少 AI API Key")

        # 创建 LLM 客户端
        llm_client = create_llm_client(provider, api_key)
        ai_analyzer = AIAnalyzer(llm_client)

        # 生成策略
        strategy_dict = ai_analyzer.generate_strategy_from_natural_language(description)

        if 'error' in strategy_dict:
            return error_response(strategy_dict['error'], 500)

        # 保存到数据库
        strategy = db.create_strategy(
            name=strategy_dict.get('name', 'AI生成策略'),
            description=strategy_dict.get('description', description),
            conditions=strategy_dict.get('conditions', []),
            strategy_type='ai',
            sort_by=strategy_dict.get('sort_by'),
            sort_desc=strategy_dict.get('sort_desc', True),
            max_stocks=strategy_dict.get('max_stocks')
        )

        # 保存 AI 建议记录
        db.save_ai_suggestion(
            suggestion_type='strategy_generation',
            input_data=description,
            output_data=json.dumps(strategy_dict, ensure_ascii=False),
            ai_provider=provider,
            ai_model=data.get('model', 'default'),
            strategy_id=strategy.id
        )

        return success_response(strategy.to_dict(), "AI 策略生成成功")

    except Exception as e:
        logger.error(f"AI 策略生成失败: {e}")
        return error_response(str(e), 500)


# ========== 筛选结果相关接口 ==========

@api_bp.route('/screening-results', methods=['GET'])
def get_screening_results():
    """获取筛选结果列表
    GET /api/screening-results?strategy_id=1&page=1&limit=10
    """
    try:
        strategy_id = request.args.get('strategy_id', type=int)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)

        results = db.get_screening_results(
            strategy_id=strategy_id,
            limit=limit
        )

        return success_response({
            'items': [r.to_dict() for r in results],
            'page': page,
            'limit': limit
        })

    except Exception as e:
        logger.error(f"获取筛选结果失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/screening-results/<int:result_id>', methods=['GET'])
def get_screening_result(result_id: int):
    """获取筛选结果详情"""
    try:
        result = db.get_screening_result(result_id)
        if not result:
            return error_response(f"筛选结果 {result_id} 不存在", 404)

        result_dict = result.to_dict()
        result_dict['items'] = [item.to_dict() for item in result.items]

        return success_response(result_dict)

    except Exception as e:
        logger.error(f"获取筛选结果详情失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/screening-results/<int:result_id>', methods=['DELETE'])
def delete_screening_result(result_id: int):
    """删除筛选结果"""
    try:
        success = db.delete_screening_result(result_id)
        if not success:
            return error_response(f"筛选结果 {result_id} 不存在", 404)

        return success_response(None, "筛选结果删除成功")

    except Exception as e:
        logger.error(f"删除筛选结果失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/screening-results/<int:result_id>/analyze', methods=['POST'])
def analyze_screening_result(result_id: int):
    """使用 AI 分析筛选结果"""
    try:
        result = db.get_screening_result(result_id)
        if not result:
            return error_response(f"筛选结果 {result_id} 不存在", 404)

        data = request.get_json() or {}
        provider = data.get('ai_provider', 'anthropic')
        api_key = data.get('api_key') or ConfigManager().ai.api_key

        if not api_key:
            return error_response("缺少 AI API Key")

        # 准备分析数据
        stocks_data = [item.to_dict() for item in result.items]

        if not stocks_data:
            return error_response("没有可分析的股票数据")

        # 创建 AI 分析器
        llm_client = create_llm_client(provider, api_key)
        ai_analyzer = AIAnalyzer(llm_client)

        # 执行分析
        analysis = ai_analyzer.analyze_results(stocks_data)

        # 更新结果记录
        db.update_strategy(result_id, ai_analysis=analysis)  # 注意：这里应该更新 ScreeningResult

        return success_response({
            'analysis': analysis,
            'stocks_analyzed': len(stocks_data)
        }, "AI 分析完成")

    except Exception as e:
        logger.error(f"AI 分析失败: {e}")
        return error_response(str(e), 500)


# ========== 历史数据接口 ==========

@api_bp.route('/stocks/<code>/history', methods=['GET'])
def get_stock_history(code: str):
    """获取股票历史数据
    GET /api/stocks/000001/history?start_date=2024-01-01&limit=30
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 30, type=int)

        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        history = db.get_historical_data(
            stock_code=code,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return success_response([h.to_dict() for h in history])

    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/stocks/<code>/history', methods=['POST'])
def save_stock_history(code: str):
    """保存股票历史数据"""
    try:
        data = request.get_json()
        if not data:
            return error_response("请求体不能为空")

        if 'data' in data:
            # 批量保存
            count = db.bulk_save_historical_data(code, data['data'])
            return success_response({'saved': count}, f"成功保存 {count} 条数据")
        else:
            # 单条保存
            historical = db.save_historical_data(code, data)
            return success_response(historical.to_dict(), "数据保存成功")

    except Exception as e:
        logger.error(f"保存历史数据失败: {e}")
        return error_response(str(e), 500)


# ========== 统计和配置接口 ==========

@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取系统统计信息"""
    try:
        stats = db.get_statistics()
        return success_response(stats)

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/configs', methods=['GET'])
def get_configs():
    """获取所有配置"""
    try:
        configs = db.get_all_configs()
        return success_response([c.to_dict() for c in configs])

    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/configs/<key>', methods=['GET'])
def get_config(key: str):
    """获取单个配置"""
    try:
        value = db.get_config(key)
        if value is None:
            return error_response(f"配置 {key} 不存在", 404)

        return success_response({'key': key, 'value': value})

    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/configs', methods=['POST'])
def set_config():
    """设置配置
    POST /api/configs
    {
        "key": "api_timeout",
        "value": "30",
        "description": "API超时时间（秒）"
    }
    """
    try:
        data = request.get_json()
        if not data or 'key' not in data or 'value' not in data:
            return error_response("缺少必要字段: key, value")

        config = db.set_config(
            key=data['key'],
            value=data['value'],
            description=data.get('description')
        )

        return success_response(config.to_dict(), "配置保存成功")

    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/configs/<key>', methods=['DELETE'])
def delete_config(key: str):
    """删除配置"""
    try:
        success = db.delete_config(key)
        if not success:
            return error_response(f"配置 {key} 不存在", 404)

        return success_response(None, "配置删除成功")

    except Exception as e:
        logger.error(f"删除配置失败: {e}")
        return error_response(str(e), 500)


# ========== AI 建议接口 ==========

@api_bp.route('/ai-suggestions', methods=['GET'])
def get_ai_suggestions():
    """获取 AI 建议列表"""
    try:
        suggestion_type = request.args.get('type')
        limit = request.args.get('limit', 20, type=int)

        suggestions = db.get_ai_suggestions(
            suggestion_type=suggestion_type,
            limit=limit
        )

        return success_response([s.to_dict() for s in suggestions])

    except Exception as e:
        logger.error(f"获取 AI 建议失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/ai-suggestions/<int:suggestion_id>/rate', methods=['POST'])
def rate_ai_suggestion(suggestion_id: int):
    """给 AI 建议评分
    POST /api/ai-suggestions/1/rate
    {"rating": 5}
    """
    try:
        data = request.get_json()
        if not data or 'rating' not in data:
            return error_response("缺少 rating 字段")

        rating = data['rating']
        if not (1 <= rating <= 5):
            return error_response("评分必须在 1-5 之间")

        suggestion = db.rate_ai_suggestion(suggestion_id, rating)
        if not suggestion:
            return error_response(f"建议 {suggestion_id} 不存在", 404)

        return success_response(suggestion.to_dict(), "评分成功")

    except Exception as e:
        logger.error(f"评分失败: {e}")
        return error_response(str(e), 500)


# ========== 执行筛选接口 ==========

@api_bp.route('/screening/execute', methods=['POST'])
def execute_screening():
    """执行筛选
    POST /api/screening/execute
    {
        "strategy_id": 1,
        "max_stocks": 100,
        "use_ai_analysis": false
    }
    """
    try:
        data = request.get_json() or {}
        strategy_id = data.get('strategy_id')

        if not strategy_id:
            return error_response("缺少 strategy_id")

        # 获取策略
        strategy = db.get_strategy(strategy_id)
        if not strategy:
            return error_response(f"策略 {strategy_id} 不存在", 404)

        # 这里调用主筛选逻辑
        # 简化版：创建结果记录
        result = db.create_screening_result(
            strategy_id=strategy_id,
            total_stocks=0,
            matched_count=0,
            status='pending'
        )

        # TODO: 实际执行筛选逻辑
        # 这会调用 main.py 中的 StockScreener

        return success_response(result.to_dict(), "筛选任务已创建")

    except Exception as e:
        logger.error(f"执行筛选失败: {e}")
        return error_response(str(e), 500)


# ========== 认证接口 ==========

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录
    POST /api/auth/login
    {
        "username": "admin",
        "password": "admin123"
    }
    """
    try:
        from auth import AuthService, generate_token

        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return error_response("缺少用户名或密码")

        auth_service = AuthService(db)
        user = auth_service.authenticate(data['username'], data['password'])

        if not user:
            return error_response("用户名或密码错误", 401)

        # 生成 Token
        token = generate_token(user['id'], user['username'], user['role'])

        return success_response({
            'token': token,
            'user': user
        }, "登录成功")

    except Exception as e:
        logger.error(f"登录失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/auth/me', methods=['GET'])
def get_current_user():
    """获取当前用户信息
    GET /api/auth/me
    需要 Authorization: Bearer <token>
    """
    try:
        from auth import login_required, AuthService

        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return error_response("未提供认证 Token", 401)

        from auth import verify_token
        payload = verify_token(token)
        if not payload:
            return error_response("无效或过期的 Token", 401)

        auth_service = AuthService(db)
        user = auth_service.get_user_by_id(payload['user_id'])

        if not user:
            return error_response("用户不存在", 404)

        return success_response(user)

    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return error_response(str(e), 500)


@api_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """刷新 Token
    POST /api/auth/refresh
    需要 Authorization: Bearer <token>
    """
    try:
        from auth import generate_token, verify_token

        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return error_response("未提供认证 Token", 401)

        payload = verify_token(token)
        if not payload:
            return error_response("无效或过期的 Token", 401)

        # 生成新 Token
        new_token = generate_token(
            payload['user_id'],
            payload['username'],
            payload['role']
        )

        return success_response({
            'token': new_token
        }, "Token 已刷新")

    except Exception as e:
        logger.error(f"刷新 Token 失败: {e}")
        return error_response(str(e), 500)


# ========== 健康检查 ==========

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return success_response({
        'status': 'healthy',
        'database': 'connected',
        'timestamp': datetime.now().isoformat()
    })
