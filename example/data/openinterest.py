import os,sys
baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')
from aq.engine.log import log
from aq.engine.mqevent import Event
from aq.engine.event   import EventEngine
from aq.broker.binancefutures import BinanceFutures
from aq.common.constant import *
from aq.data.MongoDataSerer import db
from aq.common.tools import *


class OpenInterest():
    symbol='BTCUSDT'
    starttime=None
    def __init__(self):
        self.ev=EventEngine()
        self.ev.start()
        self.broke=BinanceFutures(self.ev)
        # self.broke.start("btcusdt",[FORCEORDER])
        # self.ev.register(FORCEORDER, self.callback)
    def loop(self):
        # db.table_name.aggregate({"$group": {_id: "max", max_value: {"$max": "$column_name"}}})
        rs=db.db["openinterest"].find().sort([("timestamp",-1)]).limit(1)
        rs=list(rs)
        if len(rs)>0:
            self.starttime=float(rs[0]["timestamp"])+1000*60
        else:
            self.starttime = get_cur_timestamp_ms() - 1000 * 30 * 288 * 5 * 60
        while True:
            self.loaddata()
            if (get_cur_timestamp_ms()-self.starttime)>1000*60*5:
                time.sleep(0.5)
            else:
                time.sleep(60)

    def loaddata(self):
        endtime= self.starttime+500*1000*60*5
        t=get_cur_timestamp_ms()
        if endtime>t:
            endtime=t
        data=self.broke.get_open_interest(self.symbol,'5m',self.starttime,endtime)
        try:
            db.insert_many("openinterest", data)
            self.starttime=data[-1]["timestamp"]
        except Exception as e:
            log.error(e)

if __name__ == "__main__":
        oi=OpenInterest()
        oi.loop()