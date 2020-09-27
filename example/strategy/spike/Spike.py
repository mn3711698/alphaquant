import os
import sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

from apscheduler.schedulers.blocking import BlockingScheduler
from aq.engine.baseStrategy import BaseStrategy
from aq.common.logger import log
from aq.broker import BinanceFutures, Ftx
from aq.engine.event import EventEngine
from aq.common.message import Weixin
from aq.common.tools import *
from aq.indicator.base import *
from aq.indicator.rsi import *
from aq.engine.config import config
from aq.common.constant import *
from collections import deque
import numpy as np
from aq.engine.autoreload import run_with_reloader

class Spike(BaseStrategy):
    symbol="BTCUSDT"
    count=0
    data={}
    buy_force=0  #强平数量
    sell_force=0 #强平数量
    force_time=0 #最后强平时间
    buys=[]
    sells=[]
    maxtrades=0
    sig=0
    varsig=0
    tp_per=0.005
    sl_per=0.005
    # qty=0.001 #每单下单量
    percent=0.05 #下单量占资金百分比
    position=[]
    margin=50
    dt=3
    miniqty=3 #下单数量小数痊
    move_ratio=0.002 #移动止损止盈反弹幅度
    highprice=0
    lowprice=0
    status=False
    def __init__(self, engine, setting):
        super().__init__(engine, setting)
        self.msg = Weixin("17377523487@chatroom")
        self.ev = engine
        self.bar=deque(maxlen=1440)
        cfg = config.long
        self.broker = BinanceFutures(self.ev, cfg.api_key, cfg.api_secret)

        # self.broker = Binance(self.ev, long_cfg.api_key, long_cfg.api_secret)

        self.broker.start(self.symbol,[KLINE5,FORCEORDER])
        self.register_event()
        self.status=True
        self.check_position()


    def loadbar(self,starttime):
        data=self.broker.get_bar(self.symbol.upper(),'5m',starttime)
        d = data.values.tolist()
        self.bar.extend(d)
        d=self.bar[-1]
        st=d[0]
        if st<(get_cur_timestamp_ms()-300000):
            self.loadbar(st)


    def register_event(self):
        """"""
        # self.ev.register(TICKER, self.on_ticker)
        self.ev.register(FORCEORDER, self.on_forceorder)
        # self.ev.register(TRADES, self.on_trade)
        self.ev.register(KLINE,self.on_bar)
        # self.ev.register(ORDERBOOK, self.on_orderbook)
        # self.ev.register(ORDER, self.on_order)
        # self.ev.register(POSITION, self.on_position)
        # self.ev.register(BALANCE, self.on_balance)

    def on_forceorder(self,event):
        data = event.data
        data = data['o']
        if data['S']=="SELL":
            self.sell_force=self.sell_force+float(data['l'])
            self.buys.append([self.force_time,self.buy_force])
            self.buy_force=0
        elif data['S']=="BUY":
            self.buy_force=self.buy_force+float(data["l"])
            self.sells.append([self.force_time, self.sell_force])
            self.sell_force = 0
        self.force_time=data['T']
        # log.info(data)


    def check_force(self):
        # bar = np.array(self.bar)
        # volume = bar[:, 5]
        # volume=volume.astype(np.float)
        # log.info(volume)
        # volume = np.average(volume)
        # v=1/volume*200
        # log.info(v)
        deltatime=get_cur_timestamp_ms() - self.force_time
        if (deltatime > self.dt*1000) and self.force_time > 0:
            starttime = get_cur_timestamp_ms() - 60000 * 1440 * 30
            volume=self.max_volume(starttime)
            side=BUY
            v=0
            if self.sell_force>0:
                v=self.sell_force/volume*300
                side=BUY
            elif self.buy_force>0:
                v=self.buy_force/volume*300
                side=SELL

            self.sig = ((1 / (1 + math.exp(-v))) - 0.5) * 2
            # log.info(f"当前爆仓sig {self.sig},最近1小时成交量 {volume},强平卖单量 {self.sell_force},强平买单量 {self.buy_force}")
            price =float(self.data['c'])
            # log.info(f"当前价格 {price}")
            if self.sig>0.85:
                log.info(f"当前爆仓sig {self.sig},最近1小时成交量 {volume},强平卖单量 {self.sell_force},强平买单量 {self.buy_force}")
                self.open_order(side,price)
                self.buy_force = 0
                self.sell_force = 0
                self.force_time = 0
            self.force_time = 0


    def on_ticker(self, event):
        pass


    def on_trade(self, event):
        data=event.data
        print(data)

    def on_orderbook(self, event):
        pass

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

    def on_bar(self, event=None):
        data = event.data
        data = data['k']
        self.data=data
        self.check_force()
        # n = data['n']  # 这根K线是否完结(是否已经开始下一根K线
        # t=data['t']
        # next=data['x']
        # v=n/self.maxtrades*20
        # self.sig=((1/(1+math.exp(-v)))-0.5)*2
        # self.varsig=self.sig*300000/(get_cur_timestamp_ms()-t)
        # # [1594988400000, 9178.42, 9182.3, 9170.0, 9174.96, '1072.141', 1594988699999, '9837139.22509', 3159, '473.257',
        # #  '4342571.91987', '0']
        # # {'t': 1594995900000, 'T': 1594996199999, 's': 'BTCUSDT', 'i': '5m', 'f': 163202496, 'L': 163204715,
        # #  'o': '9151.47', 'c': '9143.34', 'h': '9151.57', 'l': '9140.51', 'v': '970.103', 'n': 2220, 'x': True,
        # #  'q': '8871138.11349', 'V': '236.435', 'Q': '2162196.58503', 'B': '0'}
        #
        # t=[data['t'],float(data['o']),float(data['h']),float(data['l']),float(data['c']),float(data['v']),data['q'],data['v'],data['n'],data['V'],data['Q'],data["B"]]
        # # if self.sig>0.85:
        # #     log.info(f"当前K线交易数: {n}")
        # #     log.info(f"当前sig: {self.sig}")
        # #     log.info(f"预计sig: {self.varsig}")
        # # #     log.info(f"当前价格：{data['c']}")
        #
        # if next:
        #     self.bar.append(t)



    def check_position(self):
        while self.status:
            try:
                position = self.broker.get_positions(self.symbol)
                if len(position)>0:
                    p=position[0]
                    # log.info(p)
                    data=self.data
                    if len(data)>0:
                        price=float(data["c"])
                        #止损
                        if p.direction==Direction.LONG:
                            if price<(p.price*(1-self.sl_per)):
                                o = self.broker.close_position(p)
                                log.info(f"止损平仓：{o}")
                                self.lowprice = 0
                                self.highprice = 0
                        else:
                            if price>(p.price*(1+self.sl_per)):
                                o = self.broker.close_position(p)
                                log.info(f"止损平仓：{o}")
                                self.lowprice = 0
                                self.highprice = 0
                        #止盈
                        if self.move_tp(p.direction, price, p.price):
                            o = self.broker.close_position(p)
                            self.lowprice = 0
                            self.highprice = 0
                            log.info(f"移动止盈：{o}")
                time.sleep(1)
            except Exception as e:
                print(e)
                time.sleep(1)


    def max_volume(self,starttime):
        self.loadbar(starttime)
        bar = np.array(self.bar)
        volume = bar[:, 5]
        volume=volume.astype(np.float)
        return np.max(volume)

    def open_order(self, side,price):
        position = self.broker.get_positions(self.symbol)
        bar_4h = self.broker.get_bar(self.symbol, "4h")
        close_4h = bar_4h["close"]
        t = trend_frsi(close_4h)


        # log.info(f"当前持仓{position}")
        if len(position)>0:
            pos=position[0]
            if (pos.direction==Direction.LONG and side==SELL) or (pos.direction==Direction.SHORT and side==BUY):
                o = self.broker.close_position(pos)
                log.info(f"止损平仓：{o}")
                self.lowprice = 0
                self.highprice = 0
                time.sleep(0.5)

        else:
            position = self.broker.get_positions(self.symbol)
            if len(position) == 0:
                value = self.broker.get_balnce("USDT")
                #根据开仓百分比下单
                qty = round(float(value.balance)*self.percent / price*50, self.miniqty)
                log.info(f"当前账户USDT余额：{value}")
                if side==BUY:
                    o=self.broker.buy(self.symbol,qty)
                    log.info(f"买单：{o}")
                    time.sleep(0.5)
                    self.position = self.broker.get_positions(self.symbol)
                    log.info(f"当前持仓{self.position }")
                    self.lowprice = 0
                    self.highprice = 0

                    msg = f"*******一阳指策略*******\n交易对:BTC合约(币安)\n当前价格：{price}\n操作建议:平空做多"
                    self.msg.send(msg)
                else:
                    o=self.broker.sell(self.symbol, qty)
                    log.info(f"卖单：{o}")
                    time.sleep(0.5)
                    self.position = self.broker.get_positions(self.symbol)
                    log.info(f"当前持仓{self.position}")
                    self.lowprice = 0
                    self.highprice = 0
                    msg = f"*******一阳指策略*******\n交易对:BTC合约(币安)\n当前价格：{price}\n操作建议:平多做空"
                    self.msg.send(msg)

    def move_tp(self,side,close,price):
        if self.highprice<close:
            self.highprice=close
        if self.lowprice>close or self.lowprice==0:
            self.lowprice=close
        if side==Direction.LONG:
            #高点超过止盈价，收盘价低于止盈价时止盈
            if self.highprice>price*(1+self.tp_per) and close<price*(1+self.tp_per):
                log.info(f"高点{self.highprice},回调到{close}")
                return True
            #高点超过止盈价，回调幅度大于回撤百分比
            elif self.highprice>price*(1+self.tp_per) and (self.highprice-close)/close>self.move_ratio:
                log.info(f"高点 {self.highprice},回调 {(self.highprice-close)/close}")
                return True
            else:
                return False
        else:
            if self.lowprice<price*(1-self.sl_per) and close>price*(1-self.tp_per):
                log.info(f"低点{self.lowprice},回调到{close}")
                return True
            elif (close-self.lowprice)/close>self.move_ratio and self.lowprice<price*(1-self.sl_per):
                log.info(f"低点 {self.lowprice},回调 {(close-self.lowprice)/close}")
                return True
            else:
                return False


def main():
    ev = EventEngine()
    ev.start()
    st = Spike(ev, None)

if __name__ == "__main__":
    main()