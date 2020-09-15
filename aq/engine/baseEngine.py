# -*- coding:utf-8 -*-
"""
@Time : 2020/3/16 12:12 上午
@Author : Domionlu
@Site : 
@File : baseEngine.py
@Software: PyCharm
"""
import traceback

from aq.engine.event import EventEngine
from aq.common.constant import *
from aq.engine.baseStrategy import BaseStrategy
from typing import Any, Callable
from aq.common import logger


def call_strategy_func(strategy:BaseStrategy, func: Callable, params: Any = None):
    """
    Call function of a strategy and catch any exception raised.
    """
    try:
        if params:
            func(params)
        else:
            func()
    except Exception:
        strategy.trading = False
        strategy.inited = False
        msg = f"触发异常已停止\n{traceback.format_exc()}"
        logger(msg, strategy)


class BaseEngine():

    def __init__(self):
        self.event=EventEngine()
        self.strategy=None

    def run(self):
        self.register_event()

    def register_event(self):
        """"""
        self.event.register(EventType.TICKER, self.process_ticket_event)
        self.event.register(EventType.ORDER, self.process_order_event)
        self.event.register(EventType.TRADE, self.process_trade_event)
        self.event.register(EventType.POSITION, self.process_position_event)

    def process_bar_event(self, event):
        strategy = self.strategy
        call_strategy_func(strategy, strategy.on_bar, event)

    def process_ticket_event(self,event):
        strategy = self.strategy
        call_strategy_func(strategy, strategy.on_ticket, event)

    def process_order_event(self, event):
        strategy = self.strategy
        call_strategy_func(strategy, strategy.on_order, event)

    def process_trade_event(self, event):
        strategy = self.strategy
        call_strategy_func(strategy, strategy.on_trade, event)

    def process_position_event(self,event):
        strategy=self.strategy
        call_strategy_func(strategy,strategy.on_position,event)


if __name__ == "__main__":
    pass