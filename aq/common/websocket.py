# -*- coding:utf-8 -*-
"""
@Time : 2020/5/1 8:48 上午
@Author : Domionlu
@Site : 
@File : websocket.py
"""
# -*- coding:utf-8 -*-
"""
@Time : 2020/4/30 8:31 上午
@Author : Domionlu
@Site : 
@File : ws.py
"""
import json
import time
from threading import Thread, Lock
from aq.common.logger import log
from websocket import WebSocketApp
import traceback


class WebsocketClient:
    _CONNECT_TIMEOUT_S = 5
    CHANNEL="channel"
    def __init__(self):
        self.connect_lock = Lock()
        self.ws = None
        self.proxies=None

    def _get_url(self):
        raise NotImplementedError()

    def _on_message(self, ws, message):
        raise NotImplementedError()
        # if self.CHANNEL.lower() in message:
        #     msg=json.loads(message)
        #     ch = msg[self.CHANNEL.lower()]
        #     f = self.channel[ch.upper()]
        #     f(message)
        #

    def _ping(self,ws):
        raise NotImplementedError()

    def send(self, message):
        self.connect()
        self.ws.send(message)

    def send_json(self, message):
        self.send(json.dumps(message))

    def _connect(self):
        assert not self.ws, "ws should be closed before attempting to connect"

        self.ws = WebSocketApp(
            self._get_url(),
            on_message=self._wrap_callback(self._on_message),
            on_close=self._wrap_callback(self._on_close),
            on_error=self._wrap_callback(self._on_error),
        )

        wst = Thread(target=self._run_websocket, args=(self.ws,))
        wst.daemon = True
        wst.start()

        # Wait for socket to connect
        ts = time.time()
        while self.ws and (not self.ws.sock or not self.ws.sock.connected):
            if time.time() - ts > self._CONNECT_TIMEOUT_S:
                self.ws = None
                return
            time.sleep(0.1)

        pingt=Thread(target=self._ping,args=(self.ws,))
        pingt.daemon=True
        pingt.start()

    def _wrap_callback(self, f):
        def wrapped_f(ws, *args, **kwargs):
            if ws is self.ws:
                try:
                    f(ws, *args, **kwargs)
                except Exception as e:
                    log.error( traceback.format_exc())
                    raise Exception(f'Error running websocket callback: {e}')
        return wrapped_f

    def _run_websocket(self, ws):
        try:
            if self.proxies:
                ws.run_forever(http_proxy_host=self.proxies['host'],http_proxy_port=self.proxies['port'])
            else:
                ws.run_forever()
        except Exception as e:
            log.error(traceback.format_exc())
            raise Exception(f'Unexpected error while running websocket: {e}')
        finally:
            self._reconnect(ws)

    def _reconnect(self, ws):
        assert ws is not None, '_reconnect should only be called with an existing ws'
        if ws is self.ws:
            #todo 2020.05.01重新连接之后需要判断当前的订阅是不是要重新订阅，包括登录状态
            log.info("Reconnect...")
            self.ws = None
            ws.close()
            self.connect()
            self._subscribe()

    def _subscribe(self) -> None:
        raise NotImplementedError

    def connect(self,proxies=None):
        self.proxies=proxies
        if self.ws:
            return
        with self.connect_lock:
            while not self.ws:
                self._connect()
                if self.ws:
                    log.info("WS连接成功！")
                    return

    def _on_close(self, ws):
        log.error("WS连接关闭")
        self._reconnect(ws)

    def _on_error(self, ws, error):
        log.error(error)
        self._reconnect(ws)

    def reconnect(self) -> None:
        if self.ws is not None:
            self._reconnect(self.ws)






if __name__ == "__main__":
    pass