import os
import sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

from apscheduler.schedulers.blocking import BlockingScheduler
from aq.engine.baseStrategy import BaseStrategy
from aq.common.logger import *
from aq.broker import BinanceFutures, Ftx
from aq.engine.event import EventEngine
from aq.common.message import Feishu
from aq.common.tools import *
from aq.indicator.base import *
from aq.indicator.rsi import *
from aq.engine.config import config
from aq.common.constant import *

class Grid(BaseStrategy):
    symbol="BTCUSDT"
    mid_price=0   # 最小二乘回归中线
    upper=0       #日线180天最高值
    lower=0       #日线180最低值


    def __init__(self, engine):
        super().__init__(engine)
        self.msg = Feishu()
        self.ev = engine
        long_cfg = config.long
        self.broker = BinanceFutures(self.ev, long_cfg.api_key, long_cfg.api_secret)
        self.register_event()
        self.broker.start(self.symbol)
        # self.broker.cancel_all_order(self.symbol)
        self.scheduler = BlockingScheduler()
        self.scheduler.add_job(self.on_bar, 'cron', minute="14,29,44,59", second="50")
        # self.scheduler.add_job(self.on_bar, 'cron', second="30")
        self.scheduler.add_job(self.broker.put_listenKey, 'interval', minutes=45)
        self.scheduler.start()

    def register_event(self):
        """"""
        self.ev.register(TICKER, self.on_ticker)
        self.ev.register(TRADE, self.on_trade)
        self.ev.register(ORDERBOOK, self.on_orderbook)
        self.ev.register(ORDER, self.on_order)
        self.ev.register(POSITION, self.on_position)
        self.ev.register(BALANCE, self.on_balance)

    def on_orderbook(self, event):
        pass
    def on_balance(self, event):
        pass

    def on_bar(self, event=None):
        pass

    def open_order(self, side):
        pass


if __name__ == "__main__":
    ev = EventEngine()
    ev.start()
    st = Grid(ev, None)
    while True:
        time.sleep(60)

