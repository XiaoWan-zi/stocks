"""施洛斯选股策略测试用例"""
# pylint: disable=protected-access,attribute-defined-outside-init

import os
from unittest.mock import patch

import pandas as pd
import pytest

from src.walter_schloss import SchlossStockScreening


class TestSchlossStockScreening:
    """施洛斯选股策略测试类"""

    def setup_method(self):
        """初始化测试环境"""
        self.screener = SchlossStockScreening()

    def test_init(self):
        """测试初始化"""
        assert self.screener.stocks_data is None
        assert self.screener.screened_stocks is None
        assert self.screener.script_dir is not None
        assert "stock_data_all_by_ws.csv" in self.screener.data_path

    def test_get_merge_key_success(self):
        """测试成功获取合并键"""
        financial_data = pd.DataFrame({'代码': ['000001', '000002']})
        stock_list = pd.DataFrame({'代码': ['000001', '000002']})
        key = self.screener._get_merge_key(financial_data, stock_list)
        assert key == '代码'

    def test_get_merge_key_no_match(self):
        """测试无法找到匹配键"""
        financial_data = pd.DataFrame({'stock': ['000001']})
        stock_list = pd.DataFrame({'code': ['000001']})
        key = self.screener._get_merge_key(financial_data, stock_list)
        assert key is None

    def test_map_financial_columns(self):
        """测试财务数据列名映射"""
        df = pd.DataFrame({
            '资产负债率(%)': [50],
            '净利润增长率(%)': [10]
        })
        result = self.screener._map_financial_columns(df)
        assert '资产负债率' in result.columns
        assert '净利润同比增长率' in result.columns

    def test_apply_schloss_strategy_no_data(self):
        """测试无数据时应用策略"""
        self.screener.stocks_data = None
        self.screener.apply_schloss_strategy()
        assert self.screener.screened_stocks is None

    @patch('src.walter_schloss.os.path.exists')
    def test_get_stock_data_with_cached_file(self, mock_exists):
        """测试从缓存文件读取数据"""
        mock_exists.return_value = True
        mock_data = pd.DataFrame({
            '代码': ['000001'],
            '名称': ['测试股票'],
            '市盈率-动态': [15],
            '市净率': [1.2]
        })

        with patch('src.walter_schloss.pd.read_csv') as mock_read:
            mock_read.return_value = mock_data
            with patch('src.walter_schloss.os.path.getmtime') as mock_time:
                mock_time.return_value = os.path.getmtime('src/walter_schloss.py')
                self.screener.get_stock_data()


class TestSchlossStrategyFilters:
    """测试施洛斯策略的筛选条件"""

    def setup_method(self):
        """初始化测试数据"""
        self.screener = SchlossStockScreening()
        self.mock_data = pd.DataFrame({
            '代码': ['000001', '000002', '000003'],
            '名称': ['股票1', '股票2', '股票3'],
            '市盈率-动态': [15, 25, 10],
            '市净率': [1.2, 2.0, 0.8],
            '资产负债率': [40, 60, 30],
            '净利润同比增长率': [10, -5, 20],
            '总市值': [10000000000, 5000000000, 20000000000]
        })

    def test_apply_schloss_strategy_with_valid_data(self):
        """测试使用有效数据应用策略"""
        self.screener.stocks_data = self.mock_data
        self.screener.apply_schloss_strategy()
        assert self.screener.screened_stocks is not None

    def test_save_results_no_data(self):
        """测试无筛选结果时保存"""
        self.screener.screened_stocks = None
        result = self.screener.save_results_to_table()
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
