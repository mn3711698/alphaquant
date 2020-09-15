# -*- coding:utf-8 -*-
"""
@Time : 2020/5/4 7:40 下午
@Author : Domionlu
@Site :
@File : spreeddata.py
价差交易，二个相关性产品配对组合成一个产品

"""
from aq.common.utility import RepeatingTimer
from aq.common.object import *
from aq.engine.baseBroke import BaseBroker

class SpreedData():
    spreed:{}#价差交易对
    offset:int=1.5 #目标是几倍标准差
    short:BaseBroker
    long:BaseBroker
    long_price:float=0
    short_price:float=0
    qty:float=0.0001#前期使用最小单位，实盘稳定之后再考虑根据资金调配仓位
    long_position:Position
    short_position:Position
    order:{}
    def __init__(self):
        RepeatingTimer(1,self.check_order).start()#每秒检查下次挂单情况

    def open_spreed(self):
        """
        合成一个配对交易，交易信号由策略完成，
        合成模式：
        1 先maker被动待成交，后再主动taker另一个交易对，被动市场优先选择流动高，有返利，深度可以差一点，主动市场优先选择有深度，手续费优惠
        2 二边都主动taker，先吃深度差，流动性差的一边，再吃深度好，流动性的一边，
        规则目标：防止合成不成功
        :param
        side:主动腿-被动腿<0:买入主动腿，卖出被动腿，主动腿-被动腿>0:卖出主动腿，买入被动腿
        type:abs(主动腿-被动腿)>1.5*spreed:同时taker,abs(主动腿-被动腿)<1.5*spreed:maker主动腿，taker被动腿
        :return:
        """
        side= (self.long_price-self.short_price)>0
        type=abs(self.long_price-self.short_price)>self.offset
        if type:
            #价差超过spreed,直接二边taker下单
            if side:
                long_order=self.long.sell(self.long.symbol,self.qty)
                short_order=self.short.buy(self.short.symbol,self.qty)
            else:
                long_order = self.long.buy(self.long.symbol,self. qty)
                short_order=self.short.sell(self.short.symbol,self.qty)
            self.order[long_order.order_id]=long_order
            self.order[short_order.order_id]=short_order
            self.long_wait = True
            self.short_wait = True
            self.hedage()
        else:
            #价差未超过spreed,long maker
            if side:
                order=self.long.sell(self.long.symbol,self.long_price ,self.qty)
            else:
                order = self.long.buy(self.long.symbol,self.long_price,self.qty)
            self.order[order.order_id]=order
            self.long_wait = True
            self.check=True

    def check_order(self):
        if self.check:
            #检查订单委托情况，如果没有成交且波动超过万2，则重新进行挂单
            bid_price = float(list(self.short.bid.keys())[0])
            ask_price = float(list(self.short.ask.keys())[0])
            order=self.order[self.order.key()[0]]
            if order.side==BUY:
                delta=(order.price-bid_price )/order.price
                if delta>0.0002:
                    self.long.cancel_order(self.long.symbol,order.order_id)
                    self.long_wait = False
            else:
                delta=(order.price-ask_price )/order.price
                if delta>0.0002:
                    self.long.cancel_order(self.long.symbol,order.order_id)
                    self.long_wait = False

    def update_order(self,order):
        if order.status==Status.FILLED:
            if self.long_wait:
                p = self.long.get_position()
                self.long_position=p
                self.long_wait=False
            if self.short_wait:
                p = self.short.get_position()
                self.short_position = p
                self.short_wait = False
            if order.order_id in order:
                del self.order[order.order_id]
            self.check=False
            self.hedage()
        elif order.status==Status.CANCELED:
            del self.order[order.order_id]
            self.check = False
        else:
            self.order[order.order_id]=order


    def hedage(self):
        """
        long挂单成交，short主动taker
        """
        if self.long_position and not self.short_position:
            side=self.long_position.side
            qty=self.long_position.qty
            if side == BUY:
                order = self.short.sell(self.short.symbol, qty)
            else:
                order = self.short.buy(self.short.symbol, qty)
            self.order[order.order_id]=order
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

    def close_positon(self,p):
        pass
    def close_spreed(self):
        """
        :return:
        """



if __name__ == "__main__":
    pass