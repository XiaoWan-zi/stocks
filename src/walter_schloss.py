import pandas as pd
import akshare as ak
import warnings
import time
import os
from datetime import datetime
from typing import Optional

# 忽略警告
warnings.filterwarnings('ignore')

class SchlossStockScreening:
    def __init__(self):
        """初始化选股策略类"""
        self.stocks_data = None
        self.screened_stocks = None
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(self.script_dir, 'stock_data_all_by_ws.csv')
        self.result_path_csv = os.path.join(self.script_dir, '筛选结果.csv')
        self.today = datetime.now().strftime('%Y-%m-%d')
        
    def get_stock_data(self) -> None:
        """获取A股股票数据"""
        print("正在获取A股股票数据...")
        
        # 检查是否有今天的本地数据
        if os.path.exists(self.data_path):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(self.data_path))
            file_date = file_mtime.strftime('%Y-%m-%d')
            
            if file_date == self.today:
                print("读取本地缓存数据...")
                self.stocks_data = pd.read_csv(self.data_path)
                print(f"成功读取{len(self.stocks_data)}只股票数据")
                return
        
        # 获取股票列表
        stock_list = ak.stock_zh_a_spot_em()
        
        # 过滤ST股票和退市股票
        stock_list = stock_list[~stock_list['名称'].str.contains('ST|退')]

        # 调试少量数据
        # stock_list = stock_list[:3]
        
        # 获取财务数据
        financial_data = self._get_financial_data(stock_list)
        
        if financial_data is None:
            print("未能获取到任何财务数据，请检查接口是否正常")
            return
            
        # 合并股票数据和财务数据
        merge_key = self._get_merge_key(financial_data, stock_list)
        if merge_key is None:
            print("无法确定合并键，请检查财务数据结构")
            return
            
        # 确保股票列表使用相同的合并键名称
        if merge_key != '代码' and '代码' in stock_list.columns:
            stock_list = stock_list.rename(columns={'代码': merge_key})
        
        # 合并数据
        self.stocks_data = pd.merge(
            stock_list, 
            financial_data, 
            on=merge_key,
            how='inner'
        )
        
        # 保存数据到本地
        self.stocks_data.to_csv(self.data_path, index=False)
        print(f"成功获取{len(self.stocks_data)}只股票数据并保存到本地")
        
    def _get_financial_data(self, stock_list: pd.DataFrame) -> Optional[pd.DataFrame]:
        """获取财务数据，使用指定start_year的stock_financial_analysis_indicator"""
        print("尝试获取财务数据...")
        financial_data = pd.DataFrame()
        stock_codes = stock_list['代码'].tolist()
        batch_size = 50  # 减小批次大小避免请求失败
        
        for i in range(0, len(stock_codes), batch_size):
            batch_codes = stock_codes[i:i+batch_size]
            batch_data = pd.DataFrame()
            
            for code in batch_codes:
                try:
                    # 获取单只股票的财务分析指标，指定start_year为2025
                    stock_financial = ak.stock_financial_analysis_indicator(
                        symbol=code, 
                        start_year="2025"
                    )
                    if not stock_financial.empty:
                        # 只保留最新一期数据（假设最后一行是最新）
                        if len(stock_financial) > 0:
                            stock_financial = stock_financial.iloc[[-1]]
                            stock_financial['代码'] = code
                            batch_data = pd.concat([batch_data, stock_financial])
                    time.sleep(0.3)  # 增加延时避免频繁请求
                except Exception as e:
                    print(f"获取股票 {code} 财务数据时出错: {e}")
                    continue
            
            if not batch_data.empty:
                financial_data = pd.concat([financial_data, batch_data])
            
            print(f"已获取 {i+batch_size if i+batch_size < len(stock_codes) else len(stock_codes)}/{len(stock_codes)} 只股票财务数据")
        
        if not financial_data.empty:
            # 转换列名以便匹配
            financial_data = self._map_financial_columns(financial_data)
            print(f"成功获取{len(financial_data)}只股票的财务分析数据")
            return financial_data
        else:
            print("未能获取到财务数据，将仅使用股票基本信息进行筛选")
            return stock_list[['代码', '名称', '最新价', '涨跌幅', '总市值', '流通市值', '市盈率-动态', '市净率']]
    
    def _map_financial_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """映射财务数据列名为统一格式"""
        column_mapping = {
            '资产负债率(%)': '资产负债率',
            '净利润增长率(%)': '净利润同比增长率',
            # 其他可能需要的映射
        }
        return df.rename(columns=column_mapping)
    
    def _get_merge_key(self, financial_data: pd.DataFrame, stock_list: pd.DataFrame) -> Optional[str]:
        """智能获取合并键"""
        print(f"{financial_data}, {stock_list}")
        potential_keys = ['stock', '代码', '股票代码', 'code']
        for key in potential_keys:
            if key in financial_data.columns and key in stock_list.columns:
                return key
        return None
    
    def apply_schloss_strategy(self) -> None:
        """应用施洛斯选股策略"""
        if self.stocks_data is None:
            print("请先获取股票数据")
            return
                
        print("正在应用施洛斯选股策略...")
        required_columns = ['市盈率-动态', '市净率', '资产负债率', '净利润同比增长率']
        available_columns = {col: col for col in required_columns if col in self.stocks_data.columns}
        missing_columns = [col for col in required_columns if col not in available_columns]
        
        if missing_columns:
            print(f"警告: 缺少关键列 {', '.join(missing_columns)}，部分筛选条件将无法应用")
        
        # 初始化筛选条件
        pe_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        pb_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        debt_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        profit_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        market_value_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        
        # 1. 低市盈率（P/E）
        if '市盈率-动态' in available_columns:
            pe_filter = (self.stocks_data[available_columns['市盈率-动态']] > 0) & \
                        (self.stocks_data[available_columns['市盈率-动态']] < 20)
            print("应用市盈率筛选，保留PE在0-20之间的股票")
        
        # 2. 低市净率（P/B）
        if '市净率' in available_columns:
            pb_filter = (self.stocks_data[available_columns['市净率']] > 0) & \
                        (self.stocks_data[available_columns['市净率']] < 1.5)
            print("应用市净率筛选，保留PB在0-1.5之间的股票")
        
        # 3. 适度的债务水平
        if '资产负债率' in available_columns:
            debt_filter = self.stocks_data[available_columns['资产负债率']] < 50
            print("应用资产负债率筛选，保留负债率低于50%的股票")
        
        # 4. 正的净利润增长率
        if '净利润同比增长率' in available_columns:
            profit_filter = self.stocks_data[available_columns['净利润同比增长率']] > 0
            print("应用净利润增长率筛选，保留增长率为正的股票")
        
        # 5. 足够的流动性（市值）
        if '总市值' in self.stocks_data.columns:
            market_value_filter = self.stocks_data['总市值'] > 1000000000  # 10亿元人民币
            print("应用市值筛选，保留总市值大于10亿元的股票")
        
        # 综合筛选
        final_filter = pe_filter & pb_filter & debt_filter & profit_filter & market_value_filter
        self.screened_stocks = self.stocks_data[final_filter].copy()
        
        if self.screened_stocks.empty:
            print("没有筛选出符合条件的股票")
            return
        
        print(f"筛选出{len(self.screened_stocks)}只符合条件的股票")
    
    def save_results_to_table(self) -> Optional[pd.DataFrame]:
        """将筛选结果保存到表格中"""
        if self.screened_stocks is None or self.screened_stocks.empty:
            print("没有筛选出符合条件的股票，无法保存结果")
            return
        
        # 确定要保存的列
        columns_to_save = ['代码', '名称']
        optional_columns = ['行业', '最新价', '涨跌幅', '总市值', 
                           '市盈率-动态', '市净率', '资产负债率', '净利润同比增长率']
        
        for col in optional_columns:
            if col in self.screened_stocks.columns:
                columns_to_save.append(col)
        
        # 去重并检查可用性
        available_columns = [col for col in columns_to_save if col in self.screened_stocks.columns]
        if not available_columns:
            print("警告: 没有可用的列来保存筛选结果")
            return
            
        # 保存为CSV
        result_data = self.screened_stocks[available_columns].copy()
        try:
            result_data.to_csv(self.result_path_csv, index=False, encoding='utf-8-sig')
            print(f"已将筛选结果保存到 {self.result_path_csv}")
        except Exception as e:
            print(f"保存CSV文件时出错: {e}")
        
        return result_data
        
    def run(self) -> Optional[pd.DataFrame]:
        """运行完整的选股流程"""
        self.get_stock_data()
        self.apply_schloss_strategy()
        return self.save_results_to_table()

def main() -> None:
    print("===== 沃尔特·施洛斯A股低估值选股策略 =====")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    screener = SchlossStockScreening()
    result = screener.run()
    if result is not None:
        print(f"\n共筛选出{len(result)}只股票，已保存到表格中")
    print("\n===== 选股完成 =====")
    print("注意: 本程序仅提供投资参考，不构成投资建议。")
    print("投资有风险，入市需谨慎。")


if __name__ == "__main__":
    main()