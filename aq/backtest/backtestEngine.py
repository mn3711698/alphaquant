from aq.broker.backtestBroker import BacktestBroker
from aq.common.object import *
from aq.engine.baseEngine import BaseEngine
import traceback
from datetime import datetime
from aq.common.logger import *
from aq.risk.analysis import *

class BacktestEngine(BaseEngine):
    """Base class for backtesting strategies.
    回测调用方式，和策略本身关联度小，不需要改变策略的情况下，可以直接用于实盘交易
    策略本身不需要关注当前是回测状态还是实盘，具体是由broker实现，回测时使用虚拟Broker，实盘时对接对应交易所
    :param barFeed: The bar feed to use to backtest the strategy.
    :type barFeed: :class:`pyalgotrade.barfeed.BaseBarFeed`.
    :param cash_or_brk: The starting capital or a broker instance.
    :type cash_or_brk: int/float or :class:`pyalgotrade.broker.broker`.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit_orders = {}
        self.limit_order_count = 0
        self.active_stop_orders = {}
        self.trade_count = 0
        self.active_limit_orders = {}
        self.mode = BacktestingMode.Bar  # Bar or Ticket 模式回测
        self.broker = BacktestBroker()
        self.bars = []
        self.tickets = []
        self.symbol = ""
        self.exchange = None
        self.trade_data = {}
        self.strategy_class = None
        self.strategy = None
        self.datetime = None
        self.daily_results = {}
        self.trades = {}

    def add_data(self, data):
        if self.mode == BacktestingMode.Ticket:
            self.tickets=data
        else:
            self.bars=data

    def add_strategy(self, strategy_class: type, setting: dict):
        """"""
        self.strategy_class = strategy_class
        self.strategy = strategy_class(self, setting)
        self.register_event()

    def run_backtest(self):
        """"""

        # self.strategy.on_init()
        # # Use the first [days] of history data for initializing strategy
        #
        # self.strategy.inited = True
        # logger.info("策略初始化完成")

        self.strategy.start()

        # Use the rest of history data for running backtesting
        if self.mode == BacktestingMode.Bar:
            history_data = self.bars
            log.info("开始回放历史Bar数据")
            for index,data in history_data.iterrows():
                try:
                    self.new_bar(data)
                except Exception:
                    log.error("触发异常，回测终止")
                    print(traceback.format_exc())
                    # logger.error(traceback.format_exc())
                    return

        else:
            history_data = self.tickets
            log.info("开始回放历史Ticket数据")
            for index,data in history_data.iterrows():
                try:
                    self.new_ticket(data)
                except Exception:
                    log.error("触发异常，回测终止")
                    log.error(traceback.format_exc())
                    return
        log.info("历史数据回放结束")

    def new_bar(self, bar):
        """"""
        # self.bar = bar
        self.datetime = bar['time']
        # self.cross_limit_order(bar)
        # self.cross_stop_order(bar)
        self.strategy.on_bar(bar)
        self.broker.do_pnl()
        # self.update_daily_close(bar.close_price)

    def new_ticket(self, data):
        return ""

    def statistics(self):
        result = self.broker.get_daily_results()
        res=Analysis(result)
        log.info("累计收益 {:.3f}".format(res["return_ratio"]))
        log.info("年化收益率 {:.3f}".format(res["annual_return_ratio"]))
        log.info("盈亏比 {:.3f}".format(res["pls"]))
        log.info("胜率 {:.3f}".format(res["wr"]))
        log.info("夏普 {:.3f}".format(res["sharp_ratio"]))
        log.info("最大回撤 {:.3f}".format(res["max_drawdown"]))
        log.info("波动率 {:.3f}".format(res["return_volatility"]))



    def set_parameters(self, symbol,mode, interval, start, end, rate, slippage, size, pricetick, capital):
        self.symbol =symbol
        self.interval = Interval(interval)
        self.rate = rate
        self.slippage = slippage
        self.size = size
        self.pricetick = pricetick
        self.start = start
        self.broker.set_capital(capital)
        self.end = end
        self.mode = mode






if __name__ == '__main__':
    """
    回测调用demo
    """
    engine = BacktestEngine()
    engine.set_parameters(
        symbol="BTC/USDT",
        mode=BacktestingMode.Bar,
        interval="1m",
        start=datetime(2019, 1, 1),
        end=datetime(2019, 4, 30),
        rate=0.3 / 10000,
        slippage=0.2,
        size=300,
        pricetick=0.2,
        capital=1000000,
    )
    feed = pd.read_csv("")
    engine.add_data(feed)
    engine.add_strategy(DoubleMaStrategy, {})

    engine.run_backtest()

    # df = engine.calculate_result()
    # engine.calculate_statistics()
    # engine.show_chart()

    # setting = OptimizationSetting()
    # setting.set_target("sharpe_ratio")
    # setting.add_parameter("atr_length", 3, 39, 1)
    # setting.add_parameter("atr_ma_length", 10, 30, 1)
    #
    # engine.run_ga_optimization(setting)
