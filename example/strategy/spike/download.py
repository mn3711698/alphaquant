
from aq.broker.binancefutures import BinanceFutures
from aq.engine.event import EventEngine
import pandas as pd
ev=EventEngine()
b=BinanceFutures(ev)
bar=b.get_bar("BTCUSDT","1m")
data=pd.DataFrame(bar)
data.to_csv("btcusdt1m.csv")