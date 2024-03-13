import numpy as np
import pandas as pd
import akshare as ak
import mpl_finance as mpf   #告警：该库名字可以更新
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

#将股票时间转换为标准时间，不带时分秒的数据 目前有错
# def date_to_num(dates):
#     num_time = []
#     for date in dates:
#         date_time = datetime.strptime(date, '%Y-%m-%d')
#         num_date = date2num(date_time)
#         num_time.append(num_date)
#     return num_time

def mean_line():
    df = ak.stock_zh_a_daily(symbol='sz002241', start_date="20220203", end_date="20230204",
                             adjust="qfq")
    print(df['close'].iloc[-1])
    df.to_excel("歌尔股份k.xlsx")
    # 创建绘图的基本参数
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111)
    # 获取刚才的股票数据
    df = pd.read_excel("歌尔股份k.xlsx")
    mpf.candlestick2_ochl(ax, df["open"], df["close"], df["high"], df["low"], width=0.6, colorup='r', colordown='green',
                          alpha=1.0)
    df['date'] = pd.to_datetime(df['date'])
    df['date'] = df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))

    def format_date(x, pos=None):
        if x < 0 or x > len(df['date']) - 1:
            return ''
        return df['date'][int(x)]

    # ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    # plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    #
    df["SMA50"] = df["close"].rolling(50).mean()
    print(df["SMA50"].iloc[-1])
    # df["SMA150"] = df["close"].rolling(150).mean()
    # df["SMA200"] = df["close"].rolling(200).mean()
    # ax.plot(np.arange(0, len(df)), df['SMA50'])  # 绘制50日均线
    # ax.plot(np.arange(0, len(df)), df['SMA150'])  # 绘制150日均线
    # ax.plot(np.arange(0, len(df)), df['SMA200'])  # 绘制200日均线
    #
    # # 显示出来
    # plt.show()

# VCP 第二阶段需要符合以下的条件：
# 1) 股价高过50日、150日和200日均线
# 2) 50日均线高于150日均线；而150日均线同时又高于200日均线
# 3) 200日均线向上倾斜至少一个月，多数四、五个月以上
# 4) 股价较52周低点至少高出30%
# 5) 股价较52周高点不超过25%
# 6) RS（Relative Strength）不低于70，最好是80多或90多.

vcp = []

def my_filter(symbol, name):
    df = ak.stock_zh_a_daily(symbol=symbol, start_date="20220203", end_date="20230304",
                             adjust="qfq")
    if df.empty:
        return
    yesterday = df["close"].iloc[-1]
    value_50 = df["close"].tail(50).mean()
    value_150 = df["close"].tail(150).mean()
    value_200 = df["close"].tail(200).mean()
    if yesterday < max([value_50, value_150, value_200]):
        return
    if value_150 < value_200 or value_50 < value_150:
        return

    df["SMA200"] = df["close"].rolling(200).mean()
    if len(df["SMA200"]) < 262:
        return
    if df["SMA200"].iloc[-1] < df["SMA200"].iloc[-151]:
        return
    min_52weeks = df["close"].tail(365).min()
    max_52weeks = df["close"].tail(365).max()
    if yesterday/min_52weeks < 1.3 or yesterday/max_52weeks > 1 or yesterday/max_52weeks < 0.7:
        return
    print(symbol, name)
    vcp.append(symbol+name)
    return

def get_all_stocks():
    # 打印所有指数股票，速度较慢
    stock_df = ak.stock_zh_index_spot()
    print(stock_df)
    # stock_df.to_excel("all.xlsx")

if __name__ == '__main__':
    df1 = ak.stock_zh_a_spot_em()
    # print(df1)
    df1 = df1.query("昨收 >= 10")
    # df1.to_excel("price_less_10.xlsx")

    # my_filter('sz002235')
    for index,row in df1.iterrows():
        # 序号    5280
        # 代码    002708
        # 名称    光洋股份
        # 最新价    7.93
        # 涨跌幅 - 9.99
        # 涨跌额 - 0.88
        # 成交量    459810.0
        # 成交额    368285518.89
        # 振幅    4.88
        # 最高    8.36
        # 最低    7.93
        # 今开    8.27
        # 12:昨收    8.81
        # 量比    1.64
        # 换手率    11.3
        # 市盈率 - 动态 - 20.26
        # 市净率    2.93
        # 总市值    3901647833.0
        # 流通市值    3225512116.0
        # 涨速    0.05
        # 分钟涨跌    0.060
        # 日涨跌幅    18.89
        # 年初至今涨跌幅    42.37
        if 0 == row[14]:
            continue
        # 00 开头的股票是深交所主板的股票
        if row[1][0:2] == '00':
            symbol = 'sz' + row[1]
            my_filter(symbol, row[2])
        # 60 开头是股票是上交所主板的股票
        elif row[1][0:2] == '60':
            symbol = 'sh' + row[1]
            my_filter(symbol, row[2])
        # 科创板 暂不处理 30:深交所创业板 68:上交所科创板 8:北交所新三板精选层
        # elif row[1][0:2] == '30':
        #     symbol = 'sz' + row[1]
        # elif row[1][0:2] == '68':
        #     symbol = 'sh' + row[1]

    print(vcp)
    # df.to_excel("stock_zh_a_daily.xlsx")
