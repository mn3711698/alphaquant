import tushare as ts
print(ts.__version__)
ts.set_token("0b1ce5f79cb391dfd8ab13e9f111c55d23f2783216cc5755d2080a74")
api = ts.pro_api()
# df = pro.trade_cal(exchange='', start_date='20200101', end_date='20200701', fields='exchange,cal_date,is_open,pretrade_date', is_open='0')
data = ts.pro_bar(pro_api=api, ts_code='000009.SZ', adj='qfq', start_date='20170101', end_date='20181011',ma=5,freq='D')
print(data)
# ts.get_hist_data('600848')