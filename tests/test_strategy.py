"""
策略模块测试
"""

import pytest
from strategy import StrategyExecutor, StrategyBuilder
from config import ConfigManager, StrategyConfig, FilterCondition


class TestStrategyBuilder:
    """策略构建器测试"""

    def test_create_momentum_strategy(self):
        """测试创建动量策略"""
        strategy = StrategyBuilder.create_momentum_strategy(
            min_turnover=15,
            min_volume_ratio=1.5,
            max_chip_concentration=20
        )

        assert strategy.name == 'momentum'
        assert len(strategy.conditions) == 4
        assert strategy.conditions[0].field == 'turnover_rate'
        assert strategy.conditions[0].value == 15

    def test_create_value_strategy(self):
        """测试创建价值策略"""
        strategy = StrategyBuilder.create_value_strategy(
            max_pe=20,
            min_roe=10
        )

        assert strategy.name == 'value'
        assert len(strategy.conditions) == 2

    def test_create_breakout_strategy(self):
        """测试创建突破策略"""
        strategy = StrategyBuilder.create_breakout_strategy(
            min_volume_surge=2.0,
            min_price_change=5
        )

        assert strategy.name == 'breakout'
        assert len(strategy.conditions) == 2


class TestStrategyExecutor:
    """策略执行器测试"""

    @pytest.fixture
    def executor(self):
        return StrategyExecutor(ConfigManager())

    @pytest.fixture
    def sample_data(self):
        return {
            'code': '000001',
            'name': '平安银行',
            'price': 12.5,
            'turnover_rate': 18.5,
            'volume_ratio': 2.0,
            'chip_concentration': 15.0,
            'consecutive_up': 1,
            'pe_ratio': 8.5,
            'pb_ratio': 0.8
        }

    def test_evaluate_condition_gt(self, executor, sample_data):
        """测试条件评估 - 大于"""
        condition = FilterCondition(
            name='换手率',
            field='turnover_rate',
            operator='>',
            value=15,
            enabled=True
        )
        assert executor.evaluate_condition(condition, sample_data) is True

    def test_evaluate_condition_lt(self, executor, sample_data):
        """测试条件评估 - 小于"""
        condition = FilterCondition(
            name='筹码集中度',
            field='chip_concentration',
            operator='<',
            value=20,
            enabled=True
        )
        assert executor.evaluate_condition(condition, sample_data) is True

    def test_evaluate_condition_eq(self, executor, sample_data):
        """测试条件评估 - 等于"""
        condition = FilterCondition(
            name='连续上涨',
            field='consecutive_up',
            operator='==',
            value=1,
            enabled=True
        )
        assert executor.evaluate_condition(condition, sample_data) is True

    def test_evaluate_condition_fail(self, executor, sample_data):
        """测试条件评估 - 失败"""
        condition = FilterCondition(
            name='换手率',
            field='turnover_rate',
            operator='<',
            value=10,
            enabled=True
        )
        assert executor.evaluate_condition(condition, sample_data) is False

    def test_evaluate_condition_disabled(self, executor, sample_data):
        """测试条件评估 - 禁用"""
        condition = FilterCondition(
            name='换手率',
            field='turnover_rate',
            operator='>',
            value=999,
            enabled=False
        )
        assert executor.evaluate_condition(condition, sample_data) is True

    def test_evaluate_condition_missing_field(self, executor, sample_data):
        """测试条件评估 - 字段缺失"""
        condition = FilterCondition(
            name='不存在的字段',
            field='non_existent',
            operator='>',
            value=0,
            enabled=True
        )
        assert executor.evaluate_condition(condition, sample_data) is False

    def test_evaluate_strategy(self, executor, sample_data):
        """测试策略评估"""
        strategy = StrategyBuilder.create_momentum_strategy(
            min_turnover=15,
            min_volume_ratio=1.5,
            max_chip_concentration=20
        )
        assert executor.evaluate_strategy(strategy, sample_data) is True

    def test_evaluate_strategy_fail(self, executor, sample_data):
        """测试策略评估 - 失败"""
        strategy = StrategyBuilder.create_momentum_strategy(
            min_turnover=50,  # 很高的条件
            min_volume_ratio=1.5,
            max_chip_concentration=20
        )
        assert executor.evaluate_strategy(strategy, sample_data) is False

    def test_filter_stocks(self, executor):
        """测试批量筛选"""
        strategy = StrategyBuilder.create_momentum_strategy(
            min_turnover=15,
            min_volume_ratio=1.5,
            max_chip_concentration=20
        )

        stocks = [
            {
                'code': '000001',
                'name': '股票A',
                'turnover_rate': 18,
                'volume_ratio': 2.0,
                'chip_concentration': 15,
                'consecutive_up': 1
            },
            {
                'code': '000002',
                'name': '股票B',
                'turnover_rate': 5,  # 不满足
                'volume_ratio': 2.0,
                'chip_concentration': 15,
                'consecutive_up': 1
            },
            {
                'code': '000003',
                'name': '股票C',
                'turnover_rate': 20,
                'volume_ratio': 1.8,
                'chip_concentration': 12,
                'consecutive_up': 1
            }
        ]

        results = executor.filter_stocks(strategy, stocks)
        assert len(results) == 2
        assert results[0]['code'] == '000001'
        assert results[1]['code'] == '000003'


class TestStrategyComparison:
    """策略操作符测试"""

    def test_gt_operator(self):
        """测试 > 操作符"""
        config = ConfigManager()
        executor = StrategyExecutor(config)
        condition = FilterCondition('test', 'field', '>', 10)
        assert executor.evaluate_condition(condition, {'field': 11}) is True
        assert executor.evaluate_condition(condition, {'field': 10}) is False

    def test_lt_operator(self):
        """测试 < 操作符"""
        config = ConfigManager()
        executor = StrategyExecutor(config)
        condition = FilterCondition('test', 'field', '<', 10)
        assert executor.evaluate_condition(condition, {'field': 9}) is True
        assert executor.evaluate_condition(condition, {'field': 10}) is False

    def test_gte_operator(self):
        """测试 >= 操作符"""
        config = ConfigManager()
        executor = StrategyExecutor(config)
        condition = FilterCondition('test', 'field', '>=', 10)
        assert executor.evaluate_condition(condition, {'field': 10}) is True
        assert executor.evaluate_condition(condition, {'field': 11}) is True
        assert executor.evaluate_condition(condition, {'field': 9}) is False

    def test_lte_operator(self):
        """测试 <= 操作符"""
        config = ConfigManager()
        executor = StrategyExecutor(config)
        condition = FilterCondition('test', 'field', '<=', 10)
        assert executor.evaluate_condition(condition, {'field': 10}) is True
        assert executor.evaluate_condition(condition, {'field': 9}) is True
        assert executor.evaluate_condition(condition, {'field': 11}) is False

    def test_eq_operator(self):
        """测试 == 操作符"""
        config = ConfigManager()
        executor = StrategyExecutor(config)
        condition = FilterCondition('test', 'field', '==', 10)
        assert executor.evaluate_condition(condition, {'field': 10}) is True
        assert executor.evaluate_condition(condition, {'field': 9}) is False

    def test_between_operator(self):
        """测试 between 操作符"""
        config = ConfigManager()
        executor = StrategyExecutor(config)
        condition = FilterCondition('test', 'field', 'between', 10, 20)
        assert executor.evaluate_condition(condition, {'field': 15}) is True
        assert executor.evaluate_condition(condition, {'field': 10}) is True
        assert executor.evaluate_condition(condition, {'field': 20}) is True
        assert executor.evaluate_condition(condition, {'field': 9}) is False
        assert executor.evaluate_condition(condition, {'field': 21}) is False
