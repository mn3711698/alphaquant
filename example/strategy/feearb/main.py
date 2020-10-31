# -*- coding:utf-8 -*-
"""
@Time : 2020/5/9 12:02 上午
@Author : Domionlu
@Site : 
@File : main.py
"""
from aq.engine.baseStrategy import BaseStrategy
from aq.broker.binancefutures import BinanceFutures
from aq.broker.huobi import HuobiFutures
from aq.backtest.hist_data.config import config
from aq.indicator.base import *
from aq.common.utility import RepeatingTimer
from aq.common.constant import *
from aq.engine.event import EventEngine

import talib

class Feeabrstrategy(BaseStrategy):
    """
    资金费率套利
    从二个市场或多个市场出找出费率差最大的交易对
    买入费率低的，卖出费率高的交易对
    定时调整二个账户的资金余额
    """

    def __init__(self, engine):
        super().__init__(engine)
        self.ev = engine
        cfg=config.short
        self.short=BinanceFutures(self.ev)
        self.long=HuobiFutures(self.ev)




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

    def on_order(self, event):
        pass
    def on_position(self, event):
        pass
    def on_ticker(self, event):
        pass

    def get_fee(self):
        short=self.short.get_fees()
        long=self.long.get_fees()
        data=[]
        for l in long:
            symbol=l.split("-")[0]+"USDT"
            r=short.get(symbol,0)
            if r!=0:
                rs=[l,long[l],r]
                data.append(rs)
        df=pd.DataFrame(data)
        df.columns=["symbil","huobi","binance"]
        df["dif"]=df["huobi"]-df["binance"]




if __name__ == "__main__":

    ev = EventEngine()
    ev.start()
    main=Feeabrstrategy(ev)
    main.get_fee()

