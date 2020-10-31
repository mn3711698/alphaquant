
import websocket
import os
from websocket import WebSocketApp

try:
    import thread
except ImportError:
    import _thread as thread
import time


class Test(WebSocketApp):
    def __init__(self):
        self.url="wss://btmx.io/api/pro/v1/stream"
        super(Test, self).__init__(url=self.url, on_open=self.on_open, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)

    def on_message(self, message):
        print("####### on_message #######")
        print(self)
        print(message)

    def on_error(self, error):
        print("####### on_error #######")
        print(self)
        print(error)

    def on_close(self):
        print("####### on_close #######")
        print(self)
        print("####### closed #######")

    def on_open(self):
        print(self)

        self.send('{"op":"sub","ch":"depth:BTC/USDT"}')

    # def start(self):
    #     ws = websocket.WebSocketApp(self.url,
    #                                 on_message=self.on_message,
    #                                 on_error=self.on_error,
    #                                 on_close=self.on_close)
    #     ws.on_open = self.on_open
    #     ws.run_forever(http_proxy_host="127.0.0.1", http_proxy_port=8118)


if __name__ == '__main__':
    value=os.environ.get("http_proxy", None)
    obj = Test()
    obj.run_forever()