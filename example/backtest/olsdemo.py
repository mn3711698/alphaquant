# -*- coding:utf-8 -*-
"""
@Time : 2020/4/4 2:48 下午
@Author : Domionlu
@Site :
@File : olsdemo.py
@Software: PyCharm
"""
import pandas as pd
import numpy as np
from aq.indicator.base import *
from aq.common.tools import time_cost
from aq.risk.analysis import *
import talib
import matplotlib.pyplot as plt
from pyecharts.charts import Line
import pyecharts.options as opts

@time_cost
def main():
    feed = pd.read_csv("binance_BTCUSDT_1d.csv")
    feed['time'] = pd.to_datetime(feed['time'])
    feed['beta'] = polyslope(feed['close'], 7)
    buy = feed[feed['beta'] > feed['beta'].shift(1)].index
    feed.loc[buy, 'signal'] = 1
    print(feed)


@time_cost
def test1(feed):

    feed['beta'] = polyslope(feed['close'], 7)
    feed['ema45']=talib.EMA(feed['close'],timeperiod=45)
    feed['buy']= feed['beta'].rolling(15).apply(up,raw=True)
    feed['sell']=feed['beta'].rolling(15).apply(down,raw=True)
    feed['endprice']=0
    trade=[]
    for i in range(1, len(feed) - 1):
        df=feed.loc[i,:]
        if df['buy']==1:
            buyindex=i
            trade.append([df['time'],'Buy',df['close'],1,df.index])
        if df['sell']==1:
            feed.loc[buyindex,"endprice"]=df['close']
            trade.append([df['time'], 'Sell', df['close'], 1,df.index])
    buy=feed.loc[feed.buy==1].copy()
    buy['pnl']=buy['endprice']-buy['close']
    buy["pnlr"] = (buy['endprice'] - buy['close'])/buy['close']
    # plt.plot(buy.time,buy.close,color='red')
    buy=buy.drop(buy.tail(1).index)
    print(buy)
    plt.plot(buy.time, buy.pnl, color='green')
    plt.plot(buy.time, buy.beta)
    plt.show()

@time_cost
def test2(feed):
    feed['b7']=polyslope(feed['close'],7)
    feed['b56']=polyslope(feed['close'],56)
    feed['ts']=feed['b56'].rolling(15).apply(side,raw=True)
    feed['up']=feed['b7'].rolling(15).apply(up,raw=True)
    feed['down']=feed['b7'].rolling(15).apply(down,raw=True)
    feed['buy']=0
    feed['sell'] = 0
    feed.loc[(feed.ts==1) & (feed.up==1),'buy']=1
    feed.loc[(feed.ts!=1) & (feed.down==1),'sell']=1
    trade = []
    buyindex=0
    for i in range(1, len(feed) - 1):
        df = feed.loc[i, :]
        if df['buy'] == 1:
            buyindex = i
            trade.append([df['time'], 'Buy', df['close'], 1, df.index])
        if df['sell'] == 1 and buyindex>0:
            feed.loc[buyindex, "endprice"] = df['close']
            trade.append([df['time'], 'Sell', df['close'], 1, df.index])
    pls,ws=pls_ws(trade)
    line = Line()
    line.add_xaxis(feed.time)
    line.add_yaxis("收盘价", feed.close)
    line.set_global_opts(title_opts=opts.TitleOpts(title="Line-基本示例"))
    line.render("line_base.html")

    buy=feed[feed.buy==1]


    print(f"{pls},{ws}")


def res(data):
    trade = []
    for i in data:
        time = i[0]
        side = i[1]
        price = i[2]
        volume = i[3]
        index=i[4]
        if side == "Buy":
            trade.append([time, price, 0, 0, 0,index])
        if side == "Sell" and len(trade) > 0:
            trade[-1][2] = price
            trade[-1][3] = price - trade[-1][1]
            trade[-1][4] = (price - trade[-1][1]) / trade[-1][1]
    result = pd.DataFrame(trade, columns=["time", "open", "close", "pnl", "res","index"])
    return result

if __name__ == "__main__":
    feed = pd.read_csv("btc30m.csv")
    feed['time'] = pd.to_datetime(feed['time'])
    test2(feed)


    pass