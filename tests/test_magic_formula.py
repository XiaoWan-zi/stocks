"""神奇公式选股策略测试用例"""
# pylint: disable=protected-access,attribute-defined-outside-init

import pytest
import pandas as pd
from src.magic_formula import MagicFormulaScreener


class TestMagicFormulaScreener:
    """神奇公式选股器测试类"""

    def setup_method(self):
        """初始化测试环境"""
        self.screener = MagicFormulaScreener()

    def test_init(self):
        """测试初始化"""
        assert self.screener.stocks_data is None
        assert self.screener.screened_stocks is None
        assert self.screener.script_dir is not None

    def test_calculate_magic_formula_metrics_no_data(self):
        """测试无数据时计算指标"""
        self.screener.stocks_data = None
        self.screener.calculate_magic_formula_metrics()
        # 方法返回 None，不赋值给变量

    def test_calculate_magic_formula_metrics_with_data(self):
        """测试有数据时计算指标"""
        self.screener.stocks_data = pd.DataFrame({
            '代码': ['000001'],
            '市盈率-动态': [15],
            '净资产收益率': [10]
        })
        self.screener.calculate_magic_formula_metrics()
        assert 'ROIC_proxy' in self.screener.stocks_data.columns
        assert 'earnings_yield' in self.screener.stocks_data.columns

    def test_apply_magic_formula_screening_no_data(self):
        """测试无数据时应用筛选"""
        self.screener.stocks_data = None
        self.screener.apply_magic_formula_screening()
        assert self.screener.screened_stocks is None

    def test_apply_magic_formula_screening_with_data(self):
        """测试有数据时应用筛选"""
        self.screener.stocks_data = pd.DataFrame({
            '代码': ['000001', '000002', '000003'],
            '名称': ['股票1', '股票2', '股票3'],
            '市盈率-动态': [15, 25, 10],
            '市净率': [1.2, 2.0, 0.8]
        })
        # 先计算指标
        self.screener.calculate_magic_formula_metrics()
        # 然后应用筛选
        self.screener.apply_magic_formula_screening()
        assert self.screener.screened_stocks is not None

    def test_save_results_no_data(self):
        """测试无筛选结果时保存"""
        self.screener.screened_stocks = None
        result = self.screener.save_results()
        assert result is None


class TestMagicFormulaMetrics:
    """测试神奇公式指标计算"""

    def setup_method(self):
        """初始化"""
        self.screener = MagicFormulaScreener()
        self.test_data = pd.DataFrame({
            '代码': ['000001'],
            '市盈率-动态': [20],
            '市净率': [1.5]
        })

    def test_roic_proxy_calculation(self):
        """测试ROIC代理指标计算"""
        self.screener.stocks_data = self.test_data.copy()
        self.screener.calculate_magic_formula_metrics()
        assert 'ROIC_proxy' in self.screener.stocks_data.columns

    def test_earnings_yield_calculation(self):
        """测试盈利收益率计算"""
        self.screener.stocks_data = self.test_data.copy()
        self.screener.calculate_magic_formula_metrics()
        assert 'earnings_yield' in self.screener.stocks_data.columns

    def test_magic_score_calculation(self):
        """测试神奇分数计算"""
        self.screener.stocks_data = pd.DataFrame({
            '代码': ['000001', '000002'],
            '名称': ['股票1', '股票2'],
            '市盈率-动态': [15, 25],
            '市净率': [1.2, 2.0]
        })
        self.screener.calculate_magic_formula_metrics()
        self.screener.apply_magic_formula_screening()
        if self.screener.screened_stocks is not None and not self.screener.screened_stocks.empty:
            assert 'magic_score' in self.screener.screened_stocks.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
