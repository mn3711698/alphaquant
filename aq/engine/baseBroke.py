from abc import ABC, abstractmethod
from aq.common.constant  import *
from typing import Any, Sequence, Dict, List, Optional, Callable
from aq.engine.event import EventEngine,Event
from websocket import WebSocketApp
from threading import Thread,Lock
from aq.common.logger import log
import traceback
import time
import json
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
    proxies={}
    param={}
    _CONNECT_TIMEOUT_S = 15
    subscribes={}

    def __init__(self,event_engine):
        self.ev=event_engine


    def on_event(self, type: str, data: Any = None) -> None:
        """
        General event push.
        """
        event = Event(type, data)
        self.ev.put(event)


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



    def connect(self):
        if self.ws:
            return
        else:
            self._connect()
            if self.ws:
                log.info("WS连接成功")

    def _connect(self):
        url=self.param.get("wshost","")
        self.ws = WebSocketApp(
                url,
                on_message=self._wrap_callback(self._on_message),
                on_close=self._wrap_callback(self._on_close),
                on_error=self._wrap_callback(self._on_error),
            )
        wst = Thread(target=self._run_websocket, args=(self.ws,))
        wst.daemon = True
        wst.start()
        ts = time.time()
        while self.ws and (not self.ws.sock or not self.ws.sock.connected):
                if time.time() - ts > self._CONNECT_TIMEOUT_S:
                    self.ws = None
                    return
                time.sleep(0.1)

    def _on_message(self, ws, message):
        raise NotImplementedError()
    def _on_close(self, ws):
        log.error("WS连接关闭")
        self._reconnect(ws)

    def _on_error(self, ws, error):
        log.error(error)
        self._reconnect(ws)

    def reconnect(self) -> None:
        if self.ws is not None:
            self._reconnect(self.ws)

    def _run_websocket(self, ws):
        try:
            if self.proxies:
                ws.run_forever(http_proxy_host=self.proxies['host'],http_proxy_port=self.proxies['port'])
            else:
                ws.run_forever()
        except Exception as e:
            log.error(traceback.format_exc())
            raise Exception(f'Unexpected error while running websocket: {e}')
        finally:
            self._reconnect(ws)

    def _reconnect(self, ws):
        assert ws is not None, '_reconnect should only be called with an existing ws'
        if ws is self.ws:
            #todo 2020.05.01重新连接之后需要判断当前的订阅是不是要重新订阅，包括登录状态
            log.info("Reconnect...")
            self.ws = None
            ws.close()
            self.connect()
            # self._subscribe()

    def _wrap_callback(self, f):
        def wrapped_f(ws, *args, **kwargs):
            if ws is self.ws:
                try:
                    f(ws, *args, **kwargs)
                except Exception as e:
                    log.error(traceback.format_exc())
                    raise Exception(f'Error running websocket callback: {e}')

        return wrapped_f

    @abstractmethod
    def get_sub(self,**kwargs):
        raise NotImplementedError



    def _subscribe(self,ch,symbols):
        if not self.ws:
            self.connect()
        if self.ws:
            for k in ch.keys():
                chanels=self.param.get("chanels",None)
                c = chanels.get(k, "")
                for symbol in symbols:
                    req=self.get_sub(channel=c,symbol=symbol)
                    log.info(req)
                    self.ws.send_json(req)
                self.subscribes[k] = ch[k]

