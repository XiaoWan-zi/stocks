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
        self.data_path = os.path.join(self.script_dir, 'stock_data.csv')
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
        
        # 临时打印原始列名用于调试
        print("股票列表原始列名:", stock_list.columns.tolist())
        
        # 过滤ST股票和退市股票
        stock_list = stock_list[~stock_list['名称'].str.contains('ST|退')]
        
        # 获取财务数据
        try:
            # 修正接口调用方式，直接获取所有股票指标数据
            financial_data = ak.stock_a_indicator_lg(symbol="all")
            print(f"成功获取{len(financial_data)}只股票的财务指标数据")
            
            # 打印财务数据列名用于调试
            print("财务数据列名:", financial_data.columns.tolist())
        except Exception as e:
            print(f"获取财务数据时出错: {e}")
            print("尝试分批获取数据...")
            financial_data = pd.DataFrame()
            batch_size = 100
            stock_codes = stock_list['代码'].tolist()
            
            for i in range(0, len(stock_codes), batch_size):
                batch_codes = stock_codes[i:i+batch_size]
                try:
                    # 分批获取，避免数据量过大
                    batch_data = pd.DataFrame()
                    for code in batch_codes:
                        stock_data = ak.stock_a_indicator_lg(symbol=code)
                        batch_data = pd.concat([batch_data, stock_data])
                        time.sleep(0.1)  # 控制请求频率
                    
                    financial_data = pd.concat([financial_data, batch_data])
                    print(f"已获取 {i+batch_size if i+batch_size < len(stock_codes) else len(stock_codes)}/{len(stock_codes)} 只股票数据")
                except Exception as e:
                    print(f"获取批次 {i//batch_size+1} 时出错: {e}")
                    continue
        
        # 合并股票数据和财务数据
        if not financial_data.empty:
            # 确定合并键
            merge_key = None
            if 'stock' in financial_data.columns:
                merge_key = 'stock'
            elif '代码' in financial_data.columns:
                merge_key = '代码'
            elif '股票代码' in financial_data.columns:
                merge_key = '股票代码'
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
                
            self.stocks_data = pd.merge(
                stock_list, 
                financial_data, 
                on=merge_key,
                how='inner'
            )
            
            # 保存数据到本地
            self.stocks_data.to_csv(self.data_path, index=False)
            print(f"成功获取{len(self.stocks_data)}只股票数据并保存到本地")
        else:
            print("未能获取到任何财务数据，请检查接口是否正常")
        
    def apply_schloss_strategy(self):
        """应用施洛斯选股策略"""
        if self.stocks_data is None:
            print("请先获取股票数据")
            return
                
        print("正在应用施洛斯选股策略...")
        
        # 定义可能的列名变体
        column_mapping = {
            '市盈率-动态': ['市盈率-动态', '动态市盈率', 'PE动态', 'PE(TTM)'],
            '市净率': ['市净率', 'PB', '市净率(PB)'],
            '资产负债率': ['资产负债率', '负债比率', '负债率'],
            '净利润同比增长率': ['净利润同比增长率', '净利润增长率', '净利润增速']
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
        
        if missing_columns:
            print(f"错误: 缺少必要的列: {', '.join(missing_columns)}")
            print("可用列包括:", self.stocks_data.columns.tolist())
            return
        
        # 检查股息率列
        dividend_candidates = ['股息率', '股息收益率', '分红率']
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
        
        # 1. 低市盈率（P/E）
        pe_filter = self.stocks_data[available_columns['市盈率-动态']] > 0
        pe_filter = pe_filter & (self.stocks_data[available_columns['市盈率-动态']] < 20)
        
        # 2. 低市净率（P/B）
        pb_filter = self.stocks_data[available_columns['市净率']] > 0
        pb_filter = pb_filter & (self.stocks_data[available_columns['市净率']] < 1.5)
        
        # 3. 高股息率（如果有数据）
        if has_dividend:
            dividend_filter = self.stocks_data[dividend_column] > 2.0
        else:
            dividend_filter = pd.Series([True] * len(self.stocks_data), index=self.stocks_data.index)
        
        # 4. 适度的债务水平（负债/资产比率）
        debt_filter = self.stocks_data[available_columns['资产负债率']] < 50
        
        # 5. 正的净利润增长率
        profit_filter = self.stocks_data[available_columns['净利润同比增长率']] > 0
        
        # 6. 足够的流动性（市值）
        market_value_filter = self.stocks_data['总市值'] > 1000000000  # 10亿元人民币
        
        # 综合筛选
        final_filter = (pe_filter & pb_filter & dividend_filter & 
                    debt_filter & profit_filter & market_value_filter)
        
        self.screened_stocks = self.stocks_data[final_filter].copy()
        
        # 计算综合评分（越低越好）
        score_components = [
            self.screened_stocks[available_columns['市盈率-动态']].rank(),
            self.screened_stocks[available_columns['市净率']].rank(),
            self.screened_stocks[available_columns['资产负债率']].rank(),
            (-1 * self.screened_stocks[available_columns['净利润同比增长率']].rank())
        ]
        
        if has_dividend:
            score_components.append(-1 * self.screened_stocks[dividend_column].rank())
        
        self.screened_stocks['评分'] = sum(score_components)
        
        # 按评分排序
        self.screened_stocks = self.screened_stocks.sort_values(by='评分')
        
        print(f"筛选出{len(self.screened_stocks)}只符合条件的股票")
        
    def analyze_results(self):
        """分析筛选结果"""
        if self.screened_stocks is None or len(self.screened_stocks) == 0:
            print("没有筛选出符合条件的股票")
            return
            
        print("\n===== 筛选结果分析 =====")
        
        # 行业分布
        industry_distribution = self.screened_stocks['行业'].value_counts()
        print("\n行业分布:")
        print(industry_distribution.head(5))
        
        # 评分分布
        plt.figure(figsize=(10, 6))
        plt.hist(self.screened_stocks['评分'], bins=10, alpha=0.7)
        plt.title('筛选股票评分分布')
        plt.xlabel('评分')
        plt.ylabel('股票数量')
        plt.grid(True)
        plt.savefig(os.path.join(self.script_dir, 'score_distribution.png'))
        print("\n评分分布图表已保存为 score_distribution.png")
        
        # 显示筛选出的股票
        top_stocks = self.screened_stocks[['代码', '名称', '行业', '市盈率-动态', '市净率', 
                                           '股息率', '资产负债率', '净利润同比增长率', '评分']].head(10)
        print("\n施洛斯策略筛选出的优质股票:")
        print(top_stocks.to_string(index=False))
        
        return top_stocks
        
    def run(self):
        """运行完整的选股流程"""
        self.get_stock_data()
        self.apply_schloss_strategy()
        return self.analyze_results()

if __name__ == "__main__":
    print("===== 沃尔特·施洛斯A股低估值选股策略 =====")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    screener = SchlossStockScreening()
    top_stocks = screener.run()
    
    print("\n===== 选股完成 =====")
    print("注意: 本程序仅提供投资参考，不构成投资建议。")
    print("投资有风险，入市需谨慎。")        