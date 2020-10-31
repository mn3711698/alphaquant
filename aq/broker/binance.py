# -*- coding:utf-8 -*-
"""
@Time : 2020/4/25 1:17 下午
@Author : Domionlu
@Site : https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md
@File : binancefutures.py
"""
import os, sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')
from apscheduler.schedulers.blocking import BlockingScheduler
import json
import copy
import hmac
import hashlib
from urllib.parse import urljoin
import requests
from aq.engine.baseBroke import BaseBroker
from aq.common import tools
from aq.engine.event import EventEngine
from aq.common.logger import log
from aq.common.aqwebsocket import WebsocketClient
import time
from aq.common.object import *
import traceback
import pandas as pd
from aq.broker.binancefutures import BinanceFutures


# proxies = {"http": "http://127.0.0.1:1087", "https": "http://127.0.0.1:1087"}
# proxies={"host":"127.0.0.1","port":"1087"}

# sched = BlockingScheduler()


class Binance(BinanceFutures):
    name = "BINANCE"
    BrokerType = Product.CASH  # 交易类型，现货，杠杆，合约

    positions = {}

    param = {
        "api": {
            "exchangeInfo": "/api/v3/exchangeInfo",
            "account": "/api/v3/account",
            "orderbook": "/api/v3/depth",
            "order": "/api/v1/order",
            "open_order": "/api/v1/openOrder",
            "open_orders": "/api/v1/openOrders",
            "balance": "/api/v3/account",
            "kline": "/api/v3/klines",
            "listenkey": "/api/v1/listenKey"
        },
        "resthost": "https://api.binance.com",
        "wshost": "wss://stream.binance.com:9443/ws",
        "channels": {"orderbook": "depth",
                     "ticker": "ticker",
                     "kline_1m": "kline_1m",
                     "kline_5m": "kline_5m",
                     "trades": "aggTrade",
                     "account": "account",
                     "order": "order",
                     "forceOrder": "forceOrder"},
        "exceptions": {

        }

    }

    def __init__(self, event_engine, api_key=None, api_secret=None):
        super().__init__(event_engine)
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.host = self.param.get("resthost", "")
        self.session = self._init_session()
        self._refresh_interval = 60
        self._last_update_id = 0
        self.bid_price = 0
        self.ask_price = 0
        self._orders = {}
        self.ws = None
        self.scheduler = BlockingScheduler()
        subscribes = {ORDERBOOK: self.on_orderbook,
                      TRADES: self.on_trades,
                      TICKER: self.on_ticker,
                      KLINE1: self.on_bar,
                      KLINE5: self.on_bar,
                      FORCEORDER: self.on_forceOrder,
                      ACCOUNT: self.on_position,
                      ORDER: self.on_orders}
        self.param["callback"] = subscribes

    def start(self, sybmol, subscribes):
        self.symbol = sybmol.lower()
        self.depth = DepthCache(self.symbol)
        # subscribes = {"orderbook": self.on_orderbook,"trades":self.on_trades}
        sub = {}
        for s in subscribes:
            if s in {"account", "order"}:
                if self.API_KEY:
                    sub[s] = self.param["callback"].get(s, None)
                else:
                    log.error(f"未设置API key,忽略{s}")
            else:
                sub[s] = self.param["callback"].get(s, None)
        self.subscribe([self.symbol], sub)

    def subscribe(self, symbols, subscribes):
        self.ws = BinanceWebsocket(rest=self, param=self.param, subscribes=subscribes, symbols=symbols)

    def _init_session(self):
        session = requests.session()
        session.headers.update({'Accept': 'application/json',
                                'User-Agent': 'binance/python',
                                'X-MBX-APIKEY': self.API_KEY})
        return session

    def on_forceOrder(self, data):
        self.on_event(FORCEORDER, data)

    def on_position(self, data):
        """
                {
                  "e": "ACCOUNT_UPDATE",                // 事件类型
                  "E": 1564745798939,                   // 事件时间
                  "T": 1564745798938 ,                  // 撮合时间
                  "a":                                  // 账户更新事件
                    {
                      "B":[                             // 余额信息
                        {
                          "a":"USDT",                   // 资产名称
                          "wb":"122624.12345678",       // 钱包余额
                          "cw":"100.12345678"           // 除去逐仓保证金的钱包余额
                        },
                        {
                          "a":"BNB",
                          "wb":"1.00000000",
                          "cw":"0.00000000"
                        }
                      ],
                      "P":[
                        {
                          "s":"BTCUSDT",            // 交易对
                          "pa":"1",                 // 仓位
                          "ep":"9000",              // 入仓价格
                          "cr":"200",               // (费前)累计实现损益
                          "up":"0.2732781800",      // 持仓未实现盈亏
                          "mt":"isolated",          // 保证金模式
                          "iw":"0.06391979"         // 若为逐仓，仓位保证金
                        }
                      ]
                    }
                }
                :param msg:
                :return:
                """
        asset = data['a']['B']
        if self.balances:
            for a in asset:
                ba = Balance(a['wb'], a['cw'])
                self.balances[a['a']] = ba
        else:
            self.get_balnce()
        pdata = data['a']['P']
        log.info(f"持仓变化信息{pdata}")
        # if self.positions:
        #     self.get_positions()
        position = None
        for d in pdata:
            p = Position()
            p.symbol = d['s']
            if d['ps'] == "LONG":
                p.direction = Direction.LONG
            elif d['ps'] == "SHORT":
                p.direction = Direction.SHORT
            if d['ps'] == "BOTH":
                p.direction = Direction.BOTH
            p.qty = float(d['pa'])
            if float(d['pa']) != 0:
                p.price = float(d['ep'])
            # log.info(f"更新持仓{p}")
            # log.info(p)
            position = self.positions.get(p.symbol, [])
            # log.info(f"当前持仓{position}")
            for i in position[::-1]:
                if p.direction == i.direction and p.symbol == i.symbol:
                    position.remove(i)
            position.append(p)
            # log.info(f"更新后持仓{position}")
            self.positions[p.symbol] = position
        log.info(self.positions)
        self.on_event(POSITION, position)
        self.on_event(BALANCE, self.balances)

    def _init_depth(self):
        log.info("初始化深度")
        res = self.get_order_book(self.symbol)
        for bid in res['bids']:
            self.depth.add_bid(bid)
        for ask in res['asks']:
            self.depth.add_ask(ask)
        self.update_orderbook()

        # set first update id
        # log.info(res)
        # self._last_update_id = res['lastUpdateId']

    def on_orderbook(self, msg):
        if msg['u'] <= self._last_update_id:
            # ignore any updates before the initial update id
            return
        # log.info(f"更新前ID{self._last_update_id}")
        for bid in msg['b']:
            self.depth.add_bid(bid)
        for ask in msg['a']:
            self.depth.add_ask(ask)
        newid = msg['u']
        if msg['pu'] != self._last_update_id:
            self._init_depth()
        self.depth.update_time = msg['E']
        self._last_update_id = newid
        # log.info(msg)
        # log.info(f"最后ID{msg['u']}")
        # log.info(f"更新后ID{self._last_update_id}")

        # log.info(msg['u'])
        # log.info(self._last_update_id)
        # after processing event see if we need to refresh the depth cache
        # if self._refresh_interval and int(time.time()) > self._refresh_time:
        #     self._init_depth()
        # log.info(msg)
        self.update_orderbook()
        self.on_event(ORDERBOOK, self.depth)

    def on_trades(self, data):
        """
        {
          "e": "aggTrade",  // 事件类型
          "E": 123456789,   // 事件时间
          "s": "BNBBTC",    // 交易对
          "a":
          "p": "0.001",     // 成交价格
          "q": "100",       // 成交数量
          "f": 100,         // 被归集的首个交易ID
          "l": 105,         // 被归集的末次交易ID
          "T": 123456785,   // 成交时间
          "m": true         // 买方是否是做市方。如true，则此次成交是一个主动卖出单，否则是一个主动买入单。
        }
        :param message:
        :return:
        """
        self.on_event(TRADES, data)
        # print(data)
        # try:
        #     m=data['o']
        #     t=Trade()
        #     t.symbol=m['s']
        #     t.price=m['p']
        #     t.qty=m['q']
        #     t.side=TAKER if m['m'] else MAKER
        #     t.time=m['T']
        #
        # except Exception as e :
        #     log.error(traceback.format_exc())

    def on_orders(self, data):
        """
       { "e":"ORDER_TRADE_UPDATE",         // 事件类型
      "E":1568879465651,                // 事件时间
      "T":1568879465650,                // 撮合时间
      "o":{
    "s":"BTCUSDT",                  // 交易对
    "c":"TEST",                     // 客户端自定订单ID
      // 特殊的自定义订单ID:
      // "autoclose-"开头的字符串: 系统强平订单
      // "adl_autoclose": ADL自动减仓订单
    "S":"SELL",                     // 订单方向
    "o":"LIMIT",                    // 订单类型
    "f":"GTC",                      // 有效方式
    "q":"0.001",                    // 订单原始数量
    "p":"9910",                     // 订单原始价格
    "ap":"0",                       // 订单平均价格
    "sp":"0",                       // 订单停止价格
    "x":"NEW",                      // 本次事件的具体执行类型
    "X":"NEW",                      // 订单的当前状态
    "i":8886774,                    // 订单ID
    "l":"0",                        // 订单末次成交数量
    "z":"0",                        // 订单累计已成交数量
    "L":"0",                        // 订单末次成交价格
    "N": "USDT",                    // 手续费资产类型
    "n": "0",                       // 手续费数量
    "T":1568879465651,              // 成交时间
    "t":0,                          // 成交ID
    "b":"0",                        // 买单净值
    "a":"9.91"                      // 卖单净值
    "m": false,                     // 该成交是作为挂单成交吗？
    "R":false,                      // 是否是只减仓单
    "wt": "CONTRACT_PRICE",         // 触发价类型
    "cp":false,                     // 是否为触发平仓单; 仅在条件订单情况下会推送此字段
    "AP":"7476.89",                 // 追踪止损激活价格, 仅在追踪止损单时会推送此字段
    "cr":"5.0"                      // 追踪止损回调比例, 仅在追踪止损单时会推送此字段
  }
        :param message:
        :return:
        """
        m = data['o']
        o = Order()
        o.symbol = m['s']
        o.broker = "BINANCE_FUTURES"
        o.order_id = m['i']
        o.broker_type = Product.FUTURES
        o.time = m['T']
        o.order_id = m["i"]
        o.side = m['S']
        o.type = m['o']
        o.price = float(m['p'])
        o.qty = float(m['q'])
        o.avg_price = float(m['ap'])
        o.status = m['X']
        o.fee = m.get('n', 0)
        self._orders.update({o.order_id: o})
        self.on_event(ORDER, o)

    def on_bar(self, data):
        self.on_event(KLINE, data)

    def on_ticker(self, data):
        # {
        #     "e": "24hrTicker", // 事件类型
        # "E": 123456789, // 事件时间
        # "s": "BNBBTC", // 交易对
        # "p": "0.0015", // 24小时价格变化
        # "P": "250.00", // 24小时价格变化（百分比）
        # "w": "0.0018", // 平均价格
        # "c": "0.0025", // 最新成交价格
        # "Q": "10", // 最新成交价格上的成交量
        # "o": "0.0010", // 24小时内第一比成交的价格
        # "h": "0.0025", // 24小时内最高成交价
        # "l": "0.0010", // 24小时内最低成交加
        # "v": "10000", // 24小时内成交量
        # "q": "18", // 24小时内成交额
        # "O": 0, // 统计开始时间
        # "C": 86400000, // 统计关闭时间
        # "F": 0, // 24小时内第一笔成交交易ID
        # "L": 18150, // 24小时内最后一笔成交交易ID
        # "n": 18151 // 24小时内成交数
        # }
        # log.info(data)

        self.on_event(TICKER, data)

    def update_orderbook(self):
        # log.info(self.depth.bids())
        # log.info(self.depth.asks())
        self.bid_price = float(self.depth.bids()[0][0])
        self.ask_price = float(self.depth.asks()[0][0])
        self.mid_price = round((self.bid_price + self.ask_price) / 2, 4)

    #
    # def on_order(self,msg):
    #     log.info(f"on_order:{msg}")
    def get_depth(self, symbol):
        data = self.get_order_book(symbol)
        db = DepthCache(symbol)
        for bid in data['bids']:
            db.add_bid(bid)
        for ask in data['asks']:
            db.add_ask(ask)
        self.bid = db.bids()
        self.ask = db.asks()
        return self.bid, self.ask

    def get_order_book(self, symbol, limit=500):
        url = self.param['api'].get("orderbook", None)
        # uri = "/api/v3/depth"
        data = {
            "symbol": symbol,
            "limit": limit,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        data = self.request("get", url, body=data, auth=False)
        return data

    def get_user_account(self):
        """Get user account information.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        url = self.param['api'].get("account", None)
        # uri = "/api/v3/account"
        ts = tools.get_cur_timestamp_ms()
        params = {
            "timestamp": str(ts)
        }
        success, error = self.request("get", url, params, auth=True)
        return success, error

    def create_order(self, action, symbol, quantity, price=None, order_type=OrderType.LIMIT, reduceOnly=False,
                     tif=None,
                     position_side="BOTH", client_id=None):
        """Create an order.
        LIMIT_MAKER are LIMIT orders that will be rejected if they would immediately match and trade as a taker.
        STOP_LOSS and TAKE_PROFIT will execute a MARKET order when the stopPrice is reached.
        Any LIMIT or LIMIT_MAKER type order can be made an iceberg order by sending an icebergQty.
        Any order with an icebergQty MUST have timeInForce set to GTC.
        MARKET orders using quantity specifies how much a user wants to buy or sell based on the market price.
        MARKET orders using quoteOrderQty specifies the amount the user wants to spend (when buying) or receive (when selling) of the quote asset; the correct quantity will be determined based on the market liquidity and quoteOrderQty.
        MARKET orders using quoteOrderQty will not break LOT_SIZE filter rules; the order will execute a quantity that will have the notional value as close as possible to quoteOrderQty.
        """
        url = self.param['api'].get("order", None)

        # url = "/fapi/v1/order"
        data = {
            "symbol": symbol,
            "side": action,
            "type": order_type.name.upper(),
            "positionSide": position_side,
            "quantity": quantity,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        if tif != None:
            data["timeInForce"] = tif.name
        if reduceOnly:
            data["reduceOnly"] = reduceOnly
        if price:
            data["price"] = price
        if client_id:
            data["newClientOrderId"] = client_id
        # log.info(f"{symbol},{action},{quantity},{price}")
        log.info(data)
        return self.request("post", url, body=data, auth=True)

    def buy(self, symbol, quantity, price=None, position_side="BOTH", tif=Timeinforce.GTC):
        if price:
            order = self.create_order(BUY, symbol, quantity, price, position_side=position_side, tif=tif)
        else:
            order = self.create_order(BUY, symbol, quantity, order_type=OrderType.MARKET, position_side=position_side,
                                      tif=tif)

        return self.parse_order(order)

    def sell(self, symbol, quantity, price=None, position_side="BOTH", tif=Timeinforce.GTC):
        if price:
            order = self.create_order(SELL, symbol, quantity, price, position_side=position_side, tif=tif)
        else:
            order = self.create_order(SELL, symbol, quantity, order_type=OrderType.MARKET, position_side=position_side,
                                      tif=tif)
        return self.parse_order(order)

    def parse_order(self, data):
        """
            {
        "clientOrderId": "testOrder", // 用户自定义的订单号
        "cumQuote": "0", // 成交金额
        "executedQty": "0", // 成交数量
        "orderId": 22542179, // 系统订单号
        "origQty": "10", // 原始委托数量
        "price": "0", // 委托价格
        "reduceOnly": false, // 仅减仓
        "side": "SELL", // 买卖方向
        "positionSide": "SHORT", // 持仓方向
        "status": "NEW", // 订单状态
        "stopPrice": "0", // 触发价，对`TRAILING_STOP_MARKET`无效
        "symbol": "BTCUSDT", // 交易对
        "timeInForce": "GTC", // 有效方法
        "type": "TRAILING_STOP_MARKET", // 订单类型
        "activatePrice": "9020", // 跟踪止损激活价格, 仅`TRAILING_STOP_MARKET` 订单返回此字段
        "priceRate": "0.3", // 跟踪止损回调比例, 仅`TRAILING_STOP_MARKET` 订单返回此字段
        "updateTime": 1566818724722, // 更新时间
        "workingType": "CONTRACT_PRICE" // 条件价格触发类型
    }
        :param data:
        :return:
        """
        # print(data)
        if "code" in data:
            log.error(data)
            return None
        else:
            o = Order()
            o.order_id = data["orderId"]
            o.broker = self.name
            o.symbol = data['symbol']
            o.price = float(data['price'])
            o.qty = float(data['origQty'])
            o.filled_qty = float(data['executedQty'])
            o.time = data['updateTime']
            o.side = data['side']
            o.reduce = data['reduceOnly']
            o.tif = data['timeInForce']
            o.stopPrice = float(data["stopPrice"])
            o.direction = data['positionSide']
            return o

    def get_trades(self, symbol, order_id=None):
        url = self.param['api'].get("order", None)
        # uri = "/fapi/v1/order"
        data = {
            "symbol": symbol,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        if order_id:
            data["orderId"] = order_id
        return self.request("get", url, body=data, auth=True)

    def get_open_order(self, symbol, order_id=None):
        url = self.param['api'].get("open_order", None)
        # uri = "/fapi/v1/openOrder"
        data = {
            "symbol": symbol,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        if order_id:
            data["orderId"] = order_id
        return self.request("get", url, body=data, auth=True)

    def get_open_orders(self, symbol):
        url = self.param['api'].get("open_orders", None)
        # uri = "/fapi/v1/openOrders"
        data = {
            "symbol": symbol,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        return self.request("get", url, body=data, auth=True)

    def get_positions(self, symbol=None):
        self._get_positions(symbol)
        # log.info(self.positions)
        return self.positions.get(symbol, [])

    def _get_positions(self, symbol=None):
        """"
                [
            {
                "entryPrice": "0.00000", // 开仓均价
                "marginType": "isolated", // 逐仓模式或全仓模式
                "isAutoAddMargin": "false",
                "isolatedMargin": "0.00000000", // 逐仓保证金
                "leverage": "10", // 当前杠杆倍数
                "liquidationPrice": "0", // 参考强平价格
                "markPrice": "6679.50671178",   // 当前标记价格
                "maxNotionalValue": "20000000", // 当前杠杆倍数允许的名义价值上限
                "positionAmt": "0.000", // 头寸数量，符号代表多空方向, 正数为多，负数为空
                "symbol": "BTCUSDT", // 交易对
                "unRealizedProfit": "0.00000000", // 持仓未实现盈亏
                "positionSide": "BOTH", // 持仓方向
            },
            {
                "entryPrice": "6563.66500", // 开仓均价
                "marginType": "isolated", // 逐仓模式或全仓模式
                "isAutoAddMargin": "false",
                "isolatedMargin": "15517.54150468", // 逐仓保证金
                "leverage": "10", // 当前杠杆倍数
                "liquidationPrice": "5930.78", // 参考强平价格
                "markPrice": "6679.50671178",   // 当前标记价格
                "maxNotionalValue": "20000000", // 当前杠杆倍数允许的名义价值上限
                "positionAmt": "20.000", // 头寸数量，符号代表多空方向, 正数为多，负数为空
                "symbol": "BTCUSDT", // 交易对
                "unRealizedProfit": "2316.83423560" // 持仓未实现盈亏
                "positionSide": "LONG", // 持仓方向
            },
            {
                "entryPrice": "0.00000", // 开仓均价
                "marginType": "isolated", // 逐仓模式或全仓模式
                "isAutoAddMargin": "false",
                "isolatedMargin": "5413.95799991", // 逐仓保证金
                "leverage": "10", // 当前杠杆倍数
                "liquidationPrice": "7189.95", // 参考强平价格
                "markPrice": "6679.50671178",   // 当前标记价格
                "maxNotionalValue": "20000000", // 当前杠杆倍数允许的名义价值上限
                "positionAmt": "-10.000", // 头寸数量，符号代表多空方向, 正数为多，负数为空
                "symbol": "BTCUSDT", // 交易对
                "unRealizedProfit": "-1156.46711780" // 持仓未实现盈亏
                "positionSide": "SHORT", // 持仓方向
            }

        ]
         """
        uri = "/fapi/v1/positionRisk"
        data = {
            "timestamp": tools.get_cur_timestamp_ms()
        }
        data = self.request("get", uri, body=data, auth=True)
        position = {}
        if isinstance(data, list):
            log.info("is list")
            for d in data:
                if float(d['positionAmt']) != 0:
                    p = Position()
                    p.broker = self.name
                    p.symbol = d['symbol']
                    p.qty = float(d['positionAmt'])
                    if d['positionSide'] == "BOTH":
                        p.direction = Direction.LONG if p.qty > 0 else Direction.SHORT
                    else:
                        p.direction = Direction.LONG if d['positionSide'] == "LONG" else Direction.SHORT
                    p.price = float(d['entryPrice'])
                    p.liquidation_Price = float(d['liquidationPrice'])
                    if p.symbol in position:
                        position[p.symbol].append(p)
                    else:
                        position[p.symbol] = []
                        position[p.symbol].append(p)
                    # log.info("新增加持仓记录")
                    # log.info(p)
            self.positions = position
        else:
            log.info(f"无效持仓 {data}")
        if symbol:
            # log.info(self.positions)
            # log.info(symbol)
            return self.positions.get(symbol, [])

    def get_balnce(self, symbol=None):
        url = self.param['api'].get("balance", None)
        # uri = "/fapi/v1/balance"
        data = {
            "timestamp": tools.get_cur_timestamp_ms()
        }
        balance = self.request("get", url, body=data, auth=True)
        for b in balance:
            ba = Balance(b['balance'], b['withdrawAvailable'])
            self.balances[b['asset']] = ba
        return self.balances

    def get_bar(self, symbol, timeframe, starttime=None):
        url = self.param['api'].get("kline", None)
        # uri = "/fapi/v1/klines"
        data = {
            "symbol": symbol,
            "interval": timeframe
        }
        if starttime:
            data["startTime"] = starttime
        bar = self.request("get", url, body=data, auth=False)
        self.bars = bar
        df = pd.DataFrame(bar)
        df.columns = ['open_time',
                      'open', 'high', 'low', 'close', 'volume',
                      'close_time', 'qav', 'num_trades',
                      'taker_base_vol', 'taker_quote_vol', 'ignore']
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df['qav'] = df['qav'].astype(float)
        df['taker_base_vol'] = df['taker_base_vol'].astype(float)
        df['taker_quote_vol'] = df['taker_quote_vol'].astype(float)
        # log.info(f"bar:{bar}")
        return df


    def close_position(self, position):
        if position.direction == Direction.LONG:
            return self.sell(position.symbol, position.qty)
        else:
            return self.buy(position.symbol, position.qty)


    def close_Shortorder(self, symbol, stopprice):
        url = self.param['api'].get("order", None)
        # url = "/fapi/v1/order"
        data = {
            "symbol": symbol,
            "side": BUY,
            "type": OrderType.STOP_MARKET.name,
            "positionSide": Direction.SHORT.name,
            "stopprice": stopprice,
            "closePosition": True,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        # log.info(f"{symbol},{action},{quantity},{price}")
        # log.info(data)
        order = self.request("post", url, body=data, auth=True)
        return self.parse_order(order)


    def close_Longorder(self, symbol, stopprice):
        url = self.param['api'].get("order", None)
        # url = "/fapi/v1/order"
        data = {
            "symbol": symbol,
            "side": SELL,
            "type": OrderType.STOP_MARKET.name,
            "positionSide": Direction.LONG.name,
            "stopprice": stopprice,
            "closePosition": True,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        # log.info(f"{symbol},{action},{quantity},{price}")
        # log.info(data)
        order = self.request("post", url, body=data, auth=True)
        return self.parse_order(order)


    def cancel_order(self, symbol, order_id=None):
        # uri = "/fapi/v1/order"
        url = self.param['api'].get("order", None)
        data = {
            "symbol": symbol,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        if order_id:
            data["orderId"] = order_id
        return self.request("delete", url, body=data, auth=True)


    def cancel_all_order(self, symbol):
        uri = "/fapi/v1/allOpenOrders"
        data = {
            "symbol": symbol,
            "timestamp": tools.get_cur_timestamp_ms()
        }
        return self.request("delete", uri, body=data, auth=True)


    def signature(self, data, auth=False):
        if data:
            query = "&".join(["=".join([str(k), str(v)]) for k, v in data.items()])
        else:
            query = ""
        if auth and query:
            sign = hmac.new(self.API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
            query += "&signature={s}".format(s=sign)
        return query


    def get_listenKey(self):
        url = self.param['api'].get("listenKey", None)
        # uri = "/fapi/v1/listenKey"
        data = {
            "timestamp": tools.get_cur_timestamp_ms()
        }

        key = self.request("post", url, body=data, auth=False)
        return key


    # @sched.scheduled_job('interval', minutes=45)
    def put_listenKey(self):
        if self.API_KEY:
            url = self.param['api'].get("listenKey", None)
            data = {
                "timestamp": tools.get_cur_timestamp_ms()
            }
            return self.request("put", url, body=data, auth=False)





class BinanceWebsocket(WebsocketClient):
    """ Binance Trade module. You can initialize trader object with some attributes in kwargs.
    """
    host = "wss://fstream.binance.com/ws/"

    def __init__(self, **kwargs):
        """Initialize."""
        super().__init__()
        param = kwargs.get("param", {})
        self.host = param.get("wshost", "")
        self.chanels = param.get("channels", {})
        self.subscribes = kwargs.get("subscribes", {})
        self.rest = kwargs.get("rest", None)
        self.listenKey = ""
        self.symbols = kwargs.get("symbols", ["btcusdt"])
        self.connect()

        self.subscribe(self.subscribes)

    def _on_message(self, ws, msg):
        try:
            message = json.loads(msg)
            channel = message.get('e')
            if channel == "depthUpdate":
                f = self.subscribes.get("orderbook", None)
                f(message)
            elif channel == 'depth':
                f = self.subscribes.get("orderbook", None)
                f(message)
            elif channel == 'aggTrade':
                f = self.subscribes.get("trades", None)
                f(message)

            elif channel == '24hrTicker':
                f = self.subscribes.get("ticker", None)
                f(message)
            elif channel == 'ACCOUNT_UPDATE':
                f = self.subscribes.get("account", None)
                f(message)
            elif channel == 'ORDER_TRADE_UPDATE':
                f = self.subscribes.get("order", None)
                f(message)
            elif channel == 'forceOrder':
                f = self.subscribes.get("forceOrder", None)
                f(message)
            elif channel == 'kline':
                k = message["k"]
                i = k["i"]
                # log.info(self.subscribes)
                f = self.subscribes.get("kline_" + i, None)
                f(message)
            else:
                log.error(f"未知消息类型:{msg}")
        except Exception as e:
            log.error(traceback.format_exc())

    def _get_url(self):
        try:
            self.listenKey = self.rest.get_listenKey()
            return self.host + "/" + self.listenKey["listenKey"]
        except Exception as e:
            log.info("获取listenkey异常")
            return self.host

    def _subscribe(self) -> None:
        self.subscribe(self.subscribes)

    def subscribe(self, channels):
        for k in channels.keys():
            c = self.chanels.get(k, "")
            for symbol in self.symbols:
                req = {
                    "method": "SUBSCRIBE",
                    "params": [f'{symbol}@{c}'],
                    "id": 1
                }
                log.info(req)
                self.send_json(req)
            self.subscribes[k] = channels[k]

    def _ping(self, ws):
        pass
        # timeout = 30
        # count = 0
        # while self.ws:
        #     if count < timeout:
        #         time.sleep(1)
        #         count = count + 1
        #     else:
        #         log.debug("ping")
        #         self.send_json({'op': 'ping'})
        #         count = 0


from operator import itemgetter


class DepthCache(object):
    def __init__(self, symbol):
        """Initialise the DepthCache
        :param symbol: Symbol to create depth cache for
        :type symbol: string
        """
        self.symbol = symbol
        self._bids = {}
        self._asks = {}
        self.update_time = None

    def add_bid(self, bid):
        """Add a bid to the cache
        :param bid:
        :return:
        """
        self._bids[bid[0]] = float(bid[1])
        if bid[1] == "0.00000000":
            del self._bids[bid[0]]

    def add_ask(self, ask):
        """Add an ask to the cache
        :param ask:
        :return:
        """
        self._asks[ask[0]] = float(ask[1])
        if ask[1] == "0.00000000":
            del self._asks[ask[0]]

    def bids(self):
        """Get the current bids
        :return: list of bids with price and quantity as floats
        .. code-block:: python
            [
                [
                    0.0001946,  # Price
                    45.0        # Quantity
                ],
                [
                    0.00019459,
                    2384.0
                ],
                [
                    0.00019158,
                    5219.0
                ],
                [
                    0.00019157,
                    1180.0
                ],
                [
                    0.00019082,
                    287.0
                ]
            ]
        """
        return DepthCache.sort_depth(self._bids, reverse=True)

    def asks(self):
        """Get the current asks
        :return: list of asks with price and quantity as floats
        .. code-block:: python
            [
                [
                    0.0001955,  # Price
                    57.0'       # Quantity
                ],
                [
                    0.00019699,
                    778.0
                ],
                [
                    0.000197,
                    64.0
                ],
                [
                    0.00019709,
                    1130.0
                ],
                [
                    0.0001971,
                    385.0
                ]
            ]
        """
        return DepthCache.sort_depth(self._asks, reverse=False)

    @staticmethod
    def sort_depth(vals, reverse=False):
        """Sort bids or asks by price
        """
        lst = [[float(price), quantity] for price, quantity in vals.items()]
        lst = sorted(lst, key=itemgetter(0), reverse=reverse)
        return lst


# sched.start()
# sched.print_jobs(jobstore=None, out=sys.stdout)  # 输出作业信息
# log.info("Binance定时任务启动")
def test_order():
    ev = EventEngine()
    key = "qer4Udt2tkbfOihvE5zlINiPgfmuC5hbx1SEQmmow8XXiJqZhyGwtF83VRjuIqXN"
    secret = "X7UOt9wgYNCgjuLwIKX6Taij6afQTj89mKqG4fsYqufnxqrLI2GsV5kTZ7H7u1TL"
    b = Binance(ev, key, secret)
    b.start(["BTCUSDT"])
    # success,text=b.get_user_account()
    # success, orderid = b.buy()
    while True:
        time.sleep(5)
        print(b.get_balnce("USDT"))
        print(b.get_positions("BTCUSDT", Direction.SHORT))
        print(b.get_positions("BTCUSDT", Direction.LONG))
    pass


def on_sub(event):
    data = event.data
    print(data)


def test_subscribe():
    ev = EventEngine()
    ev.start()
    b = Binance(ev)
    b.start("btcusdt", [FORCEORDER])
    ev.register(FORCEORDER, on_sub)


def teste_bar():
    ev = EventEngine()
    ev.start()
    b = Binance(ev)
    bar = b.get_bar("BTCUSDT", "15m")
    log.info(bar.tail())
    balance = b.get_balnce()
    # ev.register(FORCEORDER, on_sub)


if __name__ == "__main__":
    # test_order()
    teste_bar()
