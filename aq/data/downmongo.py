# -*- coding:utf-8 -*-
"""
@Time : 2020/5/3 8:05 下午
@Author : Domionlu
@Site : 
@File : downmongo.py
"""
from aq.data.MongoDataSerer import db,get_spreed
import pandas as pd
from pandas import DataFrame,Series

data=get_spreed()
data.to_csv("spreed.csv")
print(data.describe())