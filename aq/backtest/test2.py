#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究
# zsxq 知识星球

import wx
import wx.adv
import wx.grid
import wx.html2
import os
import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
#from matplotlib.backends.backend_wx import NavigationToolbar2Wx
import matplotlib.gridspec as gridspec # 分割子图
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import tushare as ts
import baostock as bs
import mpl_finance as mpf # attention: mpl_finance 从2020年开始更新至 mplfinance

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

#参数设置
pd.set_option('display.expand_frame_repr',False) # False不允许换行
pd.set_option('display.max_rows', 20) # 显示的最大行数
pd.set_option('display.max_columns', 18) # 显示的最大列数
pd.set_option('precision', 2) # 显示小数点后的位数

def bs_k_data_stock(code_val='sz.000651', start_val='2009-01-01', end_val='2019-06-01',
                    freq_val='d', adjust_val='3'):

    # 登陆系统
    lg = bs.login()
    # 获取历史行情数据
    fields= "date,open,high,low,close,volume,turn,peTTM,pbMRQ"
    df_bs = bs.query_history_k_data_plus(code_val, fields, start_date=start_val, end_date=end_val,
                                 frequency=freq_val, adjustflag=adjust_val) # <class 'baostock.data.resultset.ResultData'>
    # frequency="d"取日k线，adjustflag="3"默认不复权，1：后复权；2：前复权

    data_list = []

    while (df_bs.error_code == '0') & df_bs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(df_bs.get_row_data())
    result = pd.DataFrame(data_list, columns=df_bs.fields)

    for i, v in result.turn.items():
        if v.find('.') == -1:
            result.iloc[i, result.columns.get_loc('turn')] = np.nan

    result = result.astype({'turn': 'float64', 'pbMRQ': 'float64', 'peTTM': 'float64','volume':'uint64',
                            'close': 'float64', 'open': 'float64', 'low': 'float64', 'high': 'float64'})

    result.volume = result.volume / 100  # 单位转换：股-手
    result.volume = result.volume.astype('uint64')
    result.date = pd.DatetimeIndex(result.date)
    result.set_index("date", drop=True, inplace=True)
    result.index = result.index.set_names('Date')
    result['OpenInterest'] = 0
    result.turn.fillna(method='ffill', inplace=True)

    recon_data = {'high': result.high, 'low': result.low, 'open': result.open, 'close': result.close,\
                  'volume': result.volume,
                  'turn': result.turn,
                  'peTTM': result.peTTM,
                  'pbMRQ': result.pbMRQ}
    df_recon = pd.DataFrame(recon_data)

    # 登出系统
    bs.logout()
    return df_recon


# 搭建backtrader版股票本地自定义回测平台
# 对应公众号文章《搭建系统|听说backtrader很不错！把它集成到本地GUI回测平台中！》 - vbt.1.1
# 对应公众号文章《搭建系统|别只盯MA、KDJ、MACD这些技术指标，择时策略也能叠加基本面指标！》 - vbt.1.2
# 对应公众号文章《搭建系统|本地量化工具集成开源量化框架backtrader操作指南！》 - vbt.1.3
# 对应公众号文章《搭建系统|继承backtrader的本地量化回测平台如何玩转多股轮动策略！》 - vbt.1.4

if True:
    import wx.gizmos
    import Code_for_strategy
    from aq.backtest.Code_for_strategy import *
    from importlib import reload

    try:
        import backtrader as bt
    except ImportError:
        raise ImportError(
            'backtrader seems to be missing. Needed for back testing support')

    # 扩展backtrader财务数据格式
    class Add_financedata(bt.feeds.PandasData):
        lines = ('turn', 'peTTM', 'pbMRQ',)
        params = (('turn', -1), ('peTTM', -1), ('pbMRQ', -1),)

    # 点击策略列表函数，打开对应的文件
    # 在线修改文件中的代码，修改后点击保存
    class EditorDialog(wx.Dialog):  # user-defined

        def __init__(self, parent, text):
            wx.Dialog.__init__(self, parent, -1, u"策略编辑", size=(600, 500),
                               style=wx.CAPTION | wx.CLOSE_BOX | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)

            label_sure = wx.StaticText(self, -1, text)
            label_sure.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))

            butsbox = wx.BoxSizer(wx.HORIZONTAL)
            okbtn = wx.Button(self, wx.ID_OK, u"保存")
            okbtn.SetDefault()
            clbtn = wx.Button(self, wx.ID_CANCEL, u"取消")
            butsbox.Add(okbtn, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
            butsbox.Add(clbtn, 1, wx.ALIGN_CENTER | wx.ALL, 5)

            self.contents = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(500, 400))

            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(label_sure, flag=wx.ALIGN_CENTER)
            sizer.Add(butsbox, flag=wx.ALIGN_CENTER)
            sizer.Add(self.contents, flag=wx.EXPAND)
            self.SetSizer(sizer)

        def OpenValue(self):

            with open('Code_for_strategy.py', 'r+', encoding='utf-8') as f:
                self.contents.SetValue(f.read())

        def SaveValue(self):

            with open('Code_for_strategy.py', 'r+', encoding='utf-8') as f:
                rawcontes = self.contents.GetValue()
                rawcontes = rawcontes.replace("”", "\"")
                rawcontes = rawcontes.replace("“", "\"")
                rawcontes = rawcontes.replace("‘", "\'")
                rawcontes = rawcontes.replace("’", "\'")
                f.write(rawcontes)

    class CollegeTreeListCtrl(wx.gizmos.TreeListCtrl):

        def __init__(self, parent=None, id=-1, pos=(0, 0), size=wx.DefaultSize,
                     style=wx.TR_DEFAULT_STYLE | wx.TR_FULL_ROW_HIGHLIGHT):

            wx.gizmos.TreeListCtrl.__init__(self, parent, id, pos, size, style)

            self.root = None
            self.InitUI()

        def InitUI(self):
            self.il = wx.ImageList(16, 16, True)
            self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16, 16)))
            self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16, 16)))
            self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16, 16)))
            self.SetImageList(self.il)
            self.AddColumn(u'名称')
            self.AddColumn(u'类型')
            self.AddColumn(u'函数')
            self.SetColumnWidth(0, 150)
            self.SetColumnWidth(1, 60)
            self.SetColumnWidth(2, 140)

        def refDataShow(self, newDatas):
            # if self.root != None:
            #    self.DeleteAllItems()

            if newDatas != None:
                self.root = self.AddRoot(u'择时策略')
                self.SetItemText(self.root, "", 1) # 第1列上添加
                self.SetItemText(self.root, "", 2) # 第2列上添加

                for cityID in newDatas.keys():# 填充整个树
                    child = self.AppendItem(self.root, cityID)
                    lastList = newDatas.get(cityID, [])
                    self.SetItemText(child, cityID + u" (共" + str(len(lastList)) + u"个)", 0)
                    self.SetItemImage(child, 0, which=wx.TreeItemIcon_Normal) # wx.TreeItemIcon_Expanded

                    for index in range(len(lastList)):
                        college = lastList[index]  # TreeItemData是每一个ChildItem的唯一标示
                        # 以便在点击事件中获得点击项的位置信息
                        # "The TreeItemData class no longer exists, just pass your object directly to the tree instead
                        # data = wx.TreeItemData(cityID + "|" + str(index))
                        last = self.AppendItem(child, str(index), data=cityID + "|" + str(index))
                        self.SetItemText(last, college.get('名称', ''), 0)
                        self.SetItemText(last, college.get('类型', ''), 1)
                        self.SetItemText(last, str(college.get('函数', '')), 2)
                        self.SetItemImage(last, 0, which=wx.TreeItemIcon_Normal) # wx.TreeItemIcon_Expanded
                        self.Expand(self.root)
                        pass

        """
        def DeleteSubjectItem(self, treeItemId):
            self.Delete(treeItemId)
            self.Refresh()
            pass
        """

    class BacktdPanel(wx.Panel):
        def __init__(self, parent):
            wx.Panel.__init__(self,parent=parent, id=-1)

            # 分割子图实现代码
            self.figure = Figure()
            gs = gridspec.GridSpec(2, 1, left=0.05, bottom=0.1, right=0.95, top=0.95, wspace=None, hspace=0.1,
                                   height_ratios=[2, 1])
            self.graph_trade = self.figure.add_subplot(gs[0, :])
            self.graph_profit = self.figure.add_subplot(gs[1, :])
            self.FigureCanvas = FigureCanvas(self, -1, self.figure) # figure加到FigureCanvas

            self.NavigationToolbar = NavigationToolbar(self.FigureCanvas)

            self.StaticText = wx.StaticText(self, -1, label=u'微信公众号《元宵大师带你用Python量化交易》')

            self.SubBoxSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.SubBoxSizer.Add(self.NavigationToolbar, proportion=0, border=2, flag=wx.ALL | wx.EXPAND)
            self.SubBoxSizer.Add(self.StaticText, proportion=0, border=2, flag=wx.ALL | wx.EXPAND)

            self.TopBoxSizer = wx.BoxSizer(wx.VERTICAL)
            self.TopBoxSizer.Add(self.FigureCanvas, proportion=1, border=2, flag=wx.ALL|wx.EXPAND)
            self.TopBoxSizer.Add(self.SubBoxSizer, proportion=0, border=2, flag=wx.ALL | wx.EXPAND)
            self.SetSizer(self.TopBoxSizer)
            self.Fit()

    class BacktdFrame(wx.Frame):

        #stock_list = ["sz.002273", "sz.000876", "sh.601319"]
        stock_list = ["sh.600705", "sh.600578", "sz.000425", "sz.002493", "sh.600208", "sh.601333", "sh.601872",
                      "sh.600887", "sh.600339", "sh.601992", "sh.600297", "sz.002415", "sh.600027", "sz.000959",
                      "sh.600886", "sz.000898", "sz.000825", "sz.000157", "sh.601633", "sh.600031", "sh.601111",
                      "sz.002736", "sh.600690", "sh.601898", "sh.600958", "sh.601939", "sz.001979", "sz.002024",
                      "sh.601009", "sh.600999", "sh.601211", "sh.601688", "sz.000333", "sz.002142"]

        def __init__(self, parent=None, id=-1, Fun_SwFrame=None):
            # hack to help on dual-screen, need something better XXX - idfah
            displaySize = wx.DisplaySize() # (1920, 1080)
            displaySize = 0.85 * displaySize[0], 0.75 * displaySize[1]

            # call base class constructor
            wx.Frame.__init__(self, parent = None, title = u'量化软件', size=displaySize,
                          style=wx.DEFAULT_FRAME_STYLE^wx.MAXIMIZE_BOX) # size=(1000,600)

            self.fun_swframe = Fun_SwFrame # 用于回测功能集成到整体系统中

            # 创建并初始化 treeListCtrl--策略树
            self.init_tree()

            # 创建并初始化 wxGrid--回测结果表
            self.init_grid()

            # 创建并初始化 TextCtrl--日志框
            self.log_tx = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(260, 320))

            # 创建并初始化 ListBox--股票组合列表
            self.listBox = wx.ListBox(self, -1, size=(260, 200), choices=self.stock_list, style=wx.LB_EXTENDED)
            self.listBox.Bind(wx.EVT_LISTBOX_DCLICK, self.event_listCtrlSelect)

            vboxnetA = wx.BoxSizer(wx.VERTICAL)  # 纵向box
            vboxnetA.Add(self.treeListCtrl, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=2)  # proportion参数控制容器尺寸比例
            vboxnetA.Add(self.listBox, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=2)
            vboxnetA.Add(self.grid, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=2)
            vboxnetA.Add(self.log_tx, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=2)

            # 创建参数区面板
            self.ParaPanel = wx.Panel(self,-1)

            # 创建显示区面板
            self.DispPanel = BacktdPanel(self)  # 自定义
            # Note that event is a MplEvent
            self.DispPanel.FigureCanvas.mpl_connect('motion_notify_event', self.event_UpdateStatusBar)
            self.DispPanel.FigureCanvas.Bind(wx.EVT_ENTER_WINDOW, self.event_ChangeCursor)
            self.statusBar = wx.StatusBar(self, -1)
            self.SetStatusBar(self.statusBar)
            # print(self.DispPanel2.GetSize()) # 默认是(20,20)

            # matplotlib显示的子图
            self.graph_trade = self.DispPanel.graph_trade
            self.graph_profit = self.DispPanel.graph_profit

            # 第二层布局
            self.add_stock_para_lay()
            vbox_sizer_a = wx.BoxSizer(wx.VERTICAL) # 纵向box
            vbox_sizer_a.Add(self.ParaPanel, proportion=1, flag=wx.EXPAND|wx.BOTTOM, border=2)  # 添加行情参数布局
            vbox_sizer_a.Add(self.DispPanel, proportion=10, flag=wx.EXPAND|wx.BOTTOM, border=2)
            vbox_sizer_a.Add(self.statusBar, proportion=0, flag=wx.EXPAND|wx.BOTTOM, border=2)

            # 第一层布局
            self.HBoxPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.HBoxPanelSizer.Add(vboxnetA, proportion=1, border=2, flag=wx.EXPAND | wx.ALL)
            self.HBoxPanelSizer.Add(vbox_sizer_a, proportion=10, border=2, flag=wx.EXPAND | wx.ALL)
            self.SetSizer(self.HBoxPanelSizer)  # 使布局有效

            self.function = ''

        def init_grid(self):
            self.grid = wx.grid.Grid(self, -1)
            self.grid.CreateGrid(10, 2)
            self.grid.SetColLabelValue(0, "回测选项")
            self.grid.SetColLabelValue(1, "回测结果")

        def init_tree(self):
            self.treeListCtrl = CollegeTreeListCtrl(parent=self, size=(260, 200))
            self.treeListCtrl.Bind(wx.EVT_TREE_SEL_CHANGED, self.event_OnTreeListCtrlClickFunc)
            self.colleges = {
                u'经典策略': [
                    {'名称': u'N日突破', '类型': u'趋势', '函数': u'未定义'},
                    {'名称': u'动能转换', '类型': u'趋势','函数': u'未定义'},
                    {'名称': u'KDJ峰谷', '类型': u'波动','函数': u'未定义'},
                    {'名称': u'均线交叉', '类型': u'趋势','函数': u'dua_ma_strategy'}],
                u'自定义策略': [
                    {'名称': u'yx-zl-1', '类型': u'基本面','函数': u'FinanceDatStrategy'},
                    {'名称': u'yx-zl-2', '类型': u'趋势','函数': u'未定义'},
                    {'名称': u'yx-zl-3', '类型': u'组合型', '函数': u'MulitShiftStrategy'},
                    {'名称': u'yx-zl-4', '类型': u'波动','函数': u'未定义'}]
            }
            # TreeCtrl显示数据接口
            self.treeListCtrl.refDataShow(self.colleges)

        def add_stock_para_lay(self):

            # 回测参数
            back_para_box = wx.StaticBox(self.ParaPanel, -1, u'回测参数')
            back_para_sizer = wx.StaticBoxSizer(back_para_box, wx.HORIZONTAL)

            # 行情参数——日历控件时间周期
            self.dpc_end_time = wx.adv.DatePickerCtrl(self.ParaPanel, -1,
                                                      style = wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE)#结束时间
            self.dpc_start_time = wx.adv.DatePickerCtrl(self.ParaPanel, -1,
                                                        style = wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE)#起始时间

            self.start_date_box = wx.StaticBox(self.ParaPanel, -1, u'开始日期(Start)')
            self.end_date_box = wx.StaticBox(self.ParaPanel, -1, u'结束日期(End)')
            self.start_date_sizer = wx.StaticBoxSizer(self.start_date_box, wx.VERTICAL)
            self.end_date_sizer = wx.StaticBoxSizer(self.end_date_box, wx.VERTICAL)
            self.start_date_sizer.Add(self.dpc_start_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
            self.end_date_sizer.Add(self.dpc_end_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

            date_time_now = wx.DateTime.Now()  # wx.DateTime格式"03/03/18 00:00:00"
            self.dpc_end_time.SetValue(date_time_now)
            self.dpc_start_time.SetValue(date_time_now.SetYear(date_time_now.year - 1))

            self.stock_code_box = wx.StaticBox(self.ParaPanel, -1, u'股票代码')
            self.stock_code_sizer = wx.StaticBoxSizer(self.stock_code_box, wx.VERTICAL)
            self.stock_code_input = wx.TextCtrl(self.ParaPanel, -1, "sz.000876", style=wx.TE_LEFT|wx.TE_PROCESS_ENTER)
            self.stock_code_input.Bind(wx.EVT_TEXT_ENTER, self.event_EnterStcode)
            self.stock_code_sizer.Add(self.stock_code_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

            self.init_cash_box = wx.StaticBox(self.ParaPanel, -1, u'初始资金')
            self.init_cash_sizer = wx.StaticBoxSizer(self.init_cash_box, wx.VERTICAL)
            self.init_cash_input = wx.TextCtrl(self.ParaPanel, -1, "10000", style=wx.TE_LEFT)
            self.init_cash_sizer.Add(self.init_cash_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

            self.init_trader_box = wx.StaticBox(self.ParaPanel, -1, u'交易规模')
            self.init_trader_sizer = wx.StaticBoxSizer(self.init_trader_box, wx.VERTICAL)
            self.init_trader_input = wx.TextCtrl(self.ParaPanel, -1, "500", style=wx.TE_LEFT)
            self.init_trader_sizer.Add(self.init_trader_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

            self.init_commission_box = wx.StaticBox(self.ParaPanel, -1, u'手续费')
            self.init_commission_sizer = wx.StaticBoxSizer(self.init_commission_box, wx.VERTICAL)
            self.init_commission_input = wx.TextCtrl(self.ParaPanel, -1, "0.002", style=wx.TE_LEFT)
            self.init_commission_sizer.Add(self.init_commission_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

            # 回测按钮
            self.start_back_but = wx.Button(self.ParaPanel, -1, "开始回测")
            self.start_back_but.Bind(wx.EVT_BUTTON, self.event_start_run)  # 绑定按钮事件

            # 返回主菜单按钮
            self.return_menu_but = wx.Button(self.ParaPanel, -1, "主菜单")
            self.return_menu_but.Bind(wx.EVT_BUTTON, self.event_SwitchMenu)  # 绑定按钮事件
            self.return_menu_but.Bind(wx.EVT_BUTTON, self.event_SwitchMenu)  # 绑定按钮事件

            back_para_sizer.Add(self.start_date_sizer, proportion=0, flag=wx.EXPAND|wx.CENTER|wx.ALL, border=10)
            back_para_sizer.Add(self.end_date_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
            back_para_sizer.Add(self.stock_code_sizer, proportion=0,flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
            back_para_sizer.Add(self.init_cash_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
            back_para_sizer.Add(self.init_trader_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
            back_para_sizer.Add(self.init_commission_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
            back_para_sizer.Add(self.start_back_but, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
            back_para_sizer.Add(self.return_menu_but, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)

            self.ParaPanel.SetSizer(back_para_sizer)

        def tx_to_ctrl(self):

            with open('logtrade.txt', 'r+', encoding='utf-8') as f:
                self.log_tx.SetValue(f.read())
                f.truncate(0) # 清空文件内容

        def MessageDiag(self, info):
            dlg_mesg = wx.MessageDialog(None, info, u"温馨提示",
                                        wx.YES_NO | wx.ICON_INFORMATION)
            if dlg_mesg.ShowModal() == wx.ID_YES:
                print("return choose yes option")
            dlg_mesg.Destroy()

        def update_subgraph(self):
            self.DispPanel.FigureCanvas.draw()

        def clear_subgraph(self):
            # 再次画图前,必须调用该命令清空原来的图形
            self.graph_trade.clear()
            self.graph_profit.clear()

        def backtrader_excetue(self, st_code, cash_val=10000, stake_val=500, commission_val=0.002,
                                    fromdate_val = '', todate_val = ''):
            # 此部分与backtrader使用相同

            # 加载数据
            cerebro = bt.Cerebro()  # 初始化cerebro回测系统设置
            for s in st_code:
                dat_feed_pandas = bs_k_data_stock(s, start_val=fromdate_val.strftime('%Y-%m-%d'),
                                           end_val=todate_val.strftime('%Y-%m-%d'))
                data = Add_financedata(dataname=dat_feed_pandas, fromdate=fromdate_val, todate=todate_val)  # 加载回测期间的数据
                cerebro.adddata(data, name=s)  # 将数据传入回测系统
            # cerebro.optstrategy(dua_ma_strategy, ma_long=range(10, 20)) # 导入策略参数寻优 与addstrategy二选一

            cerebro.addstrategy(self.function)  # 将交易策略加载到回测系统中
            cerebro.broker.setcash(cash_val)  # 设置初始资本为10,000
            cerebro.addsizer(bt.sizers.FixedSize, stake=stake_val)  # 设定每次交易买入的股数
            cerebro.broker.setcommission(commission=commission_val)  # 设置交易手续费为 0.2%

            print('初始资金: %.2f' % cerebro.broker.getvalue())
            self.grid.SetCellValue(0, 0, '初始资金')
            self.grid.SetCellValue(0, 1, str(cerebro.broker.getvalue()))

            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DW')

            results = cerebro.run()  # 运行回测系统
            strat = results[0]
            print(f'最终资金: {round(cerebro.broker.getvalue(), 2)}')  # 获取回测结束后的总资金
            self.grid.SetCellValue(1, 0, '最终资金')
            self.grid.SetCellValue(1, 1, str(cerebro.broker.getvalue()))

            print('回撤指标:', strat.analyzers.DW.get_analysis())
            self.grid.SetCellValue(2, 0, '股价回撤')
            self.grid.SetCellValue(2, 1, str(strat.analyzers.DW.get_analysis()['drawdown']))
            self.grid.SetCellValue(3, 0, '资金回撤')
            self.grid.SetCellValue(3, 1, str(strat.analyzers.DW.get_analysis()['moneydown']))
            print('夏普比率:', strat.analyzers.SharpeRatio.get_analysis())
            self.grid.SetCellValue(4, 0, '夏普比率')
            self.grid.SetCellValue(4, 1, str(strat.analyzers.SharpeRatio.get_analysis()['sharperatio']))
            #cerebro.plot(style='candlestick')

        def draw_backTest(self):
            # 可视化处理回测结果
            df_broker_dat = self.df_trader
            df_broker_dat["profit"].fillna(0, inplace=True)

            for kl_index, today in df_broker_dat.iterrows():
                # 买入/卖出执行代码
                if np.isnan(today.buy) == False:  # 买入
                    start = df_broker_dat.index.get_loc(kl_index)
                    self.graph_trade.scatter(kl_index, today.buy, marker='v', color='r', alpha=1)

                if np.isnan(today.sell) == False:  # 卖出
                    end = df_broker_dat.index.get_loc(kl_index)
                    if df_broker_dat.close[end] < df_broker_dat.close[start]:  # 赔钱显示绿色
                        self.graph_trade.fill_between(df_broker_dat.index[start:end], 0, df_broker_dat.close[start:end],
                                                 color='green', alpha=0.38)
                    else:  # 赚钱显示红色
                        self.graph_trade.fill_between(df_broker_dat.index[start:end], 0, df_broker_dat.close[start:end], color='red',
                                                 alpha=0.38)
                    self.graph_trade.scatter(kl_index, today.sell, marker='v', color='g', alpha=1)

            # 绘制收益曲线
            self.graph_profit.bar(df_broker_dat.index, df_broker_dat.profit,
                         color=['r' if df_broker_dat.loc[x, "profit"] > 0 else 'g' for x in
                                df_broker_dat.index], label = u"单笔交易盈亏")
            df_broker_dat['profit'].cumsum().plot(grid=True, ax=self.graph_profit, label="累计收益")

            # 绘制收盘价/资金曲线曲线当前的滚动最高值
            df_broker_dat['close'].plot(grid=True, ax=self.graph_trade, label="收盘价")

            # 图表显示参数配置
            for label in self.graph_trade.xaxis.get_ticklabels():
                label.set_visible(False)
            for label in self.graph_profit.xaxis.get_ticklabels():
                label.set_rotation(45)
                label.set_fontsize(10)  # 设置标签字体
            self.graph_trade.set_xlabel("")

            self.graph_trade.set_title(u'量化回测度量')
            self.graph_trade.legend(loc='best', shadow=True, fontsize='8')
            self.graph_profit.legend(loc='best', shadow=True, fontsize='8')
            self.df_trader.drop(self.df_trader.index, axis=0, inplace=True) # 清空收集的交易详情
            plt.show()

        def event_listCtrlSelect(self, event):
            indexSelected = event.GetEventObject().GetSelection()
            print('选中Item的下标：', indexSelected)
            event.GetEventObject().Delete(indexSelected)

        def event_ChangeCursor(self, event):
            self.DispPanel.FigureCanvas.SetCursor(wx.Cursor(wx.CURSOR_BULLSEYE))

        def event_UpdateStatusBar(self, event):
            if event.inaxes:
                self.statusBar.SetStatusText(
                    "x={}  y={}".format(event.xdata, event.ydata))

        def event_start_run(self, event):
            # 点击回测按钮
            st_code = [self.listBox.GetString(i) for i in range(0, self.listBox.GetCount())]
            sdate_obj = self.dpc_start_time.GetValue()
            sdate_val = datetime.datetime(sdate_obj.year, sdate_obj.month + 1, sdate_obj.day)
            edate_obj = self.dpc_end_time.GetValue()
            edate_val = datetime.datetime(edate_obj.year, edate_obj.month + 1, edate_obj.day)

            cash_value = float(self.init_cash_input.GetValue())
            trade_value = float(self.init_trader_input.GetValue())
            commission_value = float(self.init_commission_input.GetValue())

            if self.function == "":
                self.MessageDiag("该策略未定义函数接口")
                return

            self.backtrader_excetue(st_code, cash_value, trade_value, commission_value,
                                    sdate_val, edate_val)

            self.tx_to_ctrl()
            self.clear_subgraph() # 必须清理图形才能显示下一幅图
            self.draw_backTest()
            self.update_subgraph() # 必须刷新才能显示下一幅图

        def event_SwitchMenu(self, event):
            self.fun_swframe(0)  # 切换 Frame 主界面

        def event_OnTreeListCtrlClickFunc(self, event):
            self.currentTreeItem = self.treeListCtrl.GetItemText(event.GetItem())
            self.function = ''
            if self.currentTreeItem != None:
                # 当前选中的TreeItemId对象，方便进行删除等其他的操作
                for fst_val in self.colleges.values():
                    for index in fst_val:
                        if (index.get('名称', '') == self.currentTreeItem):
                            if index.get('函数', '') != "未定义":
                                myDialog = EditorDialog(self, self.currentTreeItem)
                                myDialog.OpenValue()
                                if myDialog.ShowModal() == wx.ID_OK:
                                    myDialog.SaveValue()
                                    print("Saved")
                                else:
                                    print("Cancel")
                                reload(Code_for_strategy)
                                self.function = getattr(Code_for_strategy, index.get('函数', ''))
                                self.df_trader = getattr(Code_for_strategy, "df_trader")
                                break
                            else:
                                self.MessageDiag("该策略未定义函数接口")
                print('点击了：{0} {1}'.format(self.currentTreeItem, self.function))

        def event_EnterStcode(self, event):
            st_code = self.stock_code_input.GetValue()

            if self.listBox.FindString(st_code) == -1:
                self.listBox.InsertItems([st_code], 0)  # 插入item
            else:
                print(u"股票已经存在！")

    class StockApp(wx.App):

        def OnInit(self):
            self.frame = BacktdFrame()
            self.frame.Show()
            self.frame.Center()
            self.SetTopWindow(self.frame)
            return True

    if __name__ == '__main__':
        app = StockApp()
        app.MainLoop()