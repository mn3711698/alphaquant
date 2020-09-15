# -*- coding:utf-8 -*-
"""
@Time : 2020/4/4 1:27 下午
@Author : Domionlu
@Site : 
@File : base.py
@Software: PyCharm
"""
import numpy as np
import statsmodels.formula.api as sml
import pandas as pd
import talib

def StochRSI(close,smoothK,smoothD,lengthRSI,lengthStoch):

    RSI = talib.RSI(close, timeperiod=lengthRSI)
    LLV = RSI.rolling(window=lengthStoch).min()
    HHV = RSI.rolling(window=lengthStoch).max()
    stochRSI = (RSI - LLV) / (HHV - LLV) * 100
    fastk = talib.MA(np.array(stochRSI), smoothK)
    fastd = talib.MA(np.array(fastk),smoothD)
    return fastk, fastd

def polyslope(data,N):
    def ols(d):
        x=np.arange(len(d))
        slope,intercept = np.polyfit(x, d, deg=1)
        return slope
    beta = data.rolling(N).apply(ols, raw=True)
    return beta

def sm_ols(data,N):
    def ols(d):
        model=sml.ols(formula="",data=d).fit()
        return model[1]
    beta = data.rolling(N).apply(ols, raw=True)
    return beta

def up(data):
    if len(data)>3:
        result= data[-1]>data[-2] and data[-2] <data[-3]
        return result
    else:
        return 0

def down(data):
    if len(data)>3:
        result= data[-1]<data[-2] and data[-2] >data[-3]
        return result
    else:
        return 0

def side(data):
    if data[-1]>data[-2]>data[-3]:
        return 1
    elif data[-1]<data[-2]<data[-3]:
        return -1
    else:
        return 0


def crossover(data1,data2):
    if data1[-1]>data2[-1] and data1[-2]<data2[-2]:
        return 1
    else:
        return 0


def crossunder(data1,data2):
    if data1[-1]<data2[-1] and data1[-2]>data2[-2]:
        return 1
    else:
        return 0

def sigmoid(x):  #sigmoid函数
     return 1/(1+np.exp(-x))


if __name__ == "__main__":
    feed = pd.read_csv("binance_BTCUSDT_1d.csv")
    close=feed['close']
    beta=polyslope(close,10)
    print(beta)
    # beta=ols(close,10)

    pass