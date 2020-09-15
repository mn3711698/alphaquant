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
from aq.engine.log import log
from aq.engine.mqevent import Event
from aq.engine.event   import EventEngine
from aq.broker.binancefutures import BinanceFutures
from aq.broker.ftx import Ftx
from aq.data.MongoDataSerer import db
from  aq.common.tools import *
import time
from aq.common.utility import RepeatingTimer
import traceback

class Orderbook():
    def __init__(self):
        self.ev=EventEngine()
        self.maker=BinanceFutures(self.ev)
        self.taker=Ftx(self.ev)
        self.maker_price=0
        self.taker_price=0
        self.data=[]
        RepeatingTimer(1,self.savedb).start()

    def savedb(self):
        t=time.time()
        log.info(f"spreed:{self.taker_price},{self.maker_price}")
        if not self.taker_price==0 and not self.maker_price==0:
            try:
                db.insert_one("spreed", {"symbol": "BTCUSDT",
                                     "timestamp": get_cur_timestamp_ms(),
                                     "makerprice":  self.maker_price,
                                     "takerprice":  self.taker_price})
                log.info(f"spreed:{self.taker_price},{self.maker_price}")
            except Exception as e:
                log.error(traceback.format_exc())



    def callback(self,ch, method, properties, data):
        e=Event()
        e.loads(data)
        if "BINANCE_FUTURES" in e.routing_key:
            self.maker.bid=e.data["bid"]
            self.maker.ask=e.data["ask"]
            bid = float(list(self.maker.bid.keys())[0])
            ask = float(list(self.maker.ask.keys())[0])
            self.maker_price= round((bid+ask) / 2,4)
        elif "FTX" in e.routing_key:
            self.taker.bid = e.data["bid"]
            self.taker.ask = e.data["ask"]
            bid = float(list(self.taker.bid.keys())[0])
            ask = float(list(self.taker.ask.keys())[0])
            self.taker_price = (bid+ask) / 2


if __name__ == "__main__":

        od=Orderbook()
        Market("OrderBook","BINANCE_FUTURES","BTC-USDT",od.callback)
        Market("OrderBook", "FTX", "BTC-PERP", od.callback)
        while True:
            time.sleep(1)
