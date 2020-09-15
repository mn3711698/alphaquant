import os
import sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

from apscheduler.schedulers.blocking import BlockingScheduler
from aq.engine.baseStrategy import BaseStrategy
from aq.common.logger import *
from aq.broker import BinanceFutures, Ftx
from aq.engine.event import EventEngine
from aq.common.message import Feishu
from aq.common.tools import *
from aq.indicator.base import *
from aq.indicator.rsi import *
from aq.engine.config import config
from aq.common.constant import *


class DoubleRsi(BaseStrategy):
    author = "用Python的交易员"
    strategy_name = "DoubleRsi"
    min_tp=20 #止盈最小价格间距
    tp_price=50
    sl_price=60
    parameters = ["fast_window", "slow_window"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]
    symbol = "btcusdt"
    qty = 0.005 #下单数量
    orders={}
    vr=0.003

    def __init__(self, engine, setting):
        super().__init__(engine, setting)
        self.msg = Feishu()
        self.ev = engine
        long_cfg = config.long
        self.broker = BinanceFutures(self.ev, long_cfg.api_key, long_cfg.api_secret)
        self.register_event()
        self.broker.start(self.symbol)
        # self.broker.cancel_all_order(self.symbol)
        self.scheduler = BlockingScheduler()
        self.scheduler.add_job(self.on_bar, 'cron', minute="14,29,44,59", second="50")
        # self.scheduler.add_job(self.on_bar, 'cron', second="30")
        self.scheduler.add_job(self.broker.put_listenKey, 'interval', minutes=45)
        self.scheduler.start()


    def register_event(self):
        """"""
        # self.ev.register(TICKER, self.on_ticker)
        # self.ev.register(TRADE, self.on_trade)
        # self.ev.register(ORDERBOOK, self.on_orderbook)
        self.ev.register(ORDER, self.on_order)
        self.ev.register(POSITION, self.on_position)
        self.ev.register(BALANCE, self.on_balance)

    def on_orderbook(self, event):
        pass
        # orderbook = event.data
        # log.info(orderbook.bids())

    def on_balance(self, event):
        pass

    def on_bar(self, event=None):
        log.info("开始任务")

        # self.open_order("Sell")

        bar_15m = self.broker.get_bar(self.symbol, "15m")
        close_15m = bar_15m["close"]
        vr=(bar_15m["high"]-bar_15m["low"])/close_15m
        vr=talib.MA(np.array(vr),16)
        self.vr=vr[-1]
        self.checkorder()
        bar_4h = self.broker.get_bar(self.symbol, "4h")
        close_4h = bar_4h["close"]
        # fastk_4h, fastd_4h = StochRSI(close_4h, smoothK=3, smoothD=3, lengthRSI=7, lengthStoch=5)
        # fastk, fastd = StochRSI(close_15m, smoothK=3, smoothD=3, lengthRSI=7, lengthStoch=5)
        t=trend_frsi(close_4h)
        s=dsr(close_15m)
        # log.info(f"4小时k:{fastk_4h[-1]},d:{fastd_4h[-1]},15分钟k:{fastk[-1]},d:{fastd[-1]}")
        if t==1 and s==1:
            self.open_order("Buy")
        elif t==-1 and s==-1:
            self.open_order("Sell")
        # if fastk_4h[-1] > fastd_4h[-1] and fastk_4h[-1] > fastk_4h[-2] and fastd_4h[-1] > fastd_4h[-2] :
        #     log.info("趋势向上")
        #     if crossover(fastk, fastd) and fastk[-1] > 20:
        #         msg = f"当前时间:{get_datetime()}\n趋势：向上\n当前价格{list(close_15m)[-1]}\n策略：买入"
        #         self.msg.send("日内震荡策略", msg)
        #         self.open_order("Buy")
        #
        # elif fastk_4h[-1] < fastd_4h[-1] and fastk_4h[-1] < fastk_4h[-2] and fastd_4h[-1] < fastd_4h[-2]:
        #     log.info("趋势向下")
        #     if crossunder(fastk, fastd) and fastk[-1] < 80:
        #         msg = f"当前时间:{get_datetime()}\n趋势：向下\n当前价格{list(close_15m)[-1]}\n策略：卖出"
        #         self.msg.send("日内震荡策略", msg)
        #         self.open_order("Sell")

    def open_order(self, side):
        position = self.broker.get_positions(self.symbol.upper())
        log.info(f"当前持仓{position}")

        p = True
        # log.info(f"买卖价{self.broker.ask_price},{self.broker.bid_price}")
        bid, ask = self.broker.get_depth(self.symbol)
        # log.info(f"买卖价{bid[0]},{ask[0]}")
        for p in position:
            # log.info(f"当前持仓{p}")
            if p.qty != 0:
                p = False
        if p and side == "Buy":
            price = float(bid[0][0])
            o = self.broker.buy(self.symbol, self.qty,price=price, position_side=Direction.LONG.name)
            log.info(f"开仓单{o}")
        if p and side == "Sell":
            price = float(ask[0][0])
            o = self.broker.sell(self.symbol, self.qty, price=price, position_side=Direction.SHORT.name)
            log.info(f"开仓单{o}")

    def checkorder(self):
        """
        检查止盈订单
        当超过1小时未成交，止盈价减少移动5%
        直到成本价附近，且趋势已经反转则主动平仓
        :return:
        """
        # r=40/0.003 #以15分钟0.03波动率赚40点为基准
        # self.tp_price=round(r*self.vr)
        log.info(self.tp_price)
        # log.info(self.vr)
        log.info("检查持仓")
        qty = 0
        direction = None
        price = 0.00
        position=self.broker.get_positions(self.symbol.upper())
        pos=None
        log.info(position)
        for p in position:
            if abs(p.qty)> 0:
                pos=p
        if pos:
            if pos.direction == Direction.SHORT:
                price = round(pos.price - self.tp_price)
                tporder=self.orders.get("TP",None)
                if not tporder:
                    o = self.broker.buy(pos.symbol, abs(pos.qty), price=price, position_side=Direction.SHORT.name,tif=Timeinforce.GTC)
                # self.msg.send("订单指令", o)
                    log.info(f"新止盈单{o}")
                    self.orders["TP"]=o
                elif tporder.qty!=abs(pos.qty):
                    log.info(f"止盈单数量{tporder.qty},持仓数量{pos.qty}")
                    o=self.broker.cancel_order(self.symbol,tporder.order_id)
                    log.info(f"取消止盈单{o}")
                    self.orders.pop("TP")
                    o = self.broker.buy(pos.symbol, abs(pos.qty), price=price, position_side=Direction.SHORT.name,
                                        tif=Timeinforce.GTC)
                    # self.msg.send("订单指令", o)
                    log.info(f"新止盈单{o}")
                    self.orders["TP"] = o

                elif tporder.price<price:
                    log.info(f"止盈单价格{tporder.price},止盈价格{self.tp_price}")
                    o = self.broker.cancel_order(self.symbol, tporder.order_id)
                    log.info(f"取消止盈单{o}")
                    self.orders.pop("TP")
                    o = self.broker.buy(pos.symbol, abs(pos.qty), price=price, position_side=Direction.SHORT.name,
                                        tif=Timeinforce.GTC)
                    # self.msg.send("订单指令", o)
                    log.info(f"新止盈单{o}")
                    self.orders["TP"] = o

                slorder=self.orders.get("SL",None)
                if not slorder:
                    price = round(pos.price + self.tp_price)
                    o = self.broker.close_Shortorder(pos.symbol, price)
                    log.info(f"新止损单{o}")
                    self.orders["SL"] = o


            if pos.direction == Direction.LONG:
                price = round(pos.price + self.tp_price)
                tporder = self.orders.get("TP", None)
                if not tporder:
                    o = self.broker.sell(p.symbol, abs(pos.qty), price=price, position_side=Direction.LONG.name,
                                     tif=Timeinforce.GTC)
                # self.msg.send("订单指令", o)
                    log.info(f"新止盈单{o}")
                    self.orders["TP"] = o
                elif tporder.qty !=abs(pos.qty):
                    log.info(f"止盈单数量{tporder.qty},持仓数量{pos.qty}")
                    o = self.broker.cancel_order(self.symbol, tporder.order_id)
                    log.info(f"取消止盈单{o}")
                    self.orders.pop("TP")
                    o = self.broker.sell(p.symbol, abs(pos.qty), price=price, position_side=Direction.LONG.name,
                                         tif=Timeinforce.GTC)
                    # self.msg.send("订单指令", o)
                    log.info(f"新止盈单{o}")
                    self.orders["TP"] = o
                elif tporder.price >price:
                    log.info(f"止盈单价格{tporder.price},止盈价格{self.tp_price}")
                    o = self.broker.cancel_order(self.symbol, tporder.order_id)
                    log.info(f"取消止盈单{o}")
                    o = self.broker.sell(p.symbol, abs(pos.qty), price=price, position_side=Direction.LONG.name,
                                         tif=Timeinforce.GTC)
                    # self.msg.send("订单指令", o)
                    log.info(f"新止盈单{o}")
                    self.orders["TP"] = o

                slorder = self.orders.get("SL", None)
                if slorder is None:
                    price =round (pos.price - self.tp_price)
                    o = self.broker.close_Longorder(pos.symbol, price)
                    log.info(f"新止损单{o}")
                    self.orders["SL"] = o
                else:
                    log.info(slorder)

        else:
            log.info("空仓，取消所有订单")
            self.orders["TP"]=None
            self.orders["SL"] = None
            self.broker.cancel_all_order(self.symbol)

    def on_order(self, event):
        order = event.data
        log.info(f"订单状态{order}")
        if order.status=="CANCELED" or order.status=="FILLED":
            tporder = self.orders.get("TP", None)
            if tporder and tporder.order_id==order.order_id:
                self.orders.pop("TP")
            slorder = self.orders.get("SL", None)
            if slorder and slorder.order_id == order.order_id:
                self.orders.pop("SL")
        # msg=f"{order.order_id},{order.side},{order.status},{order.qty},{order.price}"
        self.msg.send("订单指令",f"{order}")

    def on_position(self, event):
        """
        持仓有变化，重新设计止盈止损价
        :return:
        """
        self.checkorder()




    def on_ticker(self, event):
        pass

    def on_trade(self, event):
        pass


if __name__ == "__main__":
    ev = EventEngine()
    ev.start()
    st = DoubleRsi(ev, None)
    while True:
        time.sleep(60)
