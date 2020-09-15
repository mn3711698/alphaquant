// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © ilikeronline

//@version=4
strategy(title="翡翠趋势+RSI+Boll策略", overlay=true, commission_type=strategy.commission.percent, commission_value=0.036, default_qty_type=strategy.cash, default_qty_value=100, initial_capital=100, slippage=0)

//Boll 偏差模块

use_ema = input(false, title = "使用EMA?")
source = input(close, title = "来源", type = input.source)

length = input(20, title = "长度")
multiplier = input(2, title = "乘数", step = 0.1)

mean = use_ema ? wma(source, length) : sma(source, length)
stdev = stdev(source,length)
upper = mean + (stdev*multiplier)
lower = mean - (stdev*multiplier)

buy01 = open < lower and close > lower
sell01 = open > upper and close < upper

plotshape(buy01, location = location.belowbar, style = shape.triangleup, size=size.small,color = color.green  )
plotshape(sell01, location = location.abovebar, style = shape.triangledown,size=size.small, color = color.red)

//Boll 偏差模块结束

//RSI背离模块

pine_wma(x, y) =>
    norm = 0.0
    sum = 0.0
    for i = 0 to y - 1
        weight = (y - i) * y
        norm := norm + weight
        factor = close[i] < open[i] ? -1 : 1
        sum := sum + (x[i] * weight * factor)
    sum / norm

vl1 = input(defval=5, title="第一移动平均线长度", type=input.integer)
vl2 = input(defval=8, title="第二移动平均线长度", type=input.integer)
vl3 = vl1 + vl2
vl4 = vl2 + vl3
vl5 = vl3 + vl4

v1 = pine_wma(volume, vl1)
v2 = pine_wma(v1, vl2)
v3 = pine_wma(v2, vl3)
v4 = pine_wma(v3, vl4)
vol = pine_wma(v4, vl5)

vol_color = vol > 0 ? color.green : color.red

lbR = input(title="枢轴回溯-右", defval=5)
lbL = input(title="枢轴回溯-左", defval=5)
rangeUpper = input(title="回溯范围最大值", defval=60)
rangeLower = input(title="回溯范围最小值", defval=5)
plotBull = input(title="看涨背离", defval=true)
plotHiddenBull = input(title="看涨背离-隐藏", defval=false)
plotBear = input(title="看跌背离", defval=true)
plotHiddenBear = input(title="看跌背离-隐藏", defval=false)

bearColor = color.red
bullColor = color.green
hiddenBullColor = color.new(color.green, 25)
hiddenBearColor = color.new(color.red, 25)
textColor = color.white
noneColor = color.new(color.white, 100)

plFound = na(pivotlow(vol, lbL, lbR)) ? false : true
phFound = na(pivothigh(vol, lbL, lbR)) ? false : true

_inRange(cond) =>
    bars = barssince(cond == true)
    rangeLower <= bars and bars <= rangeUpper                


volLL = vol[lbR] < valuewhen(plFound, vol[lbR], 1) and _inRange(plFound[1])
priceHL = low[lbR] > valuewhen(plFound, low[lbR], 1)
hiddenBullCond = plotHiddenBull and priceHL and volLL and plFound
volLH = vol[lbR] < valuewhen(phFound, vol[lbR], 1) and _inRange(phFound[1])
priceHH = high[lbR] > valuewhen(phFound, high[lbR], 1)
bearCond = plotBear and priceHH and volLH and phFound
volHH = vol[lbR] > valuewhen(phFound, vol[lbR], 1) and _inRange(phFound[1])
priceLH = high[lbR] < valuewhen(phFound, high[lbR], 1)
hiddenBearCond = plotHiddenBear and priceLH and volHH and phFound

//RSI背离模块结束


//==趋势策略开始==
Trend_res       = input(defval = "", title = "趋势MTF", type = input.resolution)
Trend_res_final = Trend_res == "" ? timeframe.period : Trend_res

sources = input(defval=close, title="来源")
isHA = input(false, "使用HA蜡烛", input.bool)
heikenashi_1 = heikinashi(syminfo.tickerid)


security_1 = security(heikenashi_1, timeframe.period ,sources)
src = isHA ? security_1 : sources

per = input(defval=45, minval=1, title="采样周期")
mult = input(defval=4.06, minval=0.1, step = 0.1, title="乘数范围")


smoothrng(x, t, m) =>
    wper = t * 2 - 1
    avrng = wma(abs(x - x[1]), t)
    smoothrng = wma(avrng, wper) * m
    smoothrng
smrng = smoothrng(src, per, mult)

rngfilt(x, r) =>
    rngfilt = x
    rngfilt := x > nz(rngfilt[1]) ? x - r < nz(rngfilt[1]) ? nz(rngfilt[1]) : x - r :
       x + r > nz(rngfilt[1]) ? nz(rngfilt[1]) : x + r
    rngfilt
filt = rngfilt(src, smrng)


upward = 0.0
upward := filt > filt[1] ? nz(upward[1]) + 1 : filt < filt[1] ? 0 : nz(upward[1])
downward = 0.0
downward := filt < filt[1] ? nz(downward[1]) + 1 : filt > filt[1] ? 0 : nz(downward[1])


hband = filt + smrng
lband = filt - smrng

filtcolor = upward > 0 ? color.lime : downward > 0 ? color.red : color.orange
barcolor = src > filt and src > src[1] and upward > 0 ? color.lime :
   src > filt and src < src[1] and upward > 0 ? color.green :
   src < filt and src < src[1] and downward > 0 ? color.red :
   src < filt and src > src[1] and downward > 0 ? color.maroon : color.orange

longCond = bool(na)
shortCond = bool(na)
longCond := src > filt and src > src[1] and upward > 0 or
   src > filt and src < src[1] and upward > 0
shortCond := src < filt and src < src[1] and downward > 0 or
   src < filt and src > src[1] and downward > 0

CondIni = 0
CondIni := longCond ? 1 : shortCond ? -1 : CondIni[1]
longCondition = longCond and CondIni[1] == -1
shortCondition = shortCond and CondIni[1] == 1
//==趋势策略结束==


// === Stop LOSS ===
useStopLoss = input(true, title='----- 使用止损/止盈 -----')
sl_inp = input(2.76, title='止损 %', step=0.1)/100
tp_inp = input(4.95, title='止盈 %', step=0.1)/100
stop_level = strategy.position_avg_price * (1 - sl_inp)
take_level = strategy.position_avg_price * (1 + tp_inp)
stop_level_short = strategy.position_avg_price * (1 + sl_inp)
take_level_short = strategy.position_avg_price * (1 - tp_inp)
// === Stop LOSS ===



// === strategy ===
strategy.entry("Long", strategy.long, when = bullCond, comment="Bull多")
strategy.entry("Long", strategy.long, when = hiddenBullCond, comment="Hbull多")
strategy.entry("Long", strategy.long, when = buy01, comment="Boll多")
strategy.entry("Long", strategy.long, when = longCondition, comment="趋势多")


strategy.close("Long",  when= bearCond , comment="Bear出多")
strategy.close("Long",  when= hiddenBearCond, comment="Hbear出多")
strategy.close("Long",  when= sell01, comment="Boll出多")
strategy.close("Long",  when= shortCondition, comment="趋势出多")


strategy.entry("Short", strategy.short, when = bearCond , comment="Bear空")
strategy.entry("Short", strategy.short, when = hiddenBearCond , comment="Hbear空")
strategy.entry("Short", strategy.short, when = sell01, comment="Boll空")
strategy.entry("Short", strategy.short, when = shortCondition, comment="趋势空")


strategy.close("Short", when=bullCond , comment="Bull出空")
strategy.close("Short", when=hiddenBullCond, comment="Hbear出空")
strategy.close("Short", when=buy01, comment="Boll出空")
strategy.close("Short", when=longCondition, comment="趋势出空")


if useStopLoss and strategy.position_size > 0
    strategy.exit("Stop Loss/Profit Long","Long", stop=stop_level, limit=take_level)
if useStopLoss and strategy.position_size < 0
    strategy.exit("Stop Loss/Profit Short","Short", stop=stop_level_short, limit=take_level_short)

// === strategy ===
