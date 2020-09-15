# -*- coding:utf-8 -*-
"""
@Time : 2020/4/25 9:55 上午
@Author : Domionlu
@Site :
@File : spreed_influx.py
"""
import os,sys
baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

from aq.data.market import Market
from aq.common.logger import log
from aq.engine.mqevent import Event
from aq.engine.event   import EventEngine
from aq.broker.binancefutures import BinanceFutures
from aq.common.constant import *
from aq.data.MongoDataSerer import db
from  aq.common.tools import *
import pandas as pd
import time
from aq.common.utility import RepeatingTimer


class Forceorder():
    def __init__(self):
        self.ev=EventEngine()
        self.ev.start()
        self.broke=BinanceFutures(self.ev)
        self.broke.start("btcusdt",[FORCEORDER])
        self.ev.register(FORCEORDER, self.callback)

    def callback(self,event):
        """
        {'e': 'forceOrder', 'E': 1594107015086,
        'o': {'s': 'BTCUSDT',
        'S': 'SELL',
        'o': 'LIMIT',
        'f': 'IOC',
        'q': '1.300',
        'p': '9206.39',
        'ap': '9242.01',
        'X': 'FILLED',
        'l': '1.084',
        'z': '1.300',
        'T': 1594107015081}}

        :param event:
        :return:
        """
        e=event.data
        try:
            data=e["o"]
            db.insert_one("forceorder",data)
        except Exception as e:
            log.debug(e)


if __name__ == "__main__":
        od=Forceorder()
        # while True:
        #     time.sleep(1)