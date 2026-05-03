"""
测试配置文件
"""

import os
import sys
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import Database


@pytest.fixture(scope='session')
def app():
    """创建测试用 Flask 应用"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///test.db'

    app = create_app('testing')
    return app


@pytest.fixture(scope='session')
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture(scope='session')
def db(app):
    """创建测试数据库"""
    with app.app_context():
        database = Database('sqlite:///test.db')
        yield database
        # 清理测试数据库
        os.remove('test.db') if os.path.exists('test.db') else None


@pytest.fixture
def auth_token(client):
    """获取认证 Token"""
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    data = response.get_json()
    return data.get('data', {}).get('token')


@pytest.fixture
def headers(auth_token):
    """带认证的请求头"""
    return {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }
