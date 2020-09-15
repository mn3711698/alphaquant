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


from FeedServer.log import log
from FeedServer import const
from FeedServer.mqevent import *
import time
from multiprocessing import Process

class Orderbook:

    """ Orderbook object.

    Args:
        platform: Exchange platform name, e.g. binance/bitmex.
        symbol: Trade pair name, e.g. ETH/BTC.
        asks: Asks list, e.g. [[price, quantity], [...], ...]
        bids: Bids list, e.g. [[price, quantity], [...], ...]
        timestamp: Update time, millisecond.
    """

    def __init__(self, platform=None, symbol=None, asks=None, bids=None, timestamp=None):
        """ Initialize. """
        self.platform = platform
        self.symbol = symbol
        self.asks = asks
        self.bids = bids
        self.timestamp = timestamp

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "symbol": self.symbol,
            "asks": self.asks,
            "bids": self.bids,
            "timestamp": self.timestamp
        }
        return d

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)


class Trade:
    """ Trade object.

    Args:
        platform: Exchange platform name, e.g. binance/bitmex.
        symbol: Trade pair name, e.g. ETH/BTC.
        action: Trade action, BUY or SELL.
        price: Order place price.
        quantity: Order place quantity.
        timestamp: Update time, millisecond.
    """

    def __init__(self, platform=None, symbol=None, action=None, price=None, quantity=None, timestamp=None):
        """ Initialize. """
        self.platform = platform
        self.symbol = symbol
        self.action = action
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "symbol": self.symbol,
            "action": self.action,
            "price": self.price,
            "quantity": self.quantity,
            "timestamp": self.timestamp
        }
        return d

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)


class Kline:
    """ Kline object.

    Args:
        platform: Exchange platform name, e.g. binance/bitmex.
        symbol: Trade pair name, e.g. ETH/BTC.
        open: Open price.
        high: Highest price.
        low: Lowest price.
        close: Close price.
        volume: Total trade volume.
        timestamp: Update time, millisecond.
        kline_type: Kline type name, kline - 1min, kline_5min - 5min, kline_15min - 15min.
    """

    def __init__(self, platform=None, symbol=None, open=None, high=None, low=None, close=None, volume=None,
                 timestamp=None, kline_type=None):
        """ Initialize. """
        self.platform = platform
        self.symbol = symbol
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.timestamp = timestamp
        self.kline_type = kline_type

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "symbol": self.symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timestamp": self.timestamp,
            "kline_type": self.kline_type
        }
        return d

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)


class Market_old:
    """ Subscribe Market.

    Args:
        market_type: Market data type,
            MARKET_TYPE_TRADE = "trade"
            MARKET_TYPE_ORDERBOOK = "orderbook"
            MARKET_TYPE_KLINE = "kline"
            MARKET_TYPE_KLINE_5M = "kline_5m"
            MARKET_TYPE_KLINE_15M = "kline_15m"
        platform: Exchange platform name, e.g. binance/bitmex.
        symbol: Trade pair name, e.g. ETH/BTC.
        callback: Asynchronous callback function for market data update.
                e.g. async def on_event_kline_update(kline: Kline):
                        pass
    """

    def __init__(self, market_type, platform, symbol, callback):
        """ Initialize. """
        if platform == "#" or symbol == "#":
            multi = True
        else:
            multi = False
        if market_type == const.MARKET_TYPE_ORDERBOOK:
            from FeedServer.rqevent import EventOrderbook
            EventOrderbook(platform, symbol).subscribe(callback, multi)
        elif market_type == const.MARKET_TYPE_TRADE:
            from FeedServer.rqevent import EventTrade
            EventTrade(platform, symbol).subscribe(callback, multi)
        elif market_type in [const.MARKET_TYPE_KLINE, const.MARKET_TYPE_KLINE_5M, const.MARKET_TYPE_KLINE_15M]:
            from FeedServer.rqevent import EventKline
            EventKline(platform, symbol, kline_type=market_type).subscribe(callback, multi)
        else:
            log.error("market_type error:", market_type, caller=self)

def tickcallback(ch, method, properties, data):
    e=Event()
    e.loads(data)
    log.info(f"Tick data:{e.data}")

def orderbookcallback(ch, method, properties, data):
    e=Event()
    e.loads(data)
    log.info(f"Orderbook data:{e.data}")

class Market():

    def __init__(self, market_type, platform, symbol, callback):
        p=Process(target=self.subscribe,args=(market_type, platform, symbol, callback))
        p.start()

    def subscribe(self,market_type, platform, symbol, callback):
        self.ev = EventServer()
        key = f"{platform}.{symbol}"
        self.ev.subscribe(market_type, callback, key)
        log.info(f"{market_type},{key},订阅成功！")

if __name__ == "__main__":
        Market("Ticker","COINBASE","BTC.USD",tickcallback)
        Market("Orderbook", "COINBASE", "BTC.USD", orderbookcallback)
        while True:
            time.sleep(1)



