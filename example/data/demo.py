# -*- coding:utf-8 -*-
"""
@Time : 2020/4/25 5:05 下午
@Author : Domionlu
@Site : 
@File : demo.py
"""
import pandas as pd
if __name__ == "__main__":
    data=pd.read_csv("spreed.csv")
    data["spreed"]=data["makerprice"]-data["takerprice"]

    print(data.tail())
    pass