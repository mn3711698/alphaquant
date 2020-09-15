#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究
# zsxq 知识星球

import wx
import wx.adv
import wx.grid
import wx.html2
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import numpy as np
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg  as NavigationToolbar
import matplotlib.gridspec as gridspec # 分割子图

import tushare as ts
import pandas as pd
import mpl_finance as mpf # attention: mpl_finance 从2020年开始更新至 mplfinance
import matplotlib.pyplot as plt
import baostock as bs
import datetime
import seaborn as sns  #画图用的

import sys

try:
    import backtrader as bt
except ImportError:
    raise ImportError(
        'backtrader seems to be missing. Needed for defining strategy support')

def CalNdaysSignal(stockdata, N1=50, N2=5):
    stockdata["N1_High"] = stockdata["High"].rolling(window=N1).max()  # 计算最近N1个交易日最高价
    expan_max = stockdata.Close.expanding().max()
    stockdata["N1_High"].fillna(value=expan_max, inplace=True)  # 目前出现过的最大值填充前N1个nan

    stockdata["N2_Low"] = stockdata["Low"].rolling(window=N2).min()  # 计算最近N2个交易日最低价
    expan_min = stockdata.Close.expanding().min()
    stockdata["N2_Low"].fillna(value=expan_min, inplace=True)  # 目前出现过的最小值填充前N2个nan

    # 收盘价超过N1最高价 买入股票持有
    buy_index = stockdata[stockdata.Close > stockdata.N1_High.shift(1)].index
    stockdata.loc[buy_index, "signal"] = 1
    # 收盘价超过N2最低价 卖出股票持有
    sell_index = stockdata[stockdata.Close < stockdata.N2_Low.shift(1)].index
    stockdata.loc[sell_index, "signal"] = 0
    stockdata["signal"].fillna(method="ffill", inplace=True)
    stockdata["signal"] = stockdata.signal.shift(1)
    stockdata["signal"].fillna(method="bfill", inplace=True)
    return stockdata

df_trader = pd.DataFrame(columns=["close", "buy", "sell", "profit"], dtype='float64')

def log_to_file(func):
    def wrapper(*args, **kwargs):
        # 临时把标准输出重定向到一个文件，然后再恢复正常
        with open('logtrade.txt', 'a') as f:
            oldstdout = sys.stdout
            sys.stdout = f
            try:
                func(*args, **kwargs)
            finally:
                sys.stdout = oldstdout
    return wrapper

class dua_ma_strategy(bt.Strategy):
    # 全局设定交易策略的参数
    params=(
            ("ma_short",5),
            ("ma_long", 20),
           )
    def __init__(self):

        # 指定价格序列
        self.dataclose=self.datas[0].close
        # 初始化交易指令、买卖价格和手续费
        self.order = None

        # 添加移动均线指标
        # 5日移动平均线
        self.sma5 = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.ma_short)
        # 10日移动平均线
        self.sma10 = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.ma_long)

        # 内置了talib模块
        # self.sma = bt.talib.SMA(self.data, timeperiod=self.params.maperiod)

    @log_to_file
    def log(self, txt, dt=None, doprint=False):
        # 日志函数，用于统一输出日志格式
        if doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s:\n%s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        """
        订单状态处理
        Arguments:
            order {object} — 订单状态
        """
        if order.status in [order.Submitted, order.Accepted]:
            # 如订单已被处理，则不用做任何事情
            return
        # 检查订单是否完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入订单完成！\n价格:{order.executed.price}\n\
                                成本:{order.executed.value}\n\
                                手续费:{order.executed.comm}\n'.replace(' ',''), doprint=True)
                df_trader.loc[self.datas[0].datetime.date(0), "buy"] = order.executed.price

            else:
                self.log(f'卖出订单完成！\n价格：{order.executed.price}\n\
                                成本: {order.executed.value}\n\
                                手续费{order.executed.comm}\n'.replace(' ',''), doprint=True)
                df_trader.loc[self.datas[0].datetime.date(0), "sell"] = order.executed.price

            self.bar_executed = len(self)

        # 订单因为缺少资金之类的原因被拒绝执行
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单未完成', doprint=True)
        # 订单状态处理完成，设为空
        self.order = None

    # 记录交易收益情况
    def notify_trade(self, trade):
        """
        交易成果
        Arguments: trade {object} — 交易状态
        """
        if not trade.isclosed:
            return
        # 显示交易的毛利率和净利润
        self.log('收益率：毛利润 %.2f, 净利润 %.2f\n' %
                 (trade.pnl, trade.pnlcomm), doprint=True)
        if df_trader.loc[self.datas[0].datetime.date(0), "profit"] != np.NAN:
            df_trader.loc[self.datas[0].datetime.date(0), "profit"] += trade.pnlcomm
        else:
            df_trader.loc[self.datas[0].datetime.date(0), "profit"] = trade.pnlcomm

    def next(self):
        # 记录收盘价
        self.log(f'Close, %.2f' % self.dataclose[0], doprint=False)
        df_trader.loc[self.datas[0].datetime.date(0), "close"] = self.dataclose[0]

        if self.order: # 是否有指令等待执行
            return
            # 是否持仓
        if not self.position: # 没有持仓
            # 执行买入条件判断：MA5上扬突破MA10，买入
            if self.sma5[0] > self.sma10[0]:
                self.order = self.buy() # 执行买入
                self.log('执行买入价格：%.2f' % self.dataclose[0], doprint = True)
        else:
            # 执行卖出条件判断：MA5下穿跌破MA10，卖出
            if self.sma5[0] < self.sma10[0]:
                self.order = self.sell() # 执行卖出
                self.log('执行卖出价格：%.2f' % self.dataclose[0], doprint = True)

    # 回测结束后输出
    def stop(self):
        self.log(u'金叉死叉策略 %2d 最终资金 %.2f' %
                 (self.params.ma_long, self.broker.getvalue()), doprint=True)

class FinanceDatStrategy(bt.Strategy):

    params=(
            ("turn_min",3),
            ("turn_max", 10),
            ("peTTM_min", 35),
            ("peTTM_max", 55)
           )

    def __init__(self):

        # 指定价格序列
        self.dataclose=self.datas[0].close
        # 初始化交易指令、买卖价格和手续费
        self.order = None
    @log_to_file
    def log(self, txt, dt=None, doprint=False):
        # 日志函数，用于统一输出日志格式
        if doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s:\n%s' % (dt.isoformat(), txt))

    # 记录交易收益情况
    def notify_trade(self, trade):
        """
        交易成果
        Arguments: trade {object} — 交易状态
        """
        if not trade.isclosed:
            return
        # 显示交易的毛利率和净利润
        self.log('收益率：毛利润 %.2f, 净利润 %.2f\n' %
                 (trade.pnl, trade.pnlcomm), doprint=True)

        df_trader.loc[self.datas[0].datetime.date(0), "profit"] = trade.pnlcomm

    def notify_order(self, order):
        """
        订单状态处理
        Arguments:
            order {object} — 订单状态
        """
        if order.status in [order.Submitted, order.Accepted]:
            # 如订单已被处理，则不用做任何事情
            return
        # 检查订单是否完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入订单完成！\n价格:{order.executed.price}\n\
                                成本:{order.executed.value}\n\
                                手续费:{order.executed.comm}\n'.replace(' ',''), doprint=True)
                df_trader.loc[self.datas[0].datetime.date(0), "buy"] = order.executed.price

            else:
                self.log(f'卖出订单完成！\n价格：{order.executed.price}\n\
                                成本: {order.executed.value}\n\
                                手续费{order.executed.comm}\n'.replace(' ',''), doprint=True)
                df_trader.loc[self.datas[0].datetime.date(0), "sell"] = order.executed.price

            self.bar_executed = len(self)

        # 订单因为缺少资金之类的原因被拒绝执行
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单未完成', doprint=True)
        # 订单状态处理完成，设为空
        self.order = None

    def next(self):

        # 记录收盘价
        self.log(f'Close, %.2f' % self.dataclose[0], doprint=False)
        df_trader.loc[self.datas[0].datetime.date(0), "close"] = self.dataclose[0]

        if self.order: # 是否有指令等待执行
            return
            # 是否持仓

        if not self.position:  # 没有持仓
            if self.datas[0].turn[0] < self.params.turn_min and 0 < self.datas[0].peTTM[0] < self.params.peTTM_min:
                # 得到当前的账户价值
                total_value = self.broker.getvalue()
                # 1手=100股，满仓买入
                self.order = self.buy(size=int((total_value / 100) / self.datas[0].close[0]) * 100)
                self.log('执行买入价格：%.2f' % self.dataclose[0], doprint=True)
        else:  # 持仓，满足条件全部卖出
            if self.datas[0].turn[0] > self.params.turn_max or self.datas[0].peTTM[0] > self.params.peTTM_max:
                self.close(self.datas[0])
                self.log('执行卖出价格：%.2f' % self.dataclose[0], doprint = True)


class MulitShiftStrategy(bt.Strategy):
        # 策略参数
        params = dict(
            period=20,  # 均线周期
            before_days=30, # 过去30日的收益率
            trader_num = 2 # 最多交易的个数
        )
        long_list = [] # 存储股票池

        def __init__(self):
            self.mas = dict()
            # 遍历所有股票,计算20日均线
            for data in self.datas:
                self.mas[data._name] = bt.ind.SMA(data.close, period=self.p.period)

        def next(self):
            # 计算过去若干天的收益率

            if len(self) % self.p.before_days == 0: # 注意:self的长度是逐渐增大的, 初始为period
                rate_list = []
                for data in self.datas:
                    if len(data) >= self.p.before_days: # 注意:data的长度是逐渐增大的, 初始为period
                        p0 = data.close[0]
                        pn = data.close[1-self.p.before_days]
                        rate = (p0-pn)/pn
                        rate_list.append([data._name, rate])

                sorted_rate = sorted(rate_list,key=lambda x:x[1],reverse=True)
                self.long_list = [i[0] for i in sorted_rate[:self.params.trader_num]]
                long_str = ';'.join(self.long_list)
                self.log(f'更新股票池:\n{long_str}', doprint=True)

            # 得到当前的账户价值
            total_value = self.broker.getvalue()
            p_value = total_value*0.9/self.params.trader_num

            for data in self.datas:

                pos = self.getposition(data).size # 获取仓位

                if not pos and (data._name in self.long_list) and (self.mas[data._name][0] > data.close[0]):
                    size = int(p_value/100/data.close[0])*100
                    self.buy(data = data, size = size)
                    self.log(f'执行买入:\n股票名称:{data._name};当前价格:{data.close[0]:.2f}', doprint=True)

                if (pos!=0) and (data._name not in self.long_list or self.mas[data._name][0] < data.close[0]):
                    self.close(data = data)
                    self.log(f'执行卖出:\n股票名称:{data._name};当前价格:{data.close[0]:.2f}', doprint=True)

        @log_to_file
        def log(self, txt, dt=None, doprint=False):
            # 日志函数，用于统一输出日志格式
            if doprint:
                dt = dt or self.datas[0].datetime.date(0)
                print('%s:\n%s' % (dt.isoformat(), txt))

        def notify_order(self, order):
            """
            订单状态处理
            Arguments:
                order {object} — 订单状态
            """
            if order.status in [order.Submitted, order.Accepted]:
                # 如订单已被处理，则不用做任何事情
                self.log('ORDER ACCEPTED/SUBMITTED', dt=order.created.dt)
                self.order = order
                return

            # 检查订单是否完成
            if order.status in [order.Completed]:

                if order.isbuy():
                    self.log(f'买入订单完成！\n价格:{order.executed.price:.2f}\n\
                                    成本:{order.executed.value:.2f}\n\
                                    手续费:{order.executed.comm:.2f}\n'.replace(' ', ''), doprint=True)

                    if (self.datas[0].datetime.date(0) in df_trader.index) and ("buy" in df_trader.columns):
                        # 同一天买入多股 叠加显示
                        df_trader.loc[self.datas[0].datetime.date(0), "buy"] += order.executed.price
                    else:
                        df_trader.loc[self.datas[0].datetime.date(0), "buy"] = order.executed.price

                if order.issell():
                    self.log(f'卖出订单完成！\n价格：{order.executed.price:.2f}\n\
                                    成本: {order.executed.value:.2f}\n\
                                    手续费{order.executed.comm:.2f}\n'.replace(' ', ''), doprint=True)
                    if (self.datas[0].datetime.date(0) in df_trader.index) and ("sell" in df_trader.columns):
                        # 同一天卖出多股 叠加显示
                        df_trader.loc[self.datas[0].datetime.date(0), "sell"] += order.executed.price
                    else:
                        df_trader.loc[self.datas[0].datetime.date(0), "sell"] = order.executed.price

                self.bar_executed = len(self)

            # 订单因为缺少资金之类的原因被拒绝执行
            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                self.log('订单未完成', doprint=True)
            # 订单状态处理完成，设为空
            self.order = None

        # 记录交易收益情况
        def notify_trade(self, trade):

            if not trade.isclosed:
                return
            # 显示交易的毛利率和净利润
            self.log(f'收益率：毛利润 {trade.pnl:.2f}, 净利润 {trade.pnlcomm:.2f}\n', doprint=True)

            df_trader.loc[self.datas[0].datetime.date(0), "profit"] = trade.pnlcomm

__all__ = ["dua_ma_strategy", "FinanceDatStrategy", "MulitShiftStrategy"]