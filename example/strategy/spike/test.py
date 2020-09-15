
import numpy as np
import pandas as pd

from aq.common.tools import time_cost
force=pd.read_csv("forceorder.csv")
force["T"]=pd.to_datetime(force['T'], unit='ms')
# force=force[force["T"]>"2020-07-14 11:00:01.388000 "]
force["delta"]=force["T"].shift()-force["T"]
# bar=pd.read_csv("btcusdt1m.csv")

force["delta"]=pd.to_numeric(force["delta"].dt.seconds)
force=force.fillna(0)
force=force[force["delta"]<60]
delta=np.array(force["delta"])
std=np.std(delta)
max=np.max(delta)
min=np.min(delta)
print(std)
# date_list=pd.to_datetime(bar['open_time'], unit='ms')
data_list=[]

@time_cost
def tuples(data):
    for r in data.itertuples():
        # print(r)
        data_list.append(r)
@time_cost
def rows(data):
    for r in data.iterrows():
        # print(r)
        data_list.append(r)
@time_cost
def nv(data):
    d=data.values.tolist()
    data_list.extend(d)
    d=data_list[-1]
    t=d[1]
    print(t)

nv(bar)
data=np.array(data_list)
data=data[:,9]
print(data)