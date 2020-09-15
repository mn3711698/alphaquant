import ccxt

from pycoingecko import CoinGeckoAPI
import requests
import json
import numpy as np
import pandas as pd
cg = CoinGeckoAPI()

# url="https://fapi.binance.com/fapi/v1/premiumIndex"
#
# data=requests.get(url)
# data=json.loads(data.text)
# data=pd.DataFrame(data)
# data["lastFundingRate"]=pd.to_numeric(data["lastFundingRate"])
# data=data.sort_values("lastFundingRate")
# print(data)


url="https://ftx.com/api/funding_rates"
data=requests.get(url)
print(data)
data=json.loads(data.text)
data=pd.DataFrame(data["result"])
data["rate"]=pd.to_numeric(data["rate"])
data=data.sort_values("rate")
print(data)
