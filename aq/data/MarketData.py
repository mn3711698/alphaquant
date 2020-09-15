class MarketData():
    bar_data={}
    ticket_data={}
    fee_data={}
    funding={}
    his_trade_data={}
    #回测时一次性加载所有数据，尽量使用list,字典消耗会更多
    def add_bar_data(self,data):
        #todo 需要增加bar数据检验逻辑
        self.bar_data=data

    def add_ticket_data(self,data):
        #todo 需要增加ticket数据检验逻辑
        self.ticket_data=data