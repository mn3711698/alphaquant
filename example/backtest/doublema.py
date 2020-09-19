import backtrader as bt
import os,sys
from backtrader.order import Order
import pandas as pd
import numpy as np
import backtrader.analyzers as btanalyzers
import datetime

class Doublema(bt.Strategy):
    params = {"short_window": 15, "long_window": 30}

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.short_ma = bt.indicators.SMA(self.datas[0].close,period=self.p.short_window)
        self.long_ma = bt.indicators.SMA(self.datas[0].close,period=self.p.long_window)


    def next(self):
        self.log(f"short_ma:{self.short_ma[0]},long_ma:{self.long_ma[0]}")


df = pd.read_csv("BINANCE_BTCUSDT.csv", encoding='gbk')  # df=pd.read_csv(data_path,encoding='gbk')
df.index = pd.to_datetime(df['time'])
df = df[['open', 'high', 'low', 'close', 'volume']]
df["openinterest"]=-1
params = dict(
    fromdate=datetime.datetime(2010, 1, 4),
    todate=datetime.datetime(2020, 3, 20),
    timeframe=bt.TimeFrame.Minutes,
    compression=1,
    dtformat=('%Y-%m-%d %H:%M:%S'),
    tmformat=('%H:%M:%S'),
    datetime=0,
    high=2,
    low=3,
    open=1,
    close=4,
    volume=5,
    openinterest=6)
df = df[['open', 'high', 'low', 'close', 'volume', 'openinterest']]
feed =  bt.feeds.PandasDirectData(dataname=df,**params)
cerebro = bt.Cerebro()
cerebro.adddata(feed,name = "btc")
cerebro.addstrategy(Doublema)
cerebro.broker.setcommission(commission=0.0005)
cerebro.broker.setcash(100000.0)
cerebro.run()
