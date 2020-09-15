from abc import ABC, abstractmethod
from aq.common.constant  import *
from typing import Any, Sequence, Dict, List, Optional, Callable
from aq.engine.event import EventEngine,Event


class BaseBroker(ABC):
    """Base class for brokers.

    .. note::
    broker 交易所&经纪商基础类
    用于下单，格式转换，获取持仓数据等
    """
    name = "BaseBroke"
    BrokerType=Product.CASH #交易类型，现货，杠杆，合约
    bars=None  #历史Bar数据
    tickets=None
    account=[]
    markets={}
    positions={}
    balances={}
    bid={}
    ask={}
    symbol=""
    mid_price:float=0
    bid_price:float=0
    ask_price:float=0
    price:float=0 #bid+ask/2
    model="Prod"

    def __init__(self,event_engine):
        self.ev=event_engine


    def on_event(self, type: str, data: Any = None) -> None:
        """
        General event push.
        """
        event = Event(type, data)
        self.ev.put(event)

    @abstractmethod
    def update_orderbook(self,*args, **kwargs):
        raise NotImplementedError
    @abstractmethod
    def subscribe(self,*args, **kwargs):
        raise NotImplementedError
    @abstractmethod
    def get_trades(self,*args, **kwargs):
        """
        :return: {
        time:1567736576000 时间戳到毫秒
        Price:100.00 成交价格
        Amount:1.00  成交数量
        Type: 0      订单类型 ORDER_TYPE_BUY=0，ORDER_TYPE_SELL=1
        }
        """
        raise NotImplementedError()

    def get_depth(self,*args, **kwargs):
        """
        :return{
        asks:[]
        bids:[]
        }
        """
        raise NotImplementedError()

    def get_bar(self,*args, **kwargs):
        return self.bars

    def get_ticket(self,*args, **kwargs):
        return self.tickets


    @abstractmethod
    def get_positions(self,*args, **kwargs):
        """获取持仓，杠杆，合约"""
        raise NotImplementedError()





    @abstractmethod
    def buy(self,*args, **kwargs):
        """Submits an order.

        :param order: The order to submit.
        :type order: :class:`Order`.

        .. note::
            * After this call the order is in SUBMITTED state and an event is not triggered for this transition.
            * Calling this twice on the same order will raise an exception.
        """
        raise NotImplementedError()

    @abstractmethod
    def sell(self,*args, **kwargs):
        raise NotImplementedError()

    def _handel_request(self,response):
        code = response.status_code
        if code not in (200, 201, 202, 203, 204, 205, 206,400):
            text = response.text
            return text
        try:
            result = response.json()
        except:
            result = response.text
        return result

    @abstractmethod
    def cancel_order(self,*args, **kwargs):
        """Requests an order to be canceled. If the order is filled an Exception is raised.
        取消订单
        """
        raise NotImplementedError()



