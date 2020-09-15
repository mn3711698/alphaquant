# -*- coding: utf-8 -*-
# @Time : 2020/3/15 9:27 下午
# @Author : Aries
# @Site :
# @File : sta.py
# @Software: PyCharm
from aq.common.object import *
from aq.engine.baseStrategy import BaseStrategy
import talib
import numpy as np
from aq.common.logger import *
from aq.indicator.base import polyslope

class TrendStrategy(BaseStrategy):
    author = "用Python的交易员"
    strategy_name ="Trend"
    fast_window = 10
    slow_window = 20
    fast_ma0 = 0.0
    fast_ma1 = 0.0
    slow_ma0 = 0.0
    slow_ma1 = 0.0
    parameters = ["fast_window", "slow_window"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]
    symbol="BTC/USDT"

    def __init__(self, engine, setting):
        super().__init__(engine, setting)
        self.symbol="BTC/USDT"

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        log.info("策略初始化")

    def on_start(self):
        """
        Callback when strategy is started.
        """
        log.info("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        log.info("策略停止")

    def on_tick(self):
        """
        Callback of new tick data update.
        """
        pass

    def on_bar(self, data):
        """
        Callback of new bar data update.
        """
        self.broker.add_bar(data)

        bar = self.broker.get_bar()
        if len(bar) < 10:
            return
        pos = self.broker.get_positions()
        b7=polyslope(bar['close'],7)
        b56=polyslope(bar['close'],56)


        if cross_over and pos ==0:
            self.broker.buy(symbol="BTC/USDT",price=data.close, volume=1)

        elif cross_below and pos > 0:

            self.broker.sell(symbol="BTC/USDT",price=data.close, volume=1)

    def on_order(self, event):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, event):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_position(self, event):
        """
        Callback of stop order update.
        """
        pass

    def on_ticket(self, event):
        pass

    def put_event(self):
        pass