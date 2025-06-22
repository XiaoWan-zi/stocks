import pandas as pd
import numpy as np
import akshare as ak
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
import time
import os

# 忽略警告
warnings.filterwarnings('ignore')

class SchlossStockScreening:
    def __init__(self):
        """初始化选股策略类"""
        self.stocks_data = None
        self.market_data = None
        self.screened_stocks = None
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(self.script_dir, 'stock_data_by_ws.csv')
        self.result_path_csv = os.path.join(self.script_dir, '筛选结果.csv')
        self.today = datetime.now().strftime('%Y-%m-%d')
        
    def get_stock_data(self):
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
        
        # 获取财务数据
        financial_data = self._get_financial_data(stock_list)
        
        if financial_data is None:
            print("未能获取到任何财务数据，请检查接口是否正常")
            return
            
        # 合并股票数据和财务数据
        # 确定合并键
        merge_key = None
        if 'stock' in financial_data.columns:
            merge_key = 'stock'
        elif '代码' in financial_data.columns:
            merge_key = '代码'
        elif '股票代码' in financial_data.columns:
            merge_key = '股票代码'
        elif 'code' in financial_data.columns:
            merge_key = 'code'
        else:
            # 尝试找出可能的股票代码列
            potential_keys = [col for col in financial_data.columns if '代码' in col or 'code' in col.lower()]
            if potential_keys:
                merge_key = potential_keys[0]
                print(f"使用潜在的合并键: {merge_key}")
            else:
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
        
    def _get_financial_data(self, stock_list):
        """获取财务数据的辅助方法，支持多数据源尝试"""
        print("尝试获取财务数据...")
        
        # 首先尝试使用原来的接口
        try:
            financial_data = ak.stock_a_indicator_lg(symbol="all")
            print(f"成功获取{len(financial_data)}只股票的财务指标数据")
            return financial_data
        except Exception as e:
            print(f"获取主要财务数据时出错: {e}")
        
        # 如果主要数据源失败，尝试备选数据源
        try:
            # 使用stock_financial_analysis_indicator获取财务分析指标
            financial_data = pd.DataFrame()
            stock_codes = stock_list['代码'].tolist()
            batch_size = 100
            
            for i in range(0, len(stock_codes), batch_size):
                batch_codes = stock_codes[i:i+batch_size]
                batch_data = pd.DataFrame()
                
                for code in batch_codes:
                    try:
                        # 尝试获取单只股票的财务分析指标
                        stock_financial = ak.stock_financial_analysis_indicator(stock=code)
                        if not stock_financial.empty:
                            # 添加股票代码列以便合并
                            stock_financial['code'] = code
                            batch_data = pd.concat([batch_data, stock_financial])
                        time.sleep(0.1)  # 控制请求频率
                    except Exception as e:
                        print(f"获取股票 {code} 财务分析指标时出错: {e}")
                        continue
                
                if not batch_data.empty:
                    financial_data = pd.concat([financial_data, batch_data])
                
                print(f"已获取 {i+batch_size if i+batch_size < len(stock_codes) else len(stock_codes)}/{len(stock_codes)} 只股票财务分析数据")
            
            if not financial_data.empty:
                # 转换列名以便匹配原代码
                financial_data = self._map_financial_columns(financial_data)
                print(f"备选数据源成功获取{len(financial_data)}只股票的财务分析数据")
                return financial_data
            else:
                print("备选数据源也未能获取到财务数据")
        except Exception as e:
            print(f"获取备选财务数据时出错: {e}")
        
        # 如果所有方法都失败，返回股票列表作为基础数据
        print("警告: 未能获取到财务数据，将仅使用股票基本信息进行筛选")
        return stock_list[['代码', '名称', '最新价', '涨跌幅', '总市值', '流通市值', '市盈率-动态', '市净率']]
    
    def _map_financial_columns(self, df):
        """将备选数据源的列名映射到主程序使用的列名"""
        column_mapping = {
            '资产负债率(%)': '资产负债率',
            '净利润同比增长率(%)': '净利润同比增长率',
            # 可以添加更多映射关系
        }
        
        # 重命名列
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        # 转换百分比数据为数值
        for col in ['资产负债率', '净利润同比增长率']:
            if col in df.columns and df[col].dtype == 'object':
                df[col] = df[col].str.rstrip('%').astype(float) / 100.0
        
        return df
        
    def apply_schloss_strategy(self):
        """应用施洛斯选股策略"""
        if self.stocks_data is None:
            print("请先获取股票数据")
            return
                
        print("正在应用施洛斯选股策略...")
        
        # 定义可能的列名变体
        column_mapping = {
            '市盈率-动态': ['市盈率-动态', '动态市盈率', 'PE动态', 'PE(TTM)', '市盈率(TTM)'],
            '市净率': ['市净率', 'PB', '市净率(PB)'],
            '资产负债率': ['资产负债率', '负债比率', '负债率', '资产负债率(%)'],
            '净利润同比增长率': ['净利润同比增长率', '净利润增长率', '净利润增速', '净利润同比增长率(%)']
        }
        
        # 查找实际存在的列名
        available_columns = {}
        missing_columns = []
        
        for required, candidates in column_mapping.items():
            found = False
            for candidate in candidates:
                if candidate in self.stocks_data.columns:
                    available_columns[required] = candidate
                    found = True
                    break
            if not found:
                missing_columns.append(required)
        
        # 打印缺失的列，但不终止程序
        if missing_columns:
            print(f"警告: 缺少以下列，将跳过对应的筛选条件: {', '.join(missing_columns)}")
        
        # 检查股息率列
        dividend_candidates = ['股息率', '股息收益率', '分红率', '股息率(%)']
        dividend_column = None
        
        for candidate in dividend_candidates:
            if candidate in self.stocks_data.columns:
                dividend_column = candidate
                break
        
        if dividend_column is None:
            print("警告: 数据中不存在股息率相关列，将跳过该筛选条件")
            has_dividend = False
        else:
            has_dividend = True
            print(f"使用股息率列: {dividend_column}")
            
            # 确保股息率是数值类型
            if self.stocks_data[dividend_column].dtype == 'object':
                self.stocks_data[dividend_column] = self.stocks_data[dividend_column].str.rstrip('%').astype(float)
        
        # 初始化所有筛选条件为True
        pe_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        pb_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        dividend_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        debt_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        profit_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        market_value_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        
        # 1. 低市盈率（P/E）
        if '市盈率-动态' in available_columns:
            pe_filter = self.stocks_data[available_columns['市盈率-动态']] > 0
            pe_filter = pe_filter & (self.stocks_data[available_columns['市盈率-动态']] < 20)
            print(f"应用市盈率筛选，保留PE在0-20之间的股票")
        else:
            print("警告: 缺少市盈率数据，跳过该筛选条件")
        
        # 2. 低市净率（P/B）
        if '市净率' in available_columns:
            pb_filter = self.stocks_data[available_columns['市净率']] > 0
            pb_filter = pb_filter & (self.stocks_data[available_columns['市净率']] < 1.5)
            print(f"应用市净率筛选，保留PB在0-1.5之间的股票")
        else:
            print("警告: 缺少市净率数据，跳过该筛选条件")
        
        # 3. 高股息率（如果有数据）
        if has_dividend:
            dividend_filter = self.stocks_data[dividend_column] > 2.0  # 假设股息率单位为%
            print(f"应用股息率筛选，保留股息率大于2%的股票")
        
        # 4. 适度的债务水平（负债/资产比率）
        if '资产负债率' in available_columns:
            debt_filter = self.stocks_data[available_columns['资产负债率']] < 50
            print(f"应用资产负债率筛选，保留负债率低于50%的股票")
        
        # 5. 正的净利润增长率
        if '净利润同比增长率' in available_columns:
            profit_filter = self.stocks_data[available_columns['净利润同比增长率']] > 0
            print(f"应用净利润增长率筛选，保留增长率为正的股票")
        
        # 6. 足够的流动性（市值）
        if '总市值' in self.stocks_data.columns:
            market_value_filter = self.stocks_data['总市值'] > 1000000000  # 10亿元人民币
            print(f"应用市值筛选，保留总市值大于10亿元的股票")
        else:
            print("警告: 缺少总市值数据，跳过该筛选条件")
        
        # 综合筛选
        final_filter = (pe_filter & pb_filter & dividend_filter & 
                    debt_filter & profit_filter & market_value_filter)
        
        self.screened_stocks = self.stocks_data[final_filter].copy()
        
        if self.screened_stocks.empty:
            print("没有筛选出符合条件的股票")
            return
        
        # 计算综合评分（越低越好）
        score_components = []
        
        if '市盈率-动态' in available_columns:
            score_components.append(self.screened_stocks[available_columns['市盈率-动态']].rank())
            
        if '市净率' in available_columns:
            score_components.append(self.screened_stocks[available_columns['市净率']].rank())
            
        if '资产负债率' in available_columns:
            score_components.append(self.screened_stocks[available_columns['资产负债率']].rank())
            
        if '净利润同比增长率' in available_columns:
            score_components.append(-1 * self.screened_stocks[available_columns['净利润同比增长率']].rank())
            
        if has_dividend:
            score_components.append(-1 * self.screened_stocks[dividend_column].rank())
        
        if score_components:
            self.screened_stocks['评分'] = sum(score_components)
            # 按评分排序
            self.screened_stocks = self.screened_stocks.sort_values(by='评分')
            print(f"筛选出{len(self.screened_stocks)}只符合条件的股票，并计算了综合评分")
        else:
            print(f"筛选出{len(self.screened_stocks)}只符合条件的股票，但缺少足够数据计算综合评分")
        
    def save_results_to_table(self):
        """将筛选结果保存到表格中"""
        if self.screened_stocks is None or self.screened_stocks.empty:
            print("没有筛选出符合条件的股票，无法保存结果")
            return
        
        # 确定要保存的列
        columns_to_save = ['代码', '名称']
        
        # 添加可选列，直接检查self.screened_stocks的列
        if '行业' in self.screened_stocks.columns:
            columns_to_save.append('行业')
            
        if '最新价' in self.screened_stocks.columns:
            columns_to_save.append('最新价')
            
        if '涨跌幅' in self.screened_stocks.columns:
            columns_to_save.append('涨跌幅')
            
        if '总市值' in self.screened_stocks.columns:
            columns_to_save.append('总市值')
            
        # 直接检查列名是否存在，不依赖available_columns
        for col in ['市盈率-动态', '市净率', '股息率', '资产负债率', '净利润同比增长率', '评分']:
            if col in self.screened_stocks.columns:
                columns_to_save.append(col)
        
        # 确保列名唯一
        columns_to_save = list(dict.fromkeys(columns_to_save))
        print(columns_to_save)
        
        # 避免KeyError
        available_columns_to_save = [col for col in columns_to_save if col in self.screened_stocks.columns]
        
        if not available_columns_to_save:
            print("警告: 没有可用的列来保存筛选结果")
            return
            
        # 准备保存的数据
        result_data = self.screened_stocks[available_columns_to_save].copy()
        
        # 保存为CSV
        try:
            result_data.to_csv(self.result_path_csv, index=False, encoding='utf-8-sig')
            print(f"已将筛选结果保存到 {self.result_path_csv}")
        except Exception as e:
            print(f"保存CSV文件时出错: {e}")
        
        return result_data
        
    def run(self):
        """运行完整的选股流程"""
        self.get_stock_data()
        self.apply_schloss_strategy()
        return self.save_results_to_table()

if __name__ == "__main__":
    print("===== 沃尔特·施洛斯A股低估值选股策略 =====")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    screener = SchlossStockScreening()
    result = screener.run()
    
    if result is not None:
        print(f"\n共筛选出{len(result)}只股票，已保存到表格中")
    
    print("\n===== 选股完成 =====")
    print("注意: 本程序仅提供投资参考，不构成投资建议。")
    print("投资有风险，入市需谨慎。")