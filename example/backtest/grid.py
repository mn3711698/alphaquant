import backtrader as bt
import os,sys
import pandas as pd
import numpy as np

class GridStrategy(bt.Strategy):
    params = (
        ('maperiod', 30),
    )

    def __init__(self):
        self.high = self.data.high
        self.low = self.data.low
        self.close=self.data.close
        self.volt=(self.high-self.low)/self.close
        self.status=0

    def init_pos(self):
        price=self.close[0]
        cash = self.broker.get_cash()
        size=cash/2/price
        self.buy(price=price, size=size)






    def next(self):
        if self.status==0:
            self.init_pos()
            self.status=1
        cash=self.broker.get_cash()
        value=self.broker.get_value()
        pos=self.getposition()
        print(cash,value,pos)







        # if self.last_price_index == None:
        #     for i in range(len(self.price_levels)):
        #         if self.data.close > self.price_levels[i]:
        #             self.last_price_index = i
        #             self.order_target_percent(
        #                 target=i/(len(self.price_levels) - 1))
        #             return
        # else:
        #     signal = False
        #     while True:
        #         upper = None
        #         lower = None
        #         if self.last_price_index > 0:
        #             upper = self.price_levels[self.last_price_index - 1]
        #         if self.last_price_index < len(self.price_levels) - 1:
        #             lower = self.price_levels[self.last_price_index + 1]
        #         # 还不是最轻仓，继续涨，就再卖一档
        #         if upper != None and self.data.close > upper:
        #             self.last_price_index = self.last_price_index - 1
        #             signal = True
        #             continue
        #         # 还不是最重仓，继续跌，再买一档
        #         if lower != None and self.data.close < lower:
        #             self.last_price_index = self.last_price_index + 1
        #             signal = True
        #             continue
        #         break
        #     if signal:
        #         self.long_short = None
        #         self.order_target_percent(
        #             target=self.last_price_index/(len(self.price_levels) - 1))

if __name__ == '__main__':
    # 创建引擎
    cerebro = bt.Cerebro()

    # 加入网格策略
    cerebro.addstrategy(GridStrategy)

    # 导入数据
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, 'BINANCE_BTCUSDT.csv')
    data = bt.feeds.BacktraderCSVData(dataname=datapath, timeframe=bt.TimeFrame.Minutes)

    cerebro.adddata(data)

    # 设置起始资金
    cerebro.broker.setcash(100000.0)


    # 设定对比指数
    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years,
        data=data, _name='benchmark')

    # 策略收益
    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years, _name='portfolio')

    start_value = cerebro.broker.getvalue()
    print('Starting Portfolio Value: %.2f' % start_value)

    # Run over everything
    results = cerebro.run(runonce=False)

    strat0 = results[0]
    tret_analyzer = strat0.analyzers.getbyname('portfolio')
    print('Portfolio Return:', tret_analyzer.get_analysis())
    tdata_analyzer = strat0.analyzers.getbyname('benchmark')
    print('Benchmark Return:', tdata_analyzer.get_analysis())

    # 画图
    cerebro.plot(style='candle', barup='green')