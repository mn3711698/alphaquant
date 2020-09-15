import backtrader as bt
import pymongo
import datetime


class MongoData(bt.feed.DataBase):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        # name of the table is indicated by dataname
        # data is fetch between fromdate and todate
        assert (self.p.fromdate is not None)
        assert (self.p.todate is not None)

        # name of db
        self.db = db

        # iterator 4 data in the list
        self.iter = None
        self.data = None

    def start(self):
        super().start()
        if self.data is None:
            # connect to mongo db local default config
            client = pymongo.MongoClient('mongodb://localhost:27017/')
            db = client[self.db]
            collection = db[self.p.dataname]
            self.data = list(collection.find({'date': {'$gte': self.p.fromdate, '$lte': self.p.todate}}))
            client.close()

        # set the iterator anyway
        self.iter = iter(self.data)

    def stop(self):
        pass

    def _load(self):
        if self.iter is None:
            # if no data ... no parsing
            return False

        # try to get 1 row of data from iterator
        try:
            row = next(self.iter)
        except StopIteration:
            # end of the list
            return False

        # fill the lines
        self.lines.datetime[0] = self.date2num(row['starttime'])
        self.lines.open[0] = row['open']
        self.lines.high[0] = row['high']
        self.lines.low[0] = row['low']
        self.lines.close[0] = row['close']
        self.lines.volume[0] = row['volume']
        self.lines.openinterest[0] = -1

        # Say success
        return True