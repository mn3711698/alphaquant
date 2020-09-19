import os
import sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

from apscheduler.schedulers.blocking import BlockingScheduler
from aq.engine.baseStrategy import BaseStrategy
from aq.common.logger import *
from aq.broker import Binance, Ftx
from aq.engine.event import EventEngine
from aq.common.message import Feishu
from aq.common.tools import *
from aq.indicator.base import *
from aq.indicator.rsi import *
from aq.engine.config import config
from aq.common.constant import *

class Grid(BaseStrategy):
    """"
    网格策略
    网络大小根据波动率设置
    持仓根据50%-200%
    """

    symbol="BTCUSDT"
    timeframe="1h"
    mid_price=0   # 最小二乘回归中线
    upper=0       #日线180天最高值
    lower=0       #日线180最低值


    def __init__(self, engine, setting):
        super().__init__(engine, setting)
        self.data=None
        self.volt_per = 0  #周期波动率
        self.status = 0    #当前状态
        self.cur_price = 0 #当前成交价格
        self.orders = {}   #未执行订单
        self.ev = engine
        long_cfg = config.long
        self.broker = Binance(self.ev, long_cfg.api_key, long_cfg.api_secret)
        self.register_event()
        self.broker.start(self.symbol,[KLINE5,ORDER])
        self.size=0
        self.orders={}
        self.volt_per=0
        self.init_pos()

    def register_event(self):
        """"""
        self.ev.register(TICKER, self.on_ticker)
        self.ev.register(TRADES, self.on_trade)
        self.ev.register(ORDERBOOK, self.on_orderbook)
        self.ev.register(ORDER, self.on_order)
        self.ev.register(POSITION, self.on_position)
        self.ev.register(BALANCE, self.on_balance)

    def on_orderbook(self, event):
        pass
    def on_balance(self, event):
        pass

    def on_order(self, side):
        pass
    def on_position(self,event):
        pass
    def on_ticker(self, event):
        pass

    def on_trade(self, event):
        pass

    def init_pos(self):
        self.data=self.broker.get_bar(self.symbol,self.timeframe)
        data=pd.DataFrame(self.data)
        volt=(data["high"]-data["low"])/data["close"]
        self.volt_per=volt[:,-30].mean()
        cash = self.broker.get_balnce("USDT")
        asset=self.broker.get_balnce("BTC")
        close=data["close"].values
        price=close[-1]
        amount=cash+asset*price
        self.size=round(amount/price*self.volt_per,2)
        self.status=1
        log.info(f"网格策略初始化成功,账户资产:{amount},资产:{asset},资金:{cash},网格间隔：{volt}，网格数量：{self.size}")

    def on_bar(self, event=None):
        data = event.data
        data = data['k']
        self.add_bar(data)
        if self.status!=0:
            if len(self.orders)==0:
                price=data["c"]
                order=self.broker.buy(symbol=self.symbol,price=price*(1-self.volt_per),quantity=self.size)
                self.orders[order.ref]=order
                order = self.broker.sell(symbol=self.symbol, price=price * (1 + self.volt_per), quantity=self.size)
                self.orders[order.ref] = order


    def add_bar(self,data):
        self.data.append(data)
        data = pd.DataFrame(self.data)
        volt = (data["high"] - data["low"]) / data["close"]
        self.volt_per = volt[:, -30].mean()

    def notify_order(self, order):
        try:
            if order.status in [order.Completed]:
                self.cur_price=order.price
                self.orders.pop(order.ref)
                for i in self.orders:
                    self.broker.cancel_order(self.symbol,order.id)
            if order.status in [order.Canceled]:
                self.orders.pop(order.ref)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    ev = EventEngine()
    ev.start()
    st = Grid(ev, None)
    while True:
        time.sleep(60)

