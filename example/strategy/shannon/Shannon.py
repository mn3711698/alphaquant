import os
import sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

from apscheduler.schedulers.blocking import BlockingScheduler
from aq.engine.baseStrategy import BaseStrategy
from aq.common.logger import *
from aq.broker import Binance
from aq.engine.event import EventEngine
from aq.common.message import Feishu
from aq.common.tools import *
from aq.indicator.base import *
from aq.indicator.rsi import *
from aq.engine.config import config
from aq.common.constant import *
from collections import deque
import numpy as np
from aq.engine.autoreload import run_with_reloader


class Shannon(BaseStrategy):
    symbol = "BTCUSDT"
    ratio=0.5


    def __init__(self, engine, setting):
        super().__init__(engine, setting)
        self.ev = engine
        self.bar = deque(maxlen=1440)
        cfg = config.long
        self.broker = Binance(self.ev, cfg.api_key, cfg.api_secret)
        self.broker.start(self.symbol, [KLINE5])
        self.register_event()



    def register_event(self):
        """"""
        # self.ev.register(TICKER, self.on_ticker)
        self.ev.register(FORCEORDER, self.on_forceorder)
        # self.ev.register(TRADES, self.on_trade)
        self.ev.register(KLINE, self.on_bar)



    def check_balance(self):
        balance=self.broker.get_balnce()


    def on_ticker(self, event):
        pass

    def on_trade(self, event):
        data = event.data
        print(data)

    def on_orderbook(self, event):
        pass

    def on_position(self, event):
        data = event.data
        log.info(f"持仓更新 {data}")
        self.position = self.broker.get_positions(self.symbol)

    def on_order(self, event):
        data = event.data
        log.info(f"订单更新 {data}")
        self.position = self.broker.get_positions(self.symbol)

    def on_balance(self, event):
        pass



    def on_bar(self, event=None):
        data = event.data
        data = data['k']

        n = data['n']  # 这根K线是否完结(是否已经开始下一根K线

        t = data['t']
        next = data['x']


        # [1594988400000, 9178.42, 9182.3, 9170.0, 9174.96, '1072.141', 1594988699999, '9837139.22509', 3159, '473.257',
        #  '4342571.91987', '0']
        # {'t': 1594995900000, 'T': 1594996199999, 's': 'BTCUSDT', 'i': '5m', 'f': 163202496, 'L': 163204715,
        #  'o': '9151.47', 'c': '9143.34', 'h': '9151.57', 'l': '9140.51', 'v': '970.103', 'n': 2220, 'x': True,
        #  'q': '8871138.11349', 'V': '236.435', 'Q': '2162196.58503', 'B': '0'}

        t = [data['t'], float(data['o']), float(data['h']), float(data['l']), float(data['c']), float(data['v']),
             data['q'], data['v'], data['n'], data['V'], data['Q'], data["B"]]
        # if self.sig>0.85:
        #     log.info(f"当前K线交易数: {n}")
        #     log.info(f"当前sig: {self.sig}")
        #     log.info(f"预计sig: {self.varsig}")
        #     log.info(f"当前价格：{data['c']}")
        if next:
            self.bar.append(t)



    def open_order(self, side):
        position = self.broker.get_positions(self.symbol)
        log.info(f"当前持仓{position}")
        if side == BUY:
            o = self.broker.buy(self.symbol, self.qty)
            log.info(f"买单：{o}")
            self.position = self.broker.get_positions(self.symbol)
            log.info(f"当前持仓{position}")
        else:
            o = self.broker.sell(self.symbol, self.qty)
            log.info(f"卖单：{o}")
            self.position = self.broker.get_positions(self.symbol)
            log.info(f"当前持仓{position}")


def main():
    ev = EventEngine()
    ev.start()
    st = Shannon(ev, None)


if __name__ == "__main__":
    main()