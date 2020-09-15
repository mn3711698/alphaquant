import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import talib as tb


forceorder=pd.read_csv("forceorder.csv")
fo=forceorder[["T","S","ap","q"]]
fo.columns=["time","side","price","volume"]
fo["time"]=pd.to_datetime(fo["time"],unit="ms")
fo=fo.set_index("time")
buy=fo[fo["side"]=="BUY"]
sell=fo[fo["side"]=="SELL"]
buy_sign_price=buy["price"].resample("min").min()
buy_sign_volume=buy["volume"].resample("min").sum()
sell_sign_price=sell["price"].resample("min").max()
sell_sign_volume=sell["volume"].resample("min").sum()

bar=pd.read_csv("btcusdt1m.csv")
data_list=bar[["open_time","open","high","low","close","volume"]]
data_list.columns=['time','Open','High','Low','Close','Volume']
data_list["time"]=pd.to_datetime(data_list['time'], unit='ms')
data_list=data_list.set_index("time",drop=True)
data_list["buy_sign_price"]=buy_sign_price
data_list["buy_sign_volume"]=buy_sign_volume
data_list["sell_sign_price"]=sell_sign_price
data_list["sell_sign_volume"]=sell_sign_volume
data_list=data_list.fillna(0)
data_list['buy']=data_list["buy_sign_volume"]/data_list["Volume"]
data_list['sell']=data_list["sell_sign_volume"]/data_list["Volume"]

# data_list=[]
# data_list['open_time']=mdates.date2num(data_list['open_time'])

add_plot=[
    mpf.make_addplot(data_list["buy_sign_price"],scatter=True,markersize=100,marker="^",color='y'),
    mpf.make_addplot(data_list["sell_sign_price"],scatter=True,markersize=100,marker="v",color='r'),
]
mpf.plot(data_list,style='charles', figscale=2,addplot=add_plot,volume=True)

