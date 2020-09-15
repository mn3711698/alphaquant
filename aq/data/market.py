# -*- coding:utf-8 -*-
"""
@Time : 2020/4/14 9:57 下午
@Author : Domionlu
@Site :
@File : market.py
"""
# -*- coding:utf-8 -*-

"""
Market module.

Author: HuangTao
Date:   2019/02/16
Email:  huangtao@ifclover.com
"""

import json


from aq.common.logger import log
from aq.engine.mqevent import *
import time
from multiprocessing import Process
import threading
import traceback

def tickcallback(ch, method, properties, data):
    e=Event()
    e.loads(data)

def orderbookcallback(ch, method, properties, data):
    e=Event()
    e.loads(data)
    log.info(e.routing_key)

class Market():
    def __init__(self, market_type, platform, symbol, callback):
        t=threading.Thread(target=self.subscribe, args=(market_type, platform, symbol, callback))
        t.start()
    def subscribe(self,market_type, platform, symbol, callback):
        try:
            self.ev = EventServer()
            symbol=symbol.replace("-",".")
            key = f"{platform}.{symbol}"
            self.ev.subscribe(market_type, callback, key)
            log.info(f"{market_type},{key},订阅成功！")
        except Exception as e:
            log.error(e)
            traceback.format_exc()

if __name__ == "__main__":
        Market("OrderBook","BINANCE_FUTURES","BTC-USDT",orderbookcallback)
        Market("OrderBook", "FTX", "BTC-PERP", orderbookcallback)
        while True:
            time.sleep(1)



