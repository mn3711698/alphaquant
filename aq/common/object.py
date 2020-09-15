from dataclasses import dataclass
from aq.common.constant import *




@dataclass
class Bar():
    """
    Candlestick bar data of a certain trading period.
    """
    symbol: str
    exchange: Exchange
    time: float = 0
    interval: Interval = None
    volume: float = 0
    open_interest: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0



@dataclass
class Tick():
    """
    Tick data contains information about:
        * last trade in market
        * orderbook snapshot
        * intraday market statistics.
    """
    symbol: str
    broker: Exchange
    time: float = 0
    name: str = ""
    volume: float = 0
    open_interest: float = 0
    last_price: float = 0
    last_volume: float = 0
    limit_up: float = 0
    limit_down: float = 0

    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    pre_close: float = 0

    bid_price_1: float = 0
    bid_price_2: float = 0
    bid_price_3: float = 0
    bid_price_4: float = 0
    bid_price_5: float = 0

    ask_price_1: float = 0
    ask_price_2: float = 0
    ask_price_3: float = 0
    ask_price_4: float = 0
    ask_price_5: float = 0

    bid_volume_1: float = 0
    bid_volume_2: float = 0
    bid_volume_3: float = 0
    bid_volume_4: float = 0
    bid_volume_5: float = 0

    ask_volume_1: float = 0
    ask_volume_2: float = 0
    ask_volume_3: float = 0
    ask_volume_4: float = 0
    ask_volume_5: float = 0


@dataclass
class Order():
    """
    Order data contains information for tracking lastest status
    of a specific order.
    """
    symbol=""
    broker=""
    order_id: int=0
    side: str=""
    direction:Direction=Direction.LONG
    broker_type: Product = Product.CASH
    type: OrderType = OrderType.LIMIT
    offset: Offset = Offset.NONE
    tif: Timeinforce = Timeinforce.GTC
    price: float = 0
    qty: float = 0
    filled_qty: float = 0
    avg_price: float = 0
    traded: float = 0
    fee: float = 0
    reduce = False
    post = False
    stopPrice: float = 0
    status: Status = Status.NEW
    time: float = 0

@dataclass
class Balance():
    symbol = ""
    balance: float=0.00
    withdraw_Available:float=0.00


@dataclass
class Trade():
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """
    symbol: str
    broker : Exchange
    side: str
    price: float = 0
    qty: float = 0
    fee: float = 0
    time: float = 0


@dataclass
class Position():
    symbol: str=""
    broker : Exchange=None
    direction: Direction=Direction.LONG
    price: float = 0
    avg_price: float = 0
    qty: float = 0
    Collateral: float = 0
    pnl: float = 0
    time: float = 0
    liquidation_Price:float=0

