# -*- coding:utf-8 -*-
"""
@Time : 2020/4/14 9:26 下午
@Author : Domionlu
@Site : 
@File : quant.py
"""
# -*- coding:utf-8 -*-

"""
Asynchronous driven quantitative trading framework.

Author: HuangTao
Date:   2017/04/26
Email:  huangtao@ifclover.com
"""

import signal
import asyncio

from FeedServer.log import log
from FeedServer.config import  config


class Quant:
    """ Asynchronous driven quantitative trading framework.
    """

    def __init__(self):
        self.loop = None
        self.event_center = None

    def initialize(self, config_module=None):
        """ Initialize.

        Args:
            config_module: config file path, normally it"s a json file.
        """
        self._get_event_loop()
        self._load_settings(config_module)
        self._init_logger()
        self._init_event_center()


    def start(self):
        """Start the event loop."""
        def keyboard_interrupt(s, f):
            print("KeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(s))
            self.loop.stop()
        signal.signal(signal.SIGINT, keyboard_interrupt)

        log.info("start io loop ...", caller=self)
        self.loop.run_forever()

    def stop(self):
        """Stop the event loop."""
        log.info("stop io loop.", caller=self)
        self.loop.stop()

    def _get_event_loop(self):
        """ Get a main io loop. """
        if not self.loop:
            self.loop = asyncio.get_event_loop()
        return self.loop

    def _load_settings(self, config_module):
        """ Load config settings.

        Args:
            config_module: config file path, normally it"s a json file.
        """
        config.loads(config_module)

    def _init_logger(self):
        """Initialize logger."""
        console = config.log.get("console", True)
        level = config.log.get("level", "DEBUG")
        path = config.log.get("path", "/tmp/logs/Quant")
        name = config.log.get("name", "quant.log")
        clear = config.log.get("clear", False)
        backup_count = config.log.get("backup_count", 0)
        if console:
            log.initLogger(level)
        else:
            log.initLogger(level, path, name, clear, backup_count)

    def _init_event_center(self):
        """Initialize event center."""
        if config.rabbitmq:
            from FeedServer.rqevent import EventCenter
            self.event_center = EventCenter()
            self.loop.run_until_complete(self.event_center.connect())


quant = Quant()

if __name__ == "__main__":
    pass