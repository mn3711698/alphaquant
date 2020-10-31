import os
import sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

import backtrader as bt
import numpy as np
import talib
from aq.indicator.rsi import *
import requests
import json
import traceback


class FisherStategy(bt.Strategy):
    params = (
        ('period', 6),
    )

    def __init__(self):
        # self.fish=Fisher()
        # self.order=None
        self.hs15=self.dnames.hs15m
        self.hs1h=self.dnames.hs1h
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.dnames.hs15m.datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))
    def next(self):
        idx=self.data.close.get_idx()
        if idx>self.p.period*2*4:
            data15m=np.array(self.hs15.close.get(size=idx))
            frsi=trend_frsi(data15m,self.p.period)
            if frsi==1:
                self.order=self.buy()
            if frsi==-1:
                self.order=self.sell()
        # if not self.position:
        #     # Not yet ... we MIGHT BUY if ...
        #     if self.fish[0]>self.fish[1] and self.fish[1]<self.fish[2]:
        #         # Keep track of the created order to avoid a 2nd order
        #         self.order = self.buy()
        # else:
        #     # Already in the market ... we might sell
        #     if self.fish[0]<self.fish[1] and self.fish[1]>self.fish[2]:
        #         # Keep track of the created order to avoid a 2nd order
        #         self.order = self.sell()


def run():
    cerebro = bt.Cerebro()
    # hist_start_data=datetime.utcnow()-timedelta(days=365)
    # data_min=bt.feeds.CCXT(exchange='bitmex',symbol="BTC/USD",name="btc_usd_min",fromdate=hist_start_data,todate=datetime.utcnow(),timeframe=bt.TimeFrame.Days)
    # cerebro.adddata(data_min)
    df=load()
    feed = bt.feeds.PandasData(dataname=df, openinterest=None, compression=15, timeframe=bt.TimeFrame.Minutes)
    cerebro.adddata(feed, name='hs15m')
    cerebro.resampledata(feed, name='hs1h', timeframe=bt.TimeFrame.Minutes, compression=60)
    cerebro.addstrategy(FisherStategy)
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.run(runonce=False)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

def download(symbol,tf,starttime):
    url=" https://api.binance.com/api/v3/klines"
    param={"symbol":symbol,"interval":tf,"startTime":starttime}
    data=requests.get(url,params=param)
    data=json.loads(data.text)
    rs=len(data)
    starttime=data[-1][6]
    param["startTime"]=starttime
    try:
        while rs>0:
            d = requests.get(url, params=param)
            d = json.loads(d.text)
            if len(d)>0:
                starttime=d[-1][6]
                param["startTime"]=starttime
                for i in d:
                    data.append(i)
                print("add new data")
            else:
                rs=0
    except Exception as e:
        print(e)
        print(traceback.print_exc())

    data=pd.DataFrame(data,columns=["starttime","open","high","low","close","volume","endtime","amount","trades","buy","sell","t"])
    data.to_csv(symbol+".csv")
    print(data.tail())


def load():
    data=pd.read_csv("BTCUSDT.csv")
    data=data[["starttime", "open","high","low","close","volume","trades"]]
    data["starttime"]=pd.to_datetime(data["starttime"],unit="ms")
    data=data.set_index("starttime")
    return data


if __name__ == '__main__':
    run()