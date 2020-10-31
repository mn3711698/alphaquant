# -*- coding:utf-8 -*-
"""
@Time : 2020/5/9 12:02 上午
@Author : Domionlu
@Site : 
@File : main.py
"""
from aq.engine.baseStrategy import BaseStrategy
from aq.broker.binancefutures import BinanceFutures
from aq.backtest.hist_data.config import config
from aq.indicator.base import *
from aq.common.utility import RepeatingTimer
from aq.common.constant import *
from aq.engine.event import EventEngine

import talib

class SHstrategy(BaseStrategy):
    """
    StrengthHedge,趋势强度对冲策略
    根据4小时TSI信号，0轴向上做多，0轴向下做空，
    多空仓位保持平衡
    """

    def __init__(self, engine):
        super().__init__(engine)
        self.bar={}
        self.t={}
        cfg=config.exchange
        self.broker=BinanceFutures(cfg)
        self.symbols = cfg.symbols
        self.timeframe=cfg.timeframe
        self.update()


    def start(self):
        bar=self.broker.get_bar(self.symbol,self.timeframe)
        self.bar=bar
        self.on_bar(bar[-1])

    def on_bar(self, event):
        if not self.broker.get_positions(self.symbol):
            self.trade()

    def trend(self):
        kma=talib.KAMA(self.bar.close,self.kma_time*16)
        close=self.bar.close
        return close[-1]>kma[-1]

    def on_trade(self,trade):
        position=self.broker.get_positions(self.symbol)
        if position:
            price=position.price
            side=position.direction
            if side==Direction.LONG:
                if trade.price-price>self.tp or price-trade.price>self.sl:
                    self.broker.close_position(position)

            else:
                if price-trade.price>self.tp or trade.price-price>self.sl:
                    self.broker.close_position(position)


    def update(self):
        tsi = pd.DataFrame()
        for s in self.symbols:
            self.bar[s]=self.broker.get_bar(s,self.timeframe)
            close=self.bar[s].close
            tsi[s]=self.tsi(close)

        print(tsi.tail())


    def tsi(self,data):
        a =talib.EMA(data,5)
        b = talib.EMA(data, 8)
        c = talib.EMA(data, 13)
        d = talib.EMA(data, 21)
        d1=a/b-1
        d2=b/c-1
        d3=c/d-1
        t=(d1+d2+d3)*1000
        return talib.EMA(t,6)


    def trade(self):
        rsi,k,d = talib.STOCHRSI(self.bar.close, self.rsi_time, self.rsi_fastk, self.rsi_fastd, self.rsi_fastd_matype);
        if self.trend():
            if crossover(k,d) and k <50:
                price=self.bar.close[-1]
                self.broker.buy(self.symbol,self.qty,price)
        else:
            if crossunder(k, d) and k > 50:
                price = self.bar.close[-1]
                self.broker.sell(self.symbol,self.qty,price)

    def on_order(self, event):
        pass
    def on_position(self, event):
        pass
    def on_ticker(self, event):
        pass

if __name__ == "__main__":

    ev = EventEngine()
    ev.start()
    main=SHstrategy(ev)
