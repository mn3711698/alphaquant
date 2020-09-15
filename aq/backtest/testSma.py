from __future__ import(absolute_import, division, print_function, unicode_literals)
from datetime import datetime, timedelta
import backtrader as bt
import os
import sys
from backtrader import cerebro
import time


# class connect_broker():
#     config = {'urls': {'api': 'https://api.sandbox.gemini.com'},
#               'apiKey': 'XXXXX',
#               'secret': 'XXXXX',
#               'nonce': lambda: str(int(time.time() * 1000))
#               }
#     broker = bt.brokers.CCXTBroker(exchange='gemini',
#                                    currency='USD', config=config)
#     cerebro.setbroker(broker)
#
#     # Create data feeds
#     data_ticks = bt.feeds.CCXT(exchange='geminy', symbol='BTC/USD',
#                                name="btc_usd_tick",
#                                timeframe=bt.TimeFrame.Ticks,
#                                compression=1, config=config)
#     cerebro.adddata(data_ticks)

import numpy as np
import math
import talib
import traceback

class Boll(bt.Indicator):
    lines = ('sma','stdev','upper','lower')
    params = (('period', 25),("multiplier",2))

    plotlines = dict(br=dict(ls='--', color='blue'))

    def __init__(self):
        self.addminperiod(self.p.period)

        # self.lines.sma = bt.talib.SMA(self.data.close, self.p.period)
    def next(self):
        data=(self.data.close.get(size=self.p.period))
        self.l.sma[0]=self.sma(data,self.p.period)
        self.l.stdev[0]=np.array(data).std()
        self.l.upper[0]=self.l.sma[0]+self.l.stdev[0]*self.p.multiplier
        self.l.lower[0] = self.l.sma[0] - self.l.stdev[0] * self.p.multiplier

    def sma(sel,x, y) :
        sum = 0.0
        for i in range(y):
            sum = sum + x[i] / y
        return sum

class Rsi(bt.Indicator):
    lines = ('vol', 'stdev', 'upper', 'lower','v1','v2','v3','v4','vol','plFound','phFound')
    params = (("period",5),
              ('vl1', 5),
              ("vl2", 5),
              ("lbR",5),
              ("lbL", 5),
              ("rangeUpper",60),
              ("rangeLower", 5),
              )

    plotlines = dict(br=dict(ls='--', color='blue'))

    def __init__(self):
        self.addminperiod(self.p.period)

        # self.lines.sma = bt.talib.SMA(self.data.close, self.p.period)

    def next(self):
        vl3=self.p.vl1+self.p.vl2
        vl4=self.p.vl2+vl3
        vl5=vl3+vl4
        self.lines.v1[0]=self.pine_wma(self.data.volume,self.p.vl1)
        self.lines.v2[0]=self.pine_wma(self.lines.v1,self.p.vl2)
        self.lines.v3[0] = self.pine_wma(self.lines.v2 , vl3)
        self.lines.v4[0] = self.pine_wma(self.lines.v3,vl4)
        self.lines.vol[0] = self.pine_wma(self.lines.v4, vl5)
        self.lines.plFound[0]=self.pivotlow(self.data.volume,self.p.lbL,self.p.lbR)
        self.lines.phFound[0] = self.pivothigh(self.data.volume, self.p.lbL, self.p.lbR)


    def _inRange(self,cond,rangeLower,rangeUpper):
        bars=self.barssince(cond)
        if rangeLower<=bars and bars<=rangeUpper:
            return True
        else:
            return False

    def barssince(self,cond):
        rt=0
        for i in  cond:
            if not i:
                rt=rt=1
            else:
                break
        return rt


    def valuewhen(self,condition, source, occurrence):
        return


    def pivotlow(self,vol,lbL,lbR):
        data=vol.get(size=(lbL+lbR+1))
        if len(data)<=0:
            return 0
        else:
            l=np.array(data[0:lbL])
            m=data[lbR:lbL+1]
            r=np.array(data[lbL+1:lbL+lbR+1])
            if m<l.min() and m<r.min():
                return True
            else:
                return False

    def pivothigh(self, vol, lbL, lbR):
        data = vol.get(size=(lbL + lbR + 1))
        if len(data) <= 0:
            return 0
        else:
            l = np.array(data[0:lbL])
            m = data[lbR:lbL + 1]
            r = np.array(data[lbL + 1:lbL + lbR + 1])
            if m > l.max() and m < r.max():
                return True
            else:
                return False

    def pine_wma(self,v,y) :
        try:
            close =np.array((self.data.close.get(size=y)))
            open= np.array((self.data.open.get(size=y)))
            volume=np.array(v.get(size=y))
            volume[np.isnan(volume)] = 0
            norm = 0.0
            sum = 0.0
            if len(volume)<y or len(close)<y or len(open)<y:
                return 0
            else:
                for i  in range(y):
                    weight = (y - i) * y
                    norm = norm + weight
                    factor =-1 if close[-(i+1)] < open[-(i+1)] else 1
                    sum = sum + (volume[-(i+1)] * weight * factor)
                rt=sum / norm
                return rt
        except Exception as e:
            print(e)
            print(traceback.print_exc())


class TrbStrategy(bt.Strategy):
    param=(
        ("length",25), #长度
        ("multiplier",2),#乘数
        ("vl1",5),#第1平均长度
        ("vl2",8),#第2平均长度
        ("lbR",5),#枢轴回溯-右
        ("lbL",5),#枢轴回溯-左
        ("rangeUpper",60),#回溯范围最大值
        ("rangeLower",5),#回溯范围最小值
        ("plotBull",True),#看涨背离
        ("plotHiddenBull",False),#看涨背离-隐藏
        ("plotBear",False),#看跌背离-隐藏
        ("Trend_res",""),#趋势MTF
        ("plotHiddenBear",False),
        ("isHA",False),#使用HA蜡烛
        ("per",45),#采样周期
        ("mult",4.06),#乘数范围
        ("sl_inp",2.76/100), #止损 %
        ("tp_imp",4.95/100 ),#止损 %
        ("useStopLoss",True)#使用止盈/止损
    )



    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''

        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # self.boll=Boll(period=25)
        self.rsi=Rsi()
        self.plFound=self.rsi.plFound
        self.phFound = self.rsi.phFound


        # self.sma=self.boll.sma
        # self.upper=self.boll.upper
        # self.lower=self.boll.lower
        self.close=self.data.close

    # def notify_order(self, order):
    #     if order.status in [order.Submitted,order.Accepted]:
    #         return
    #     if order.status in [order.Completed]:
    #         if order.isbuy():
    #             self.log('BUY EXECUTED, %.2f' % order.executed.price)
    #         elif order.issell():
    #             self.log('SELL EXECUTED, %.2f' % order.executed.price)
    #
    #         self.bar_executed = len(self)
    #     elif order.status in [order.Canceled, order.Margin, order.Rejected]:
    #         self.log('Order Canceled/Margin/Rejected')
    #     # Write down: no pending order
    #         self.order = None

    def next(self):
        self.log(f"{self.close[0]}-{self.plFound[0]},{self.phFound[0]}")

if __name__ == '__main__':
    cerebro=bt.Cerebro()
    # hist_start_data=datetime.utcnow()-timedelta(days=365)
    # data_min=bt.feeds.CCXT(exchange='bitmex',symbol="BTC/USD",name="btc_usd_min",fromdate=hist_start_data,todate=datetime.utcnow(),timeframe=bt.TimeFrame.Days)
    # cerebro.adddata(data_min)
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '.\hist_data\BINANCE_BTCUSDT.csv')
    data=bt.feeds.BacktraderCSVData(dataname=datapath,timeframe=bt.TimeFrame.Minutes)
    cerebro.adddata(data)
    cerebro.addstrategy(TrbStrategy)
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
