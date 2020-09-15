#!/usr/bin/env python
# encoding: utf-8

"""
@version: python3.8
@Author  : Dominolu
@Explain :
@Time    : 2020/7/30 14:23
@File    : ht
"""
import os
import sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

from aq.data.market import Market
from aq.engine.baseStrategy import BaseStrategy
from aq.broker import BinanceFutures
from aq.engine.event import EventEngine
from aq.common.logger import log
from aq.engine.config import Config
from aq.engine.mqevent import Event
from collections import deque
from aq.common.constant import *
import time
import numpy as np
import pandas as pd
from aq.common.tools import *
import click

class HtStrategy(BaseStrategy):
    alert="HT"
    timeframe="15m"
    symbol="BTCUSDT"
    # tp=100
    # sl=20
    # qty=0.001
    def __init__(self, engine, setting):
        super().__init__(engine, setting)
        self.ev = engine
        cfg=Config(setting)
        broker = cfg.broker
        self.tp=broker.tp
        self.sl=broker.sl
        self.qty=broker.qty
        self.symbol=broker.symbol
        self.timeframe=broker.timeframe
        self.data=deque(maxlen =1000)
        self.bar=deque(maxlen =100)
        self.broker = BinanceFutures(self.ev, broker.api_key, broker.api_secret)
        Market("Alert", "BINANCE",self.symbol, self.callback)
        self.broker.start(self.symbol, [TRADES])
        self.register_event()
        self.price=0
        self.status=True
        self.lowprice=0
        self.highprice=0
        self.position=[]
        log.info("HT策略已启动。。。")
        log.info(f"symbol:{self.symbol},qty:{self.qty},timeframe:{self.timeframe},tp:{self.tp},sl:{self.sl}")
        self.loop()

    def register_event(self):
        """"""
        # self.ev.register(TICKER, self.on_ticker)
        # self.ev.register(FORCEORDER, self.on_forceorder)
        self.ev.register(TRADES, self.on_trade)
        # self.ev.register(KLINE,self.on_bar)


    def callback(self,ch, method, properties, data):
        e = Event()
        e.loads(data)
        data=e.data
        if data["alert"]==self.alert and data["timeframe"]==self.timeframe:
            log.info(data)
            if len(self.data)>1:
                ht=self.data[-1]["ht"]
                newht=data["ht"]
                if ht>0 and newht<0:
                    self.open_order("SELL")
                if ht<0 and newht>0:
                    self.open_order("BUY")
            self.data.append(data)

    def open_order(self, side):
        position = self.broker.get_positions(self.symbol)
        if len(position)>0:
            pos=position[0]
            if (pos.direction==Direction.LONG and side==SELL) or (pos.direction==Direction.SHORT and side==BUY):
                o = self.broker.close_position(pos)
                log.info(f"止损平仓：{o}")
                time.sleep(0.5)
                self.position = self.broker.get_positions(self.symbol)

        if side == BUY:
            o = self.broker.buy(self.symbol, self.qty)
            log.info(f"买单：{o}")
            time.sleep(0.5)
            self.position = self.broker.get_positions(self.symbol)
            log.info(f"当前持仓{self.position}")

        else:
            o = self.broker.sell(self.symbol, self.qty)
            log.info(f"卖单：{o}")
            time.sleep(0.5)
            self.position = self.broker.get_positions(self.symbol)
            log.info(f"当前持仓{self.position}")
        # self.get_price()

    def loop(self):
        while self.status:
            log.info(f"当前价格 {self.price}")
            log.info(f"当前持仓{self.position}")
            time.sleep(60*5)

    def check_position(self):
        if self.status:
            # log.info(self.price)
            if len(self.position) > 0:
                p = self.position[0]
                if p.direction == Direction.LONG:
                    if self.highprice<self.price:
                        self.highprice=self.price

                    if self.price - p.price > self.tp:
                        log.info(f"多单,成本价{p.price},当前价{self.price},止盈{self.tp},持仓最高价{self.highprice}")
                        log.info(f"多单盈利{self.price - p.price}")
                        o = self.broker.close_position(p)
                        log.info(f"止盈平仓：{o}")
                        self.position = self.broker.get_positions(self.symbol)

                    if self.highprice - self.price > self.sl:
                        log.info(f"多单,成本价{p.price},当前价{self.price},止盈{self.tp},持仓最高价{self.highprice}")
                        log.info(f"多单移动止损{self.price - p.price}")
                        o = self.broker.close_position(p)
                        log.info(f"止损平仓：{o}")
                        self.position = self.broker.get_positions(self.symbol)
                else:
                    if self.lowprice>self.price or self.lowprice==0:
                        self.lowprice=self.price

                    if p.price - self.price > self.tp:
                        log.info(f"空单,成本价{p.price},当前价{self.price},止盈{self.tp},持仓最低价{self.lowprice}")
                        log.info(f"空单盈利{p.price - self.price}")
                        o = self.broker.close_position(p)
                        log.info(f"止盈平仓：{o}")
                        self.position = self.broker.get_positions(self.symbol)

                    if self.price - self.lowprice > self.sl:
                        log.info(f"空单,成本价{p.price},当前价{self.price},止盈{self.tp},持仓最低价{self.lowprice}")
                        log.info(f"空单移动止损{p.price - self.price}")
                        o = self.broker.close_position(p)
                        log.info(f"止损平仓：{o}")
                        self.position = self.broker.get_positions(self.symbol)
                # if self.move_tp(p.direction, price, p.price):
                #     o = self.broker.close_position(p)
                #     log.info(f"移动止盈：{o}")



    def on_ticker(self, event):
        pass


    def on_trade(self, event):
        data=event.data
        self.price=float(data["p"])
        self.check_position()

    def on_orderbook(self, event):
        pass

    def on_bar(self,event):
        data = event.data
        data = data['k']
        self.price=float(data['c'])
        log.info(data)
        if data['x']:
            self.bar.append(data)
        self.check_position()


    def get_price(self):
        if len(self.bar)>3:
            # bar=list(self.bar)
            bar=pd.DataFrame(self.bar).tail(3)
            high=float(bar["h"].values)
            low=float(bar["l"].values)
            self.highprice=np.max(high)
            self.lowprice=np.min(low)
        else:
            self.highprice=0
            self.lowprice=0
            # print(self.highprice,self.lowprice)


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

@click.command()
@click.option('--cfg', default="config.json", help='config file')
def main(cfg):
    ev = EventEngine()
    ev.start()
    st = HtStrategy(ev, cfg)


if __name__ == "__main__":
    main()
