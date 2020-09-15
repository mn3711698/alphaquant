#%%
from empyrical import cum_returns, annual_return, sharpe_ratio, max_drawdown

import pandas as pd
import empyrical as em
import matplotlib.pyplot as plt
df=pd.read_csv("pnl.csv")
df=df[['time','pnl']]

# df["time"]=pd.to_datetime(df["time"])
# df=df.set_index(df["time"])
df.plot(x="time",y="pnl")
# plt.show()
df["time"]=pd.to_datetime(df["time"])
df=df.set_index(df["time"])
ann_return = annual_return(df)   # 计算累计收益率
cum_return_list = cum_returns(df)
   # 计算sharp ratio
sharp = sharpe_ratio(df)
  # 最大回撤
max_drawdown_ratio = max_drawdown(df)
print("年化收益率 = {:.2%}, 累计收益率 = {:.2%}, 最大回撤 = {:.2%}, 夏普比率 = {:.2f} ".format
        (ann_return, cum_return_list[-1], max_drawdown_ratio, sharp))



