class  TradeData():
    stop_order_count = 0
    stop_orders = {}
    active_stop_orders = {}
    limit_order_count = 0
    limit_orders = {}
    active_limit_orders = {}
    strade_count = 0
    trades = {}
    #todo 需要完善相应逻辑，及是否整合到Broker更加简单？有不有必要单独建一个类来管理？