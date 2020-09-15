# -*- coding:utf-8 -*-
"""
@Time : 2020/4/14 10:19 下午
@Author : Domionlu
@Site : 
@File : Feedmq.py
"""
from multiprocessing import Process
import json

import os
import sys
baseroot=os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')

from cryptofeed import FeedHandler
from cryptofeed.exchanges import BinanceFutures,FTX,HuobiDM
from cryptofeed.defines import L2_BOOK, TRADES,TICKER ,BOOK_DELTA
from FeedServer.rabbitmq import TickerRabbit,OrderbookRabbit,BookDeltaRabbit
from cryptofeed.pairs import huobi_dm_pairs


def main():
    try:
        f = FeedHandler()
        #f.add_feed(BinanceFutures(max_depth=10, channels=[L2_BOOK], pairs=['BTC-USDT'], callbacks={L2_BOOK:OrderbookRabbit()}))
        f.add_feed(FTX(max_depth=10, channels=[L2_BOOK], pairs=['BTC-PERP'], callbacks={L2_BOOK:OrderbookRabbit()}))
        # f.add_feed(HuobiDM(max_depth=10, channels=[L2_BOOK], pairs=['BTC-USDT'], callbacks={L2_BOOK:OrderbookRabbit()}))
        f.run()
    finally:
        pass


if __name__ == '__main__':
    pairs=huobi_dm_pairs()
    print(pairs)
    main()