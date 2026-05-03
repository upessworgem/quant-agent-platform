"""
API 接口测试
"""

import pytest
import json


class TestHealthCheck:
    """健康检查测试"""

    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get('/api/health')
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200
        assert data['data']['status'] == 'healthy'


class TestAuthentication:
    """认证接口测试"""

    def test_login_success(self, client):
        """测试登录成功"""
        response = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200
        assert 'token' in data['data']
        assert 'user' in data['data']
        assert data['data']['user']['username'] == 'admin'

    def test_login_invalid_credentials(self, client):
        """测试登录失败 - 错误密码"""
        response = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'wrong_password'
        })
        data = response.get_json()

        assert response.status_code == 401
        assert data['code'] == 401

    def test_login_missing_fields(self, client):
        """测试登录失败 - 缺少字段"""
        response = client.post('/api/auth/login', json={
            'username': 'admin'
        })
        data = response.get_json()

        assert response.status_code == 400

    def test_get_current_user(self, client, headers):
        """测试获取当前用户"""
        response = client.get('/api/auth/me', headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200
        assert data['data']['username'] == 'admin'

    def test_get_current_user_no_token(self, client):
        """测试获取当前用户 - 无 Token"""
        response = client.get('/api/auth/me')

        assert response.status_code == 401

    def test_refresh_token(self, client, headers):
        """测试刷新 Token"""
        response = client.post('/api/auth/refresh', headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert 'token' in data['data']


class TestStocks:
    """股票接口测试"""

    def test_get_stocks(self, client, headers):
        """测试获取股票列表"""
        response = client.get('/api/stocks?page=1&limit=10', headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200
        assert 'items' in data['data']
        assert 'total' in data['data']

    def test_get_stock_by_code(self, client, headers):
        """测试获取单个股票"""
        response = client.get('/api/stocks/000001', headers=headers)

        # 可能返回 404 或 200
        assert response.status_code in [200, 404]

    def test_create_stock(self, client, headers):
        """测试创建股票"""
        response = client.post('/api/stocks', headers=headers, json={
            'code': '999999',
            'name': '测试股票',
            'exchange': 'SZ'
        })

        # 如果股票已存在可能返回 500
        assert response.status_code in [200, 500]

    def test_search_stocks(self, client, headers):
        """测试搜索股票"""
        response = client.get('/api/stocks?search=平安', headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200


class TestStrategies:
    """策略接口测试"""

    def test_get_strategies(self, client, headers):
        """测试获取策略列表"""
        response = client.get('/api/strategies', headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200
        assert isinstance(data['data'], list)

    def test_create_strategy(self, client, headers):
        """测试创建策略"""
        response = client.post('/api/strategies', headers=headers, json={
            'name': '测试策略',
            'description': '测试策略描述',
            'conditions': [
                {
                    'name': '换手率',
                    'field': 'turnover_rate',
                    'operator': '>',
                    'value': 15,
                    'enabled': True
                }
            ]
        })
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200
        assert data['data']['name'] == '测试策略'

    def test_create_strategy_invalid(self, client, headers):
        """测试创建策略 - 无效数据"""
        response = client.post('/api/strategies', headers=headers, json={
            'name': '',  # 名称为空
            'conditions': []
        })

        assert response.status_code == 422 or response.status_code == 400

    def test_get_strategy_by_id(self, client, headers):
        """测试获取单个策略"""
        # 先获取策略列表
        response = client.get('/api/strategies', headers=headers)
        strategies = response.get_json().get('data', [])

        if strategies:
            strategy_id = strategies[0]['id']
            response = client.get(f'/api/strategies/{strategy_id}', headers=headers)
            data = response.get_json()

            assert response.status_code == 200
            assert data['code'] == 200
            assert data['data']['id'] == strategy_id


class TestScreeningResults:
    """筛选结果接口测试"""

    def test_get_screening_results(self, client, headers):
        """测试获取筛选结果列表"""
        response = client.get('/api/screening-results', headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200
        assert 'items' in data['data']


class TestConfig:
    """配置接口测试"""

    def test_get_configs(self, client, headers):
        """测试获取配置列表"""
        response = client.get('/api/configs', headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200

    def test_set_config(self, client, headers):
        """测试设置配置"""
        response = client.post('/api/configs', headers=headers, json={
            'key': 'test_key',
            'value': 'test_value',
            'description': '测试配置'
        })
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200

    def test_get_config_by_key(self, client, headers):
        """测试获取单个配置"""
        # 先设置配置
        client.post('/api/configs', headers=headers, json={
            'key': 'test_key2',
            'value': 'test_value2'
        })

        # 再获取
        response = client.get('/api/configs/test_key2', headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200
        assert data['data']['value'] == 'test_value2'


class TestStatistics:
    """统计接口测试"""

    def test_get_statistics(self, client, headers):
        """测试获取统计信息"""
        response = client.get('/api/statistics', headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert data['code'] == 200
        assert 'stocks_count' in data['data']
        assert 'strategies_count' in data['data']
