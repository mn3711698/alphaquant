

import os, sys
baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')
from aq.broker.binancefutures import BinanceFutures
from aq.broker.huobi import HuobiFutures
from aq.common.constant import *
from aq.engine.baseStrategy import BaseStrategy
from aq.engine.config import config
from aq.common.logger import log
from aq.engine.event import EventEngine

def on_orderbook( msg):
    print(msg)
lcfg=config.long
scfg=config.short
ev=EventEngine()
long=BinanceFutures(ev)
subscribe={ORDERBOOK:on_orderbook}
# long.subscribe(lcfg.symbols,subscribe)

short=HuobiFutures(ev)
short.subscribe((scfg.symbols,subscribe))



