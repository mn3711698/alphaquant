# -*- coding:utf-8 -*-
"""
@Time : 2020/4/6 7:40 下午
@Author : Domionlu
@Site : 
@File : InfluxDataServer.py
@Software: PyCharm
"""
from influxdb import InfluxDBClient
import pandas as pd
import datetime

client = InfluxDBClient('47.245.52.122', 8086, 'admin', 'admin', 'mydb')
class DataServer():
    def __init__(self):
        self.client = InfluxDBClient('47.245.52.122', 8086, 'admin', 'admin', 'mydb')
    def querybar(self,exchange,symbol,timeframe):
        if timeframe=='1m':
            sql=f"select time,open,high,low,close,volume from bar where exchange='{exchange}' and symbol='{symbol}' and timeframe='{timeframe}' order by time  desc limit 1000"
        else:
            sql = f"select time,open,high,low,close,volume from kline_{timeframe} where exchange='{exchange}' and symbol='{symbol}' order by time  desc limit 1000"
        print(sql)
        temp=pd.DataFrame(client.query(sql).get_points())
        temp=temp.set_index("time",drop=False)

        temp=temp.sort_index()
        if len(temp)>0:
            temp=temp.set_index("time",drop=False)
        return temp

    def query(self,sql):
        temp = pd.DataFrame(client.query(sql).get_points())
        if len(temp) > 0:
            temp = temp.set_index("time", drop=False)
        return temp

if __name__ =="__main__":
    db=DataServer()
    sql="SELECT symbol,makerprice,takerprice FROM spreed"
    # data=db.query("binance","BTC/USDT","1d")
    data=db.query(sql)
    data.to_csv("spreed.csv")

