""" Base strategy for implementation """

from aq.common import logger
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    parameters = []
    variables = []
    strategy_name = ""
    trading = False
    def __init__(self,engine):
        # self.broker = engine.broker
        # self.update_setting(setting)
        pass

    def start(self):
        self.trading = True

    @abstractmethod
    def on_ticker(self, event):
        pass

    @abstractmethod
    def on_order(self, event):
        pass

    @abstractmethod
    def on_trade(self, event):
        pass

    @abstractmethod
    def on_bar(self, event):
        pass

    @abstractmethod
    def on_position(self, event):
        pass
    # def send_market_order(self, symbol, qty, is_buy, timestamp):
    #   if not self.event_sendorder is None:
    #      order = Order(timestamp, symbol, qty, is_buy, True)
    #      self.event_sendorder(order)


    # def update_setting(self, setting: dict):
    #     """
    #     Update strategy parameter wtih value in setting dict.
    #     """
    #     for name in self.parameters:
    #         if name in setting:
    #             setattr(self, name, setting[name])

    def get_parameters(self):
        """
        Get strategy parameters dict.
        """
        strategy_parameters = {}
        for name in self.parameters:
            strategy_parameters[name] = getattr(self, name)
        return strategy_parameters

    def get_variables(self):
        """
        Get strategy variables dict.
        """
        strategy_variables = {}
        for name in self.variables:
            strategy_variables[name] = getattr(self, name)
        return strategy_variables