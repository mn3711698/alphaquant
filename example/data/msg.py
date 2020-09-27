
import os
import sys

baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')
from aq.common.message import Weixin
wx=Weixin("19479203478@chatroom")
msg=  f"*******一阳指策略测试*******\n交易对:BTC合约(币安)\n当前价格：测试\n操作建议:测试"
wx.send(msg)