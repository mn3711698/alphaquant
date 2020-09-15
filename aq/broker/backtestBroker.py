from aq.engine.baseBroke import *
from aq.common.constant import *
from aq.common.object import *
from aq.common.logger import *
import numpy as np
import pandas as pd



class BacktestBroker(BaseBroker):
    name = "BacktestBroker"
    limit_orders={}
    trades={}
    trade_count=0
    pnl=[]

    benchmark=[]
    price={}
    def __init__(self):
        self.markets["BTC/USDT"]={"id":"BTC/USDT","baseAsset":"USDT","quoteAsset":"BTC"}
        pass
    def set_capital(self,capital):
        self.balances['USDT']={"free":capital}
        self.balances['BTC']={"free":0}
    def add_bar(self,data):
        """
        0 = time {str} '2017-08-17 08:00:00'
        1 = open {float} 4261.48
        2 = high {float} 4485.39
        3 = low {float} 4200.74
        4 = close {float} 4285.08
        5 = volume {float} 795.1503769999999
        :param data:
        :return:
        """
        if self.bars is None:
            self.bars=pd.DataFrame(columns=["time","open","high","low","close","volume"])

        self.bars=self.bars.append(data)
        self.datetime=data['time']
        self.price["BTC"]=data["close"]
        # symbol=data['symbol']
        # interval=data['interval']
        # d=data['data']
        # self.bars[symbol-interval].append(d)

    def add_ticket(self,data):
        if self.tickets == None:
            self.tickets =pd.DataFrame(data)
        else:
            self.tickets=self.tickets.append(data)
        # symbol=data['symbol']
        # d=data['data']
        # self.tickets[symbol].append(d)

    def get_positions(self):
        return self.balance['BTC'].get('free',0)

    #todo 实现buy
    def buy(self,**kwargs):
        symbol=self.markets[kwargs['symbol']]
        price=kwargs['price']
        volume=kwargs['volume']
        side=BUY
        status=Status.ALLTRADED
        fee=0
        self.trade_count += 1
        trade = TradeData(
            symbol=symbol['id'],
            brokername=self.name,
            orderid="",
            tradeid=str(self.trade_count),
            side=side,
            price=price,
            volume=volume,
            status=status,
            fee=fee,
            time=self.datetime
        )
        #余额加减
        baseAsset=symbol['baseAsset'] #基础货币
        quoteAsset=symbol['quoteAsset'] #交易货币

        balance=self.balance[baseAsset]
        balance=balance.get("free",0)
        total=volume*price
        if total>balance:
            trade.status=Status.REJECTED
            log.warn(f"{baseAsset}余额不足")
            return False
        else:
            self.balance[baseAsset]['free']=balance-total
            self.balance[quoteAsset]['free']=self.balance[quoteAsset].get("free", 0)+volume
            log.info(f"买入,价格 {trade.price},数量 {trade.volume}，金额 %0.2f"%total)
            #成交记录
            self.trades[trade.tradeid] = trade


    # todo 实现sell
    def sell(self,**kwargs):
        symbol = self.markets[kwargs['symbol']]
        price = kwargs['price']
        volume = kwargs['volume']
        side = SELL
        status = Status.ALLTRADED
        fee = 0
        self.trade_count += 1
        trade = TradeData(
            symbol=symbol['id'],
            brokername=self.name,
            orderid="",
            tradeid=str(self.trade_count),
            side=side,
            price=price,
            volume=volume,
            status=status,
            fee=fee,
            time=self.datetime
        )
        # 余额加减
        baseAsset = symbol['baseAsset']  # 基础货币
        quoteAsset = symbol['quoteAsset']  # 交易货币

        balance = self.balance[quoteAsset].get("free", 0)
        total = volume * price
        if volume> balance:
            trade.status = Status.REJECTED
            log.info(f"{quoteAsset}余额不足")
            return False
        else:
            self.balance[baseAsset]['free'] = self.balance[baseAsset].get('free',0)+total
            self.balance[quoteAsset]['free'] = self.balance[quoteAsset].get('free',0) - volume
            # 成交记录
            log.info(f"卖出,价格 {trade.price},数量 {trade.volume}，金额 %0.2f"%total)
            self.trades[trade.tradeid] = trade

    def do_pnl(self):
        p = 0
        for i in self.balance:
            if i == "USDT":
                p = p + self.balance[i]["free"]
            else:
                price = self.price[i]
                p = p + self.balance[i]["free"] * price
        self.pnl.append([self.datetime,p])

        self.benchmark.append([self.datetime,self.price["BTC"]])

    def get_daily_results(self):
        result={}
        result["returns"]=self.pnl
        trades=list(self.trades.values())
        trades=[[i.time,i.side,i.price,i.volume] for i in trades]
        result["trades"]=trades
        result["benchmark"]=self.benchmark
        return result
    def cancelOrder(self, order):
        pass

    def get_trades(self):
        return self.trades

    def cancel_order(self):
        pass

    def subscribe(self):
        pass

    def update_orderbook(self,*args, **kwargs):
        pass


