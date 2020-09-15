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

import talib

class Stcstrategy(BaseStrategy):

    def __init__(self, engine, setting):
        super().__init__(engine, setting)
        self.symbol=""
        self.kma_time=45
        self.rsi_time=14
        self.rsi_fastk=5
        self.rsi_fastd=3
        self.rsi_fastd_matype=0
        cfg=config.binance
        self.broker=BinanceFutures(cfg)
        self.symbol=cfg.symbol[0]
        self.timeframe="15m"
        self.qty=0.001
        self.bar=None
        self.tp=30.00
        self.sl=30.00
        RepeatingTimer(60, self.start).start()

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



if __name__ == "__main__":
    pass