from operator import itemgetter

class DepthCache(object):
    def __init__(self, symbol):
        """Initialise the DepthCache
        :param symbol: Symbol to create depth cache for
        :type symbol: string
        """
        self.symbol = symbol
        self._bids = {}
        self._asks = {}
        self.update_time = None
    def add_bid(self, bid):
        """Add a bid to the cache
        :param bid:
        :return:
        """
        self._bids[bid[0]] = float(bid[1])
        if bid[1] == "0.00000000":
            del self._bids[bid[0]]
    def add_ask(self, ask):
        """Add an ask to the cache
        :param ask:
        :return:
        """
        self._asks[ask[0]] = float(ask[1])
        if ask[1] == "0.00000000":
            del self._asks[ask[0]]
    def get_bids(self):
        """Get the current bids
        :return: list of bids with price and quantity as floats
        .. code-block:: python
            [
                [
                    0.0001946,  # Price
                    45.0        # Quantity
                ],
                [
                    0.00019459,
                    2384.0
                ],
                [
                    0.00019158,
                    5219.0
                ],
                [
                    0.00019157,
                    1180.0
                ],
                [
                    0.00019082,
                    287.0
                ]
            ]
        """
        return DepthCache.sort_depth(self._bids, reverse=True)

    def get_asks(self):
        """Get the current asks
        :return: list of asks with price and quantity as floats
        .. code-block:: python
            [
                [
                    0.0001955,  # Price
                    57.0'       # Quantity
                ],
                [
                    0.00019699,
                    778.0
                ],
                [
                    0.000197,
                    64.0
                ],
                [
                    0.00019709,
                    1130.0
                ],
                [
                    0.0001971,
                    385.0
                ]
            ]
        """
        return DepthCache.sort_depth(self._asks, reverse=False)

    @staticmethod
    def sort_depth(vals, reverse=False):
        """Sort bids or asks by price
        """
        lst = [[float(price), quantity] for price, quantity in vals.items()]
        lst = sorted(lst, key=itemgetter(0), reverse=reverse)
        return lst