from aq.backtest.backtestEngine import BacktestEngine
from aq.common.constant import *
from datetime import datetime
from aq.common.logger import *

import pandas as pd

from example.strategy.doubleEmaStrategy import DoubleMaStrategy
if __name__ == '__main__':
    """
    回测调用demo
    """
    log.info("开始回测")
    engine = BacktestEngine()
    engine.set_parameters(
        symbol="BTC/USDT",
        mode=BacktestingMode.Bar,
        interval="1m",
        start=datetime(2019, 1, 1),
        end=datetime(2019, 4, 30),
        rate=0.3 / 10000,
        slippage=0.2,
        size=300,
        pricetick=0.2,
        capital=10000,
    )
    feed = pd.read_csv("binance_BTCUSDT_1d.csv")
    feed['time'] = pd.to_datetime(feed['time'])
    engine.add_data(feed)
    engine.add_strategy(DoubleMaStrategy, {})
    #
    engine.run_backtest()
    engine.statistics()


