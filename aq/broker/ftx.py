# -*- coding:utf-8 -*-
"""
@Time : 2020/4/25 1:21 下午
@Author : Domionlu
@Site : 
@File : ftx.py
"""
import os, sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

import json
import copy
import hmac
import hashlib
from urllib.parse import urljoin
import requests
from aq.engine.baseBroke import BaseBroker
from aq.common.constant import *
from aq.common import tools
from aq.common.logger import log
from aq.engine.event import EventEngine
from aq.common.websocket import WebsocketClient
from requests import Request, Session
from collections import defaultdict, deque
from typing import DefaultDict, Deque, List, Dict
from aq.common.object import *
from aq.common.tools import *
import time
import traceback

param = {
        "api":{
            "exchangeInfo": "/exchangeInfo",
            "account": "/account",
            "cancel_orders":"/ordres"
        },
        "resthost":  "https://ftx.com/api",
        "wshost":"wss://ftexchange.com/ws/",
        "channels": {"orderbook": "orderbook",
                    "ticker": "ticker",
                    "trades": "trades",
                    "fills": "fills",
                    "orders": "orders"},
        "exceptions":{
                    'Not enough balances': 'Not enough balances',  # {"error":"Not enough balances","success":false}
                    'InvalidPrice': 'InvalidPrice',  # {"error":"Invalid price","success":false}
                    'Size too small': 'Size too small',  # {"error":"Size too small","success":false}
                    'Missing parameter price': 'Missing parameter price',  # {"error":"Missing parameter price","success":false}
                    'Order not found': 'Order not found',  # {"error":"Order not found","success":false}

                    'Invalid parameter': 'Invalid parameter',  # {"error":"Invalid parameter start_time","success":false}
                    'The requested URL was not found on the server': 'The requested URL was not found on the server',
                    'No such coin': 'No such coin',
                    'No such market':  'No such market',
                    'An unexpected error occurred': 'An unexpected error occurred',  # {"error":"An unexpected error occurred, please try again later(58BC21C795).","success":false}
                }
    }
class Ftx(BaseBroker):
    name = "FTX"
    BrokerType = Product.FUTURES  # 交易类型，现货，杠杆，合约


    def __init__(self, event_engine, api_key=None, api_secret=None):
        super().__init__(event_engine)
        self.event_engine = event_engine

        self.API_KEY = api_key
        self.API_SECRET = api_secret
        subscribe = {"orders": self.on_order,"fills":self.on_order}
        self.host=param.get("resthost","")
        self.ws =None
        self.session = self._init_session()

    def subscribe(self,subscribes,symbols):
        self.ws = FTXWebsocket(api_key=self.API_KEY,api_secret=self.API_SECRET,param=param,subscribes=subscribes,symbols=symbols)

    def _init_session(self):
        session = Session()
        session.headers.update({'Accept': 'application/json',
                                'User-Agent': 'FTX/python',
                                'FTX-KEY': self.API_KEY})
        return session

    def request(self, method, url, auth, **kwargs):
        request = Request(method, self.host + url, **kwargs)
        self._sign_request(request)
        response = self.session.send(request.prepare())
        return self._handel_request(response)

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self.API_SECRET.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self.API_KEY
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
    def on_order(self,msg):
        log.info(f"on_order:{msg}")

    def get_user_account(self):
        """Get user account information.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        url = "/account"
        ts = tools.get_cur_timestamp_ms()
        params = None
        success, error = self.request("get", url, params, auth=True)
        return success, error

    def create_order(self, action, symbol, quantity,price, order_type=OrderType.LIMIT, tif=Timeinforce.GTC,
                     client_id=None, reduceOnly=False):

        """Create an order.
        Args:
            action: Trade direction, `BUY` or `SELL`.
            symbol: Symbol name, e.g. `BTCUSDT`.
            price: Price of each contract.
            quantity: The buying or selling quantity.
            client_order_id: Client order id.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        ioc = False
        post = False
        if tif == Timeinforce.IOC:
            ioc = False
        elif tif == Timeinforce.POST:
            post = True
        url = "/orders"
        data = {
            "market": symbol,
            "side": action.lower(),
            "price": price,
            "type": order_type.value.lower(),
            "size": quantity,
            "reduceOnly": reduceOnly,
            "ioc": ioc,
            "postOnly": post,
            "clientId": client_id,
        }
        data = self.request("post", url, auth=True, json=data)
        return data

    def buy(self, symbol, quantity, price=None):
        if price:
            return self.create_order(BUY, symbol, quantity, price)
        else:
            return self.create_order(BUY, symbol, quantity, order_type=OrderType.MARKET)

    def sell(self, symbol, quantity, price=None):
        if price:
            return self.create_order(SELL, symbol, quantity, price)
        else:
            return self.create_order(SELL, symbol, quantity, order_type=OrderType.MARKET)

    def get_trades(self):

        pass

    def update_orderbook(self,data):
        self.ask=data['ask']
        self.bid=data['bid']
        self.bid_price = float(list(self.bid.keys())[0])
        self.ask_price = float(list(self.ask.keys())[0])
        self.mid_price=(self.ask_price+self.bid_price)/2

    def get_positions(self,symbol):
        """"
            {
      "success": true,
      "result": [
        {
          "cost": -31.7906,
          "entryPrice": 138.22,
          "estimatedLiquidationPrice": 152.1,
          "future": "ETH-PERP",
          "initialMarginRequirement": 0.1,
          "longOrderSize": 1744.55,
          "maintenanceMarginRequirement": 0.04,
          "netSize": -0.23,
          "openSize": 1744.32,
          "realizedPnl": 3.39441714,
          "shortOrderSize": 1732.09,
          "side": "sell",
          "size": 0.23,
          "unrealizedPnl": 0
        }
      ]
    }
        """
        url = "/positions"
        ts = tools.get_cur_timestamp_ms()
        params = None
        success, data = self.request("get", url, params, auth=True)
        if success:
            for d in data['result']:
                p = Position()
                p.broker = self.name
                p.symbol = d['future']
                p.qty = d['size']
                p.direction = Direction.LONG if d['side'] =='buy' else Direction.SHORT
                p.price = d['entryPrice']
                p.liquidation_Price = d['estimatedLiquidationPrice']
                self.positions[p.symbol] = p
        if symbol:
            return self.positions[symbol]
        else:
            return self.positions




    def parse_order(self,data):
        """
                {
          "success": true,
          "result": {
            "createdAt": "2019-03-05T09:56:55.728933+00:00",
            "filledSize": 0,
            "future": "XRP-PERP",
            "id": 9596912,
            "market": "XRP-PERP",
            "price": 0.306525,
            "remainingSize": 31431,
            "side": "sell",
            "size": 31431,
            "status": "open",
            "type": "limit",
            "reduceOnly": false,
            "ioc": false,
            "postOnly": false,
            "clientId": null,
          }
        }
        :param data:
        :return:
        """
        #todo 解析下单接口返回数据转换成Order对象
        data=data['result']
        o = Order()
        o.symbol = data['market']
        o.broker = self.name
        o.order_id = data['id']
        o.broker_type = Product.FUTURES
        o.time = get_cur_timestamp_ms()
        o.side = data['side']
        o.type = data['type']
        o.price = data['price']
        o.qty = data['size']
        o.filled_qty = data['filledSize']
        o.avg_price = data['']
        o.status = data['avgFillPrice']
        return o

    def cancel_order(self,symbol, order_id=None):
        url='/orders/'+str(order_id)
        data={}
        data = self.request("delete", url, auth=True, json=data)
        return data


    def cancel_all_order(self, symbol):
        url = '/orders'
        data = {"market": symbol}
        data = self.request("delete", url, auth=True, json=data)
        return data

    def get_open_order(self, symbol, order_id=None):
        pass

    def get_open_orders(self, symbol):
        pass

    def signature(self, data, auth=False):
        if data:
            query = "&".join(["=".join([str(k), str(v)]) for k, v in data.items()])
        else:
            query = ""
        if auth and query:
            sign = hmac.new(self.API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
            query += "&signature={s}".format(s=sign)
        return query


class FTXWebsocket(WebsocketClient):
    """ FTX Trade module. You can initialize trader object with some attributes in kwargs.
    """
    host = "wss://ftexchange.com/ws/"

    def __init__(self, **kwargs):
        """Initialize."""
        param= kwargs.get("param", {})
        self.host=param.get("wshost","")
        self.chanels=param.get("channels",{})
        self.subscribes = kwargs.get("subscribes", {})
        super().__init__()
        self._fills: Deque = deque([], maxlen=10000)
        self._orders: [int, Dict] = defaultdict(dict)
        self._api_key = kwargs.get("api_key", None)
        self._api_secret = kwargs.get("api_secret", None)
        self.symbols = kwargs.get("symbols", ["BTC-PERP"])
        self.connect()
        self.login()
        self.subscribe(self.subscribes)


    def _on_message(self, ws, message):
        # log.debug(f"on_msg:{message}")
        message = json.loads(message)
        message_type = message['type']
        if message_type in {'subscribed', 'unsubscribed'}:
            return
        elif message_type == 'info':
            if message['code'] == 20001:
                return self.reconnect()
        elif message_type == 'error':
            raise Exception(message)
        if message =="pong":
            log.debug(message)
            pass
        channel = message.get('channel',None)

        if channel == 'orderbook':
            self.orderbook_message(message)
        elif channel == 'trades':
            self.trades_message(message)
        elif channel == 'ticker':
            self.ticker_message(message)
        elif channel == 'fills':
            self.fills_message(message)
        elif channel == 'orders':
            self.orders_message(message)


    def orderbook_message(self, message):
        f = self.subscribes.get("orderbook",None)
        f(message)
        pass

    def trades_message(self, message):
        f = self.subscribes.get("trades",None)
        f(message)
        pass

    def ticker_message(self, message):
        f = self.subscribes.get("ticker",None)
        f(message)
        pass

    def fills_message(self, message):
        """
        {
          "channel": "fills",
          "data": {
            "fee": 78.05799225,
            "feeRate": 0.0014,
            "future": "BTC-PERP",
            "id": 7828307,
            "liquidity": "taker",
            "market": "BTC-PERP",
            "orderId": 38065410,
            "tradeId": 19129310,
            "price": 3723.75,
            "side": "buy",
            "size": 14.973,
            "time": "2019-05-07T16:40:58.358438+00:00",
            "type": "order"
          },
          "type": "update"
        }
        :param message:
        :return:
        """
        try:
            m = message['data']
            o = Order()
            o.symbol = m['market']
            o.broker = "FTX"
            o.order_id = m['id']
            o.broker_type = Product.FUTURES
            o.time = get_cur_timestamp_ms()
            o.side = m['side']
            o.type = m['type']
            o.price = m['price']
            o.qty = m['size']
            o.filled_qty = m['filledSize']
            o.avg_price = m['']
            o.status = m['avgFillPrice']
            self._orders.update({o.orderid: o})
            f = self.subscribes.get("orders", None)
            f(o)
        except Exception as e:
            log.error(traceback.format_exc())
            f = self.subscribes.get("orders", None)
            f(message)

    def orders_message(self, message):
        """
        {
          "channel": "orders",
          "data": {
            "id": 24852229,
            "clientId": null,
            "market": "XRP-PERP",
            "type": "limit",
            "side": "buy",
            "size": 42353.0,
            "price": 0.2977,
            "reduceOnly": false,
            "ioc": false,
            "postOnly": false,
            "status": "closed",
            "filledSize": 0.0,
            "remainingSize": 0.0,
            "avgFillPrice": 0.2978
          },
          "type": "update"
        }
        :param message:
        :return:
        """
        try:
            m = message['data']
            o=Order()
            o.symbol=m['market']
            o.broker="FTX"
            o.order_id=m['id']
            o.broker_type = Product.FUTURES
            o.time=get_cur_timestamp_ms()
            o.side=m['side']
            o.type=m['type']
            o.price=m['price']
            o.qty=m['size']
            o.filled_qty=m['filledSize']
            o.avg_price=m['avgFillPrice']
            o.status=m['status']
            self._orders.update({o.order_id:o})
            f = self.subscribes.get("orders", None)
            f(o)
        except Exception as e:
            log.error(traceback.format_exc())
            f = self.subscribes.get("orders", None)
            f(message)
        pass

    def _get_url(self):
        return self.host

    def login(self) -> None:
        if self._api_key:
            ts = int(time.time() * 1000)
            self.send_json({'op': 'login', 'args': {
                'key': self._api_key,
                'sign': hmac.new(
                    self._api_secret.encode(), f'{ts}websocket_login'.encode(), 'sha256').hexdigest(),
                'time': ts,
            }})
            self._logged_in = True
            log.debug("login")


    def subscribe(self, channels):
        for k in channels.keys():
            c=self.chanels.get(k,"")
            for symbol in self.symbols:
                log.debug(f"subscrpbe:{c}:{symbol}")
                self.send_json({'op': 'subscribe', "channel":c, "market": symbol})

            self.subscribes[k] = channels[k]

    def _ping(self,ws):
        timeout = 30
        count = 0
        while self.ws:
            if count < timeout:
                time.sleep(1)
                count = count + 1
            else:
                log.debug("ping")
                self.send_json({'op':'ping'})
                count=0


def orders(msg):
    log.info(msg)


if __name__ == "__main__":
    ev=EventEngine()
    key = "rOGo6rIk5OtpapkKTmvsPLT6mtKGmtJm9hzuy8Bu"
    secret = "mjLHNaokSQOZiPBtYnAtHynV6Y__UxMbh8s9NzRG"
    f=Ftx(ev,key,secret)
    # f.subscribe()
    time.sleep(1)
    f.cancel_all_order("BTC-PERP")
    for y in range(10):
        log.info("Start buy")
        i=f.buy("BTC-PERP",6000,0.01)
        log.info("end buy")
        # if "success" in i and i["success"]:
        #     orderid=i["result"]['id']
        #     f.cancel_order(orderid)
        # else:
        #     print(i)
        #
    # f = FTXWebsocket(api_key=key, api_secret=secret,param=param,subscribes={"trades":orders})
    # subscribe = {"orders": orders}
    # f.subscribe(subscribe)
    while True:
        time.sleep(1)
    pass
