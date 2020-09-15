# -*- coding:utf-8 -*-
"""
@Time : 2020/4/14 10:29 下午
@Author : Domionlu
@Site : 
@File : rabbitmq.py
"""
'''
Copyright (C) 2017-2020  Bryant Moscon - bmoscon@gmail.com

Please see the LICENSE file for the terms and conditions
associated with this software.
'''
import json
import asyncio

import pika
from FeedServer.mqevent import *
from FeedServer.log import log

from cryptofeed.backends.backend import BackendTickerCallback,BackendBookCallback,BackendBookDeltaCallback,BackendOpenInterestCallback

ev=EventServer()
class TickerRabbit(BackendTickerCallback):
    def __init__(self):
        self.numeric_type = float
    async def write(self, feed: str, pair: str, timestamp: float, receipt_timestamp: float, data: dict):
        try:
            if ev._connect.is_closed:
                ev.connect()
            key=pair.replace("-",".")
            e=Event(exchange="Ticker",routing_key=f"{feed}.{key}",data=data)
            ev.publish(e)
        except Exception as e:
            log.error(e)

class

class OrderbookRabbit(BackendBookCallback):
    def __init__(self):
        self.numeric_type = float
    async def write(self, feed: str, pair: str, timestamp: float, receipt_timestamp: float, data: dict):
        try:
            if ev._connect.is_closed:
                ev.connect()
            key=pair.replace("-",".")
            e=Event(exchange="OrderBook",routing_key=f"{feed}.{key}",data=data)
            ev.publish(e)
        except Exception as e:
            log.error(e)

class BookDeltaRabbit(BackendBookDeltaCallback):
    def __init__(self):
        self.numeric_type = float
    async def write(self, feed: str, pair: str, timestamp: float, receipt_timestamp: float, data: dict):
        try:
            if ev._connect.is_closed:
                ev.connect()
            key=pair.replace("-",".")
            e=Event(exchange="BookDelta",routing_key=f"{feed}.{key}",data=data)
            ev.publish(e)
        except Exception as e:
            log.error(e)
if __name__ == "__main__":
    pass