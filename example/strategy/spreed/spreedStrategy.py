# -*- coding:utf-8 -*-
"""
@Time : 2020/4/27 8:44 下午
@Author : Domionlu
@Site : 
@File : spreedStrategy.py
"""
import os, sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

from aq.data.market import Market
from aq.engine.log import log
from aq.engine.mqevent import Event
from aq.engine.event import EventEngine
from aq.broker import BinanceFutures, Ftx
from aq.common.constant import *
from aq.engine.baseStrategy import BaseStrategy
from aq.engine.config import config
from aq.common.tools import *
import pandas as pd
from aq.engine.baseBroke import BaseBroker
from aq.common.object import Position
from aq.common.utility import RepeatingTimer
import time


class SpreedStrategy(BaseStrategy):
    """"
    利用二个永续合约交易所的价格波动率进行配对套利
    利用价差在超过一定阀值之后开仓配对
    开仓配对的方式利用一边maker=taker+-点差(主要是能覆盖二边开仓的手续费)的方式开仓
    等从价差收敛之后平仓，平仓方式同开仓也是maker平仓=taker+-点差
    maker方要流动性好，交易量大，波动性大，最好有返利，taker要有深度，手续费便宜
    """
    spreed: int = 20
    offset: int = 1.5  # 目标是几倍标准差

    long_price: float = 0
    short_price: float = 0
    qty: float = 0.0001  # 前期使用最小单位，实盘稳定之后再考虑根据资金调配仓位
    long_position: Position
    short_position: Position
    order: {}

    def __init__(self, engine, setting=None):
        super().__init__(engine, setting)
        self.ev = EventEngine()
        self.data = []
        self.short: None
        self.long: None
        self.fee = 0.001  # 挂单价格增加手续费
        # todo 下单数量可以调整为根据盘口以及当前的持仓比例来控制，价差扩大，持仓未达上线，可以增仓
        self.qty = 0.001  # 下单BTC数量 反向合约需要换算
        self.spreed_position = 0
        self.status = False
        self.spreed_status = 0 #0 没有开仓，没有开单 1 long挂单，short未开单，2 long or short成交有持仓，等待对冲，3 对冲成功，等待回归平仓套利 4 long挂单平仓，5，long平仓，待short对冲平仓
        RepeatingTimer(1, self.check_order).start()  # 每秒检查下次挂单情况

    def init(self):
        # 订阅orderbook行情

        long_cfg = config.long
        short_cfg = config.short
        long_param = {"orders": self.on_order, "fills": self.on_order}
        short_param = {"orders": self.on_order}
        # 连接交易所并订阅订单状态
        self.long = BinanceFutures(self.ev, long_cfg.api_key, long_cfg.api_secret)
        self.long.subscribe(long_param, long_cfg.symbols)
        self.long.symbol = long_cfg.symbols[0]
        self.short = Ftx(self.ev, short_cfg.api_key, short_cfg.api_secret)
        self.short.subscribe(short_param, short_cfg.symbols)
        self.short.symbol = short_cfg.symbols[0]
        self.long.cancel_all_order(self.long.symbol)
        self.short.cancel_all_order(self.short.symbol)
        Market("OrderBook", "BINANCE_FUTURES", "BTC-USDT", self.on_orderbook)
        Market("OrderBook", "FTX", "BTC-PERP", self.on_orderbook)

    def on_orderbook(self,ch, method, properties, data):
        e = Event()
        e.loads(data)
        if self.long.name in e.routing_key:
            self.long.update_orderbook(e.data)

        elif self.short.name in e.routing_key:
            self.short.update_orderbook(e.data)

        if not self.short.mid_price == 0 and not self.long.mid_price == 0:
            self.status = True
            self.start()

    def on_ticket(self, event):
        pass

    def start(self):
        """"
        spreed_status
        0.未开仓，挂单，
        1.long挂单，
        2.long挂单成交，short未成功，
        3.配对成功，maker挂单平仓，
        4.long平仓成功，short未成功
        5.long开仓成功，short未成功，取消maker???

        #根据short的买卖单挂单在maker上
        #short的买一*(1-spreed),卖-*(1+spreed)
        """""
        spreed = self.long.mid_price > self.short.mid_price
        # 当前没有开仓状态，判断价差是超过目标值，则进行开仓
        if self.spreed_status == 0:
            if spreed:
                # 卖入long,买入short
                self.long_price = self.short.bid_price + self.spreed
                if self.long_price < self.long.ask_price:
                    self.long_price = self.long.ask_price
                self.short_price = self.short.bid_price

            else:
                # 买入long,卖出short
                self.long_price = self.short.bid_price + self.spreed
                if self.long_price > self.long.bid_price:
                    self.long_price = self.long.bid_price
                self.short_price = self.short.ask_price
            self.open_spreed()
        # elif self.spreed_status == 1:
        #     self.check_maker()  # 跟随taker挂maker的单，以保持足够的差价
        # elif self.spreed_status == 2:
        #     self.close_spreed()  # maker成交后马上在taker成交，如果有点差后期考虑，考虑使用IOC
        # elif self.spreed_status == 3:
        #     self.wait_spreed(BUY)
        # elif self.spreed_status == 4:
        #     # 等待缩小差价？
        #     # 二边同时挂maker订单
        #     pass

    def open_spreed(self):
        """
        合成一个配对交易，交易信号由策略完成，
        合成模式：
        1 先maker被动待成交，后再主动taker另一个交易对，被动市场优先选择流动高，有返利，深度可以差一点，主动市场优先选择有深度，手续费优惠
        2 二边都主动taker，先吃深度差，流动性差的一边，再吃深度好，流动性的一边，
        规则目标：防止合成不成功
        :param
        side:主动腿-被动腿<0:买入主动腿，卖出被动腿，主动腿-被动腿>0:卖出主动腿，买入被动腿
        type:abs(主动腿-被动腿)>spreed:同时taker,abs(主动腿-被动腿)<spreed:maker主动腿，taker被动腿
        :return:
        """
        side = (self.long_price - self.short_price) > 0
        type = abs(self.long_price - self.short_price) > self.spreed
        if type:
            # 价差超过spreed,直接二边taker下单
            if side:
                long_order = self.long.sell(self.long.symbol, self.qty)
                short_order = self.short.buy(self.short.symbol, self.qty)
            else:
                long_order = self.long.buy(self.long.symbol, self.qty)
                short_order = self.short.sell(self.short.symbol, self.qty)

            self.order[long_order.order_id] = long_order
            self.order[short_order.order_id] = short_order
            if self.hedage():
                self.spreed_status = 3 #开仓对冲成功
            else:
                self.spreed_status=0 #对冲失败，重新开始
        else:
            # 价差未超过spreed,long maker
            if side:
                order = self.long.sell(self.long.symbol,self.qty, self.long_price )
            else:
                order = self.long.buy(self.long.symbol, self.qty,self.long_price)
            if order:
                self.order[order.order_id] = order
                self.spreed_status=1


    def hedage(self):
        """
        执行三次对冲，否则取消所有挂单，所有持仓
        """
        i = 0
        while i < 3:
            self.update_postion()
            if not self.long_position and self.short_position:
                # short已成交且有持仓，long没有成交
                if self.spreed_status==1:
                    self.spreed_status = 2
                else:
                    self.spreed_status=5
                side = self.short_position.side
                qty = self.short_position.qty
                if side == BUY:
                    order = self.long.sell(self.long.symbol, qty)
                else:
                    order = self.long.buy(self.long.symbol, qty)

                self.order[order.order_id] = order

            if self.short_position and self.long_position:
                if self.spreed_status == 1:
                    self.spreed_status = 2
                else:
                    self.spreed_status = 5
                # long已成交且有持仓，short没有成交
                side = self.long_position.side
                qty = self.long_position.qty
                if side == BUY:
                    order = self.short.sell(self.short.symbol, qty)
                else:
                    order = self.short.buy(self.short.symbol, qty)
                self.order[order.order_id] = order

            if self.short_position and self.long_position:
                i = 3
                return True
            else:
                i += 1
        # todo 3次失败之后，执行取消订单，全部平仓
        #self.close_spreed()
        return False
        # if side==BUY:
        #     price=self.short.bid.price
        #     delta=(self.short_price-price)/self.short_price
        #     if abs(delta)<0.0001 or delta<0:
        #         #差小于万1，或最新short买一价格高于委托价格则进行买入
        #         order = self.short.sell(self.short.symbol, qty)
        #     else:
        #         # 最新short买一价格低于委托价格并超过万1幅度
        #         self.close_positon(self.long_position)
        # else:
        #     price = self.short.ask.price
        #     delta = (self.short_price - price) / self.short_price
        #     if abs(delta) < 0.0001 or delta > 0:
        #         #偏差小于万1，或最新short卖一价格低于委托价格则进行买入
        #         order = self.short.buy(self.short.symbol, qty)
        #     else:
        #         #最新short卖一价格高于委托价格并超过万1幅度
        #         self.close_positon(self.long_position)

    def check_order(self):
        if self.spreed_status==1 or self.spreed_status==4:
            # 检查订单委托情况，如果没有成交且波动超过万2，则重新进行挂单
            order = self.order[self.order.key()[0]]
            if order.side == BUY:
                delta = (order.price - self.short.ask_price - self.spreed) / order.price
                if delta > 0.0002:
                    self.long.cancel_order(self.long.symbol, order.order_id)
                    self.spreed_status=0
            else:
                delta = (order.price - self.short.bid_price - self.spreed) / order.price
                if delta > 0.0002:
                    self.long.cancel_order(self.long.symbol, order.order_id)
                    self.spreed_status=0

        if self.spreed_status==3:
            #todo 等待平仓
            pass

    def update_order(self, order):
        if order.status == Status.FILLED:
            self.hedage()
            del self.order[order.order_id]
            self.check = False
        elif order.status == Status.CANCELED:
            del self.order[order.order_id]
            self.check = False
        elif order.status == Status.REJECTED:
            del self.order[order.order_id]
            self.check = False
        else:
            self.order[order.order_id] = order

    def update_postion(self):
        self.long_position=self.long.get_positions(self.long.symbol)
        self.short_position=self.short.get_positions(self.short.symbol)

    def on_order(self, event):
        order = event['data']
        self.update_order(order)
        print(event)

    def on_trade(self, event):
        pass

    def on_bar(self, event):
        pass

    def on_position(self, event):
        pass


if __name__ == "__main__":
    ev=EventEngine()
    st = SpreedStrategy(ev,None)
    st.init()
    while True:
        time.sleep(1)
