import os
import sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

from apscheduler.schedulers.blocking import BlockingScheduler
from aq.engine.baseStrategy import BaseStrategy
import talib
import numpy as np
from aq.common.logger import *
from aq.indicator.base import polyslope
from aq.common.utility import RepeatingTimer
from aq.broker import BinanceFutures, Ftx
from aq.engine.event import EventEngine
from aq.common.message import Feishu
from aq.common.tools import *
from aq.indicator.base import *


class VV(BaseStrategy):
    author = "用Python的交易员"
    strategy_name ="VV"
    fast_window = 10
    slow_window = 20
    fast_ma0 = 0.0
    fast_ma1 = 0.0
    slow_ma0 = 0.0
    slow_ma1 = 0.0
    parameters = ["fast_window", "slow_window"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]
    symbol="BTCUSDT"

    def __init__(self, engine, setting):
        super().__init__(engine, setting)
        self.msg=Feishu()
        self.ev = EventEngine()
        self.broker = BinanceFutures(self.ev)
        self.scheduler = BlockingScheduler()
        self.scheduler.add_job(self.on_bar, 'cron', minute="*/1",second="30")
        # self.scheduler.add_job(self.on_bar, 'cron', minute="14,29,44,59")
        # self.scheduler.add_job(self.on_bar, 'cron', second="14,29,44,59")

        # RepeatingTimer(60,self.on_bar).start()#每秒检查下次挂单情况
        self.scheduler.start()

    def on_bar(self, event=None):
        log.info("开始任务")
        bar_15m=self.broker.get_bar(self.symbol,"15m")
        close_15m=bar_15m["close"]
        bar_4h=self.broker.get_bar(self.symbol,"4h")
        close_4h=bar_4h["close"]
        fastk_4h, fastd_4h = StochRSI(close_4h, smoothK=3,smoothD=3,lengthRSI=7,lengthStoch=5)
        fastk, fastd = StochRSI(close_15m, smoothK=3,smoothD=3,lengthRSI=7,lengthStoch=5)

        if fastk_4h[-1]>fastd_4h[-1] and fastk_4h[-1]>fastk_4h[-2] and fastd_4h[-1]>fastd_4h[-2]:
            log.info(f"4小时k:{fastk_4h[-1]},d:{fastd_4h[-1]},15分钟k:{fastk[-1]},d:{fastd[-1]}，趋势向上")
            if crossover(fastk,fastd) and fastk[-1]>20:
                msg=f"当前时间:{get_datetime()}\n趋势：向上\n当前价格{list(close_15m)[-1]}\n策略：买入"
                self.msg.send("日内震荡策略",msg)
                log.info(msg)
        elif fastk_4h[-1]<fastd_4h[-1] and fastk_4h[-1]<fastk_4h[-2] and fastd_4h[-1]<fastd_4h[-2]:
            log.info(f"4小时k:{fastk_4h[-1]},d:{fastd_4h[-1]},15分钟k:{fastk[-1]},d:{fastd[-1]}，趋势向下")
            if crossunder(fastk, fastd)and fastk[-1]<80:
                msg=f"当前时间:{get_datetime()}\n趋势：向下\n当前价格{list(close_15m)[-1]}\n策略：卖出"
                self.msg.send("日内震荡策略",msg)
                log.info(msg)

    def on_order(self,event):
        pass
    def on_position(self,event):
        pass
    def on_ticket(self,event):
        pass
    def on_trade(self,event):
        pass
if __name__ == "__main__":
    ev=EventEngine()
    st = DoubleRsi(ev,None)
    while True:
        time.sleep(60)