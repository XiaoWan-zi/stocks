"""Joel Greenblatt 神奇公式选股策略。
# pylint: disable=trailing-whitespace,line-too-long,import-outside-toplevel

神奇公式通过两个指标筛选股票：
1. 投资回报率（ROIC）= 息税前利润 / (净营运资本 + 固定资产)
2. 盈利收益率（Earnings Yield）= 息税前利润 / 企业价值

策略思路：选择高 ROIC 和高盈利收益率的股票，即"好公司+好价格"。
"""

import os
import warnings
from datetime import datetime
from typing import Optional

import pandas as pd  # pylint: disable=import-error
import akshare as ak  # pylint: disable=import-error

warnings.filterwarnings('ignore')


class MagicFormulaScreener:
    """神奇公式选股器。"""

    def __init__(self):
        """初始化选股器。"""
        self.stocks_data: Optional[pd.DataFrame] = None
        self.screened_stocks: Optional[pd.DataFrame] = None
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(self.script_dir, '..', 'magic_formula_data.csv')
        self.result_path = os.path.join(self.script_dir, '..', 'magic_formula_results.csv')

    def get_stock_data(self) -> None:
        """获取A股股票数据。"""
        print("正在获取A股股票数据...")

        # 检查本地缓存
        if os.path.exists(self.data_path):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(self.data_path))
            file_date = file_mtime.strftime('%Y-%m-%d')
            today = datetime.now().strftime('%Y-%m-%d')

            if file_date == today:
                print("读取本地缓存数据...")
                self.stocks_data = pd.read_csv(self.data_path)
                print(f"成功读取{len(self.stocks_data)}只股票数据")
                return

        stock_list = ak.stock_zh_a_spot_em()

        # 过滤ST股票和退市股票
        stock_list = stock_list[~stock_list['名称'].str.contains('ST|退', na=False)]

        # 过滤市值过小的股票（流动性要求）
        stock_list = stock_list[stock_list['总市值'] > 5000000000]  # 50亿以上

        # 获取财务数据
        financial_data = self._get_financial_data(stock_list)

        if financial_data is None:
            print("未能获取到财务数据，将使用基础股票信息")
            self.stocks_data = stock_list[
                ['代码', '名称', '最新价', '涨跌幅', '总市值', '流通市值', '市盈率-动态', '市净率']
            ]
        else:
            # 合并数据
            self.stocks_data = pd.merge(
                stock_list,
                financial_data,
                on='代码',
                how='inner'
            )

        # 保存到本地
        self.stocks_data.to_csv(self.data_path, index=False)
        print(f"成功获取{len(self.stocks_data)}只股票数据并保存到本地")

    def _get_financial_data(self, stock_list: pd.DataFrame) -> Optional[pd.DataFrame]:
        """获取财务数据。"""
        print("正在获取财务数据...")
        financial_data = pd.DataFrame()
        stock_codes = stock_list['代码'].tolist()

        # 限制处理数量，避免请求过多
        stock_codes = stock_codes[:100]  # 只处理前100只股票作为示例

        for i, code in enumerate(stock_codes):
            try:
                # 获取财务指标
                financial = ak.stock_financial_analysis_indicator(
                    symbol=code, start_year="2024"
                )

                if not financial.empty:
                    # 只保留最新一期数据
                    latest_data = financial.iloc[[-1]].copy()
                    latest_data['代码'] = code
                    financial_data = pd.concat([financial_data, latest_data])

                print(f"已处理 {i + 1}/{len(stock_codes)} 只股票")

            except (KeyError, ValueError, RuntimeError) as err:  # noqa: PERF203
                # 根据实际 akshare 可能抛出的异常类型调整
                print(f"获取股票 {code} 财务数据时出错: {err}")
                continue

        if financial_data.empty:
            print("未能获取到财务数据")
            return None

        print(f"成功获取{len(financial_data)}只股票的财务数据")
        return financial_data

    def calculate_magic_formula_metrics(self) -> None:
        """计算神奇公式指标。"""
        if self.stocks_data is None:
            print("请先获取股票数据")
            return

        print("正在计算神奇公式指标...")

        # 简化的神奇公式计算
        # 由于数据限制，使用替代指标

        # 1. 投资回报率（ROIC）的替代：ROE
        if '净资产收益率' in self.stocks_data.columns:
            self.stocks_data['ROIC_proxy'] = self.stocks_data['净资产收益率']
        else:
            # 使用市盈率倒数作为盈利能力的替代
            self.stocks_data['ROIC_proxy'] = 1 / self.stocks_data['市盈率-动态'].replace(
                [0, float('inf')], 0
            )

        # 2. 盈利收益率（Earnings Yield）的替代：市盈率倒数
        self.stocks_data['earnings_yield'] = 1 / self.stocks_data['市盈率-动态'].replace(
            [0, float('inf')], 0
        )

        # 处理异常值
        self.stocks_data['ROIC_proxy'] = self.stocks_data['ROIC_proxy'].replace(
            [float('inf'), -float('inf')], 0
        )
        self.stocks_data['earnings_yield'] = self.stocks_data['earnings_yield'].replace(
            [float('inf'), -float('inf')], 0
        )

        print("指标计算完成")

    def apply_magic_formula_screening(self) -> None:
        """应用神奇公式筛选。"""
        if self.stocks_data is None:
            print("请先获取股票数据")
            return

        print("正在应用神奇公式筛选...")

        # 过滤有效数据
        valid_data = self.stocks_data[
            (self.stocks_data['ROIC_proxy'] > 0)
            & (self.stocks_data['earnings_yield'] > 0)
            & (self.stocks_data['市盈率-动态'] > 0)
            & (self.stocks_data['市盈率-动态'] < 50)
        ].copy()  # 排除过高市盈率

        if valid_data.empty:
            print("没有符合条件的股票")
            return

        # 计算排名
        # ROIC 排名（越高越好）
        valid_data['ROIC_rank'] = valid_data['ROIC_proxy'].rank(ascending=False)

        # 盈利收益率排名（越高越好）
        valid_data['earnings_yield_rank'] = valid_data['earnings_yield'].rank(ascending=False)

        # 综合排名（越小越好）
        valid_data['magic_score'] = valid_data['ROIC_rank'] + valid_data['earnings_yield_rank']

        # 按综合排名排序
        self.screened_stocks = valid_data.sort_values('magic_score').head(50)  # 取前50名

        print(f"筛选出{len(self.screened_stocks)}只符合神奇公式的股票")

    def save_results(self) -> Optional[pd.DataFrame]:
        """保存筛选结果。"""
        if self.screened_stocks is None or self.screened_stocks.empty:
            print("没有筛选结果可保存")
            return None

        # 选择要保存的列
        columns_to_save = [
            '代码', '名称', '最新价', '涨跌幅', '总市值', '市盈率-动态', '市净率',
            'ROIC_proxy', 'earnings_yield', 'magic_score', 'ROIC_rank',
            'earnings_yield_rank'
        ]

        # 过滤存在的列
        available_columns = [col for col in columns_to_save if col in self.screened_stocks.columns]
        result_data = self.screened_stocks[available_columns].copy()

        # 保存为CSV
        try:
            result_data.to_csv(self.result_path, index=False, encoding='utf-8-sig')
            print(f"已将筛选结果保存到 {self.result_path}")
        except (OSError, ValueError) as err:
            print(f"保存结果时出错: {err}")

        return result_data

    def run(self) -> Optional[pd.DataFrame]:
        """运行完整的选股流程。"""
        print("===== Joel Greenblatt 神奇公式选股策略 =====")
        print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.get_stock_data()
        self.calculate_magic_formula_metrics()
        self.apply_magic_formula_screening()
        result = self.save_results()

        if result is not None:
            print(f"\n共筛选出{len(result)}只股票")
            print("\n前10名股票:")
            top10 = result[
                ['代码', '名称', '最新价', '市盈率-动态', 'magic_score']
            ].head(10)
            print(top10.to_string(index=False))

        print("\n===== 选股完成 =====")
        print("注意: 本程序仅提供投资参考，不构成投资建议。")
        print("投资有风险，入市需谨慎。")

        return result


def main() -> None:
    """主函数。"""
    screener = MagicFormulaScreener()
    result = screener.run()

    if result is not None:
        print(f"\n详细结果已保存到文件，共{len(result)}只股票")


if __name__ == "__main__":
    main()
