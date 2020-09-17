# -*- coding:utf-8 -*-
"""
@Time : 2020/4/8 9:17 下午
@Author : Domionlu
@Site : 
@File : mqevent.py
@Software: PyCharm
"""
import json
import zlib
import asyncio
import pika
import inspect
import aioamqp
from FeedServer.config import *
from FeedServer.log import log
from queue import Empty, Queue
from threading import Thread
from time import sleep

class EventServer:

    def __init__(self):
        self._host ="127.0.0.1"
        self._port = "5672"
        self._username ="guest"
        self._password ="guest"
        self._protocol = None
        self._connect = None
        self._channel = None  # Connection channel.
        self._connected = False  # If connect success.
        self._subscribers = []  # e.g. [(event, callback, multi), ...]
        self._event_handler = {}  # e.g. {"exchange:routing_key": [callback_function, ...]}
        self.initialize()
        self._thread: Thread = Thread(target=self._run)

    def initialize(self):
        self.connect()

    def connect(self):
        credentials = pika.PlainCredentials(self._username, self._password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self._host, port=self._port, credentials=credentials))
        channel = connection.channel()
        self._connect=connection
        exchanges = ["Trade", "Ticker", "OrderBook", "BookDelta", "Kline.15min", "Asset", ]
        for name in exchanges:
            channel.exchange_declare(name, "topic");
        self._channel = channel
        log.debug("create default exchanges success!")

    def subscribe(self,exchange,callback,binding_key):
        result = self._channel.queue_declare('', exclusive=True)
        queue_name = result.method.queue
        self._channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=binding_key)
        self._channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        self._channel.start_consuming()


    def publish(self,event):
        log.info(f"publish exchange:{event.exchange},key:{event.routing_key},data{event.data}")
        data = event.dumps()
        self._channel.basic_publish(exchange=event.exchange,
                              routing_key=event.routing_key,
                              body=data)

    def _run(self):
        while self._active:
            try:
                event = self._queue.get(block=True, timeout=1)
                self._process(event)
            except Empty:
                pass

class AsyncioTask:
    """ Single run task.
    """

    @classmethod
    def run(cls, func, *args, **kwargs):
        """ Create a coroutine and execute immediately.

        Args:
            func: Asynchronous callback function.
        """
        asyncio.run(cls.task(func, *args, **kwargs))

    async def task(self,func, *args, **kwargs):
        f=asyncio.create_task(func,*args, **kwargs)
        await asyncio.gather(f)

    @classmethod
    def call_later(cls, func, delay=0, *args, **kwargs):
        """ Create a coroutine and delay execute, delay time is seconds, default delay time is 0s.

        Args:
            func: Asynchronous callback function.
            delay: Delay time is seconds, default delay time is 0, you can assign a float e.g. 0.5, 2.3, 5.1 ...
        """
        if not inspect.iscoroutinefunction(func):
            asyncio.get_event_loop().call_later(delay, func, *args)
        else:
            def foo(f, *args, **kwargs):
                asyncio.get_event_loop().create_task(f(*args, **kwargs))
            asyncio.get_event_loop().call_later(delay, foo, func, *args)

class Event:
    """ Event base.

    Attributes:
        name: Event name.
        exchange: Exchange name.
        queue: Queue name.
        routing_key: Routing key name.
        pre_fetch_count: How may message per fetched, default is 1.
        data: Message content.
    """

    def __init__(self, name=None, exchange=None, queue=None, routing_key=None, pre_fetch_count=1, data=None):
        """Initialize."""
        self._name = name
        self._exchange = exchange
        self._queue = queue
        self._routing_key = routing_key
        self._pre_fetch_count = pre_fetch_count
        self._data = data
        self._callback = None  # Asynchronous callback function.

    @property
    def name(self):
        return self._name

    @property
    def exchange(self):
        return self._exchange

    @property
    def queue(self):
        return self._queue

    @property
    def routing_key(self):
        return self._routing_key

    @property
    def prefetch_count(self):
        return self._pre_fetch_count

    @property
    def data(self):
        return self._data

    def dumps(self):
        d = {
            "n": self.name,
            "d": self.data
        }
        s = json.dumps(d)
        b = zlib.compress(s.encode("utf8"))
        return b

    def loads(self, b):
        b = zlib.decompress(b)
        d = json.loads(b.decode("utf8"))
        self._name = d.get("n")
        self._data = d.get("d")
        return d


    def __str__(self):
        info = "EVENT: name={n}, exchange={e}, queue={q}, routing_key={r}, data={d}".format(
            e=self.exchange, q=self.queue, r=self.routing_key, n=self.name, d=self.data)
        return info

    def __repr__(self):
        return str(self)




if __name__ == "__main__":
    pass
