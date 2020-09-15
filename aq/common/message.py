"https://open.feishu.cn/open-apis/bot/hook/b1aa39a0d98b43448cb76b18a2c4c6f7"

import requests
import json
from aq.common.logger import log

class Feishu():
    url="https://open.feishu.cn/open-apis/bot/hook/b1aa39a0d98b43448cb76b18a2c4c6f7"
    def send(self,title, text):
        data = json.dumps({"title" : title, "text" : text}, ensure_ascii= False)
        byte_data =  data.encode('utf-8')
        result = requests.post(self.url,byte_data)

class Weixin():
    url="http://47.240.12.212"
    chatroom="19479203478@chatroom"
    def __init__(self,chartroom):
        self.chatroom=chartroom
    def send(self, text):
        msg={"code":1,"to_wxid":self.chatroom,"text": text}
        log.info(msg)
        result = requests.post(self.url,json=msg)

if __name__ == "__main__":
    wx=Weixin("19479203478@chatroom")
    wx.send("test")
