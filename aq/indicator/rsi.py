import numpy as np
from aq.indicator.base import *
from aq.common.logger import log
from aq.common.tools import *
import talib
import math


def trend_rsi(data,smoothK=3,smoothD=3,lengthRSI=7,lengthStoch=5):
    """"
    :return 0:盘整，1:向上，-1:向下
    """
    k,d=StochRSI(data, smoothK=smoothK, smoothD=smoothD, lengthRSI=lengthRSI, lengthStoch=lengthStoch)
    l = f"{k[-1]},{d[-1]}"
    trend=0#趋势盘整
    if k[-1] > d[-1] and k[-1] > k[-2] and d[-1] > d[-2]:
        log.info(f"趋势向上,{l}")
        trend = 1 #
    elif k[-1] < d[-1] and k[-1] < k[-2] and d[-1] < d[-2]:
        log.info(f"趋势向下,{l}")
        trend = -1
    return trend

def trend_frsi(data,timeperiod=6):
    low=-0.8
    high=0.8
    r = talib.RSI(data, timeperiod=timeperiod)
    v1=0.1*(r-50)
    v2=talib.WMA(v1,timeperiod)
    ifish=list((np.exp(2*v2)-1)/(np.exp(2*v2)+1))
    log.info(f"{ifish[-1]},{ifish[-2]}")
    trend = 0
    if (ifish[-1]>0 and ifish[-1]>ifish[-2]) or (ifish[-1]>0.95):
        trend=1
    elif (ifish[-1]<0 and ifish[-1]<ifish[-2]) or (ifish[-1]<-0.95):
        trend=-1
    # if ifish[-1]>ifish[-2] and ifish[-2]>ifish[-3] and ifish[-1]>low:
    #     trend=1
    # elif ifish[-1]<ifish[-2] and ifish[-2]<ifish[-3] and ifish[-1]<high:
    #     trend=-1
    return trend

def dsr(data,smoothK=3,smoothD=3,lengthRSI=7,lengthStoch=5):
    """"
    :return 1:买入/开多，-1:卖出/开空
    """
    k,d=StochRSI(data, smoothK=smoothK, smoothD=smoothD, lengthRSI=lengthRSI, lengthStoch=lengthStoch)
    # log.info(f"4小时k:{k[-1]},d:{d[-1]},15分钟k:{k[-1]},d:{fastd[-1]}")
    s=f"{k[-1]},{d[-1]}"
    log.info(s)
    sign=0
    if crossover(k, d) and k[-1] > 20:
            # msg = f"当前时间:{get_datetime()}\n趋势：向上\n当前价格{list(short)[-1]}\n策略：买入"
        sign=1
            # self.msg.send("日内震荡策略", msg)
            # self.open_order("Buy")

    if crossunder(k, d) and k[-1] < 80:
        sign=-1
            # msg = f"当前时间:{get_datetime()}\n趋势：向下\n当前价格{list(short)[-1]}\n策略：卖出"
            # self.msg.send("日内震荡策略", msg)
            # self.open_order("Sell")
    return sign

if __name__ == "__main__":
    feed = pd.read_csv("BINANCE_BTCUSDT, 240.csv")
    close=feed['close']
    t=trend_frsi(close)
    print(t)
    # beta=ols(close,10)

    pass