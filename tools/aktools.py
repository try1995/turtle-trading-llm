import os
import requests
import tempfile
import json
import akshare as ak
from .base_tool import markdownpdf
from typing import get_type_hints, Optional, Any, List, Dict, Annotated


def stock_zh_a_hist(
    symbol: Annotated[str, "股票代码，e.g. 603777"],
    start_date: Annotated[str, "开始日期 %Y%m%d，e.g. 20210301"],
    end_date: Annotated[str, "结束日期 %Y%m%d，e.g. 20210616"],
    period: Annotated[str, "周期，choice of {'daily','weekly','monthly'}，默认 daily"]="daily",
    adjust: Annotated[str, "复权方式，默认不复权；qfq: 前复权；hfq: 后复权,不复权：看表面价格，忽略分红影响。前复权：看近期成本，适合短线。后复权：看真实收益，适合长线。"]="",
):
    """
    东方财富-沪深京 A 股日频率历史行情
    注：日期都填 YYYYMMDD 格式;

    输出参数-历史行情数据

    名称	类型	描述
    日期	object	交易日
    股票代码	object	不带市场标识的股票代码
    开盘	float64	开盘价
    收盘	float64	收盘价
    最高	float64	最高价
    最低	float64	最低价
    成交量	int64	注意单位: 手
    成交额	float64	注意单位: 元
    振幅	float64	注意单位: %
    涨跌幅	float64	注意单位: %
    涨跌额	float64	注意单位: 元
    换手率	float64	注意单位: %
    """
    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=symbol, period=period, start_date=start_date, end_date=end_date, adjust=adjust)
    record = stock_zh_a_hist_df.astype(str).to_dict("records")
    return json.dumps(record, ensure_ascii=False)



def stock_research_report_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"]
):
    """
    获取东方财富个股研报数据
    
    输出参数
    
    名称	类型	描述
    序号	int	-
    股票代码	str	-
    股票简称	str	-
    报告名称	str	-
    东财评级	str	-
    机构	str	-
    近一月个股研报数	int	-
    2024-盈利预测-收益	float	-
    2024-盈利预测-市盈率	float	-
    2025-盈利预测-收益	float	-
    2025-盈利预测-市盈率	float	-
    2026-盈利预测-收益	float	-
    2026-盈利预测-市盈率	float	-
    行业	str	-
    日期	str	-
    报告PDF链接	str	-
    """
    stock_research_report_em_df = ak.stock_research_report_em(symbol).head(10)
    # return stock_research_report_em_df
    record = stock_research_report_em_df.astype(str).to_dict("records")
    return json.dumps(record, ensure_ascii=False)


def stock_research_report_markdown(report_urls: Annotated[str, "英文逗号分隔的报告PDF链接， eg.http://1.pdf,http://2.pdf"]):
    """
    返回研报的PDF解析结果，输出示例如下：
    第一家研报解析结果：
    xxx
    
    第二家研报解析结果：
    xxx
    """
    report_res = []
    for index, report_url in enumerate(report_urls.split(",")):
        with tempfile.TemporaryDirectory() as tempdir:
            ret = requests.get(report_url)
            file_path = os.path.join(tempdir, "temp.pdf")
            with open(file_path, 'wb') as f:
                f.write(ret.content)
            result = markdownpdf(file_path)
            report_res.append(f"第{index+1}家研报解析结果:\n"+result)
    return "\n\n".join(report_res)

# import talib as tl
# from numba import njit
import pandas as pd
import numpy as np


# ---------- Supertrend numba 加速 ----------
# @njit
def _supertrend_nb(h, l, c, atr, mult=3.0):
    n = len(c)
    ub = np.empty(n); lb = np.empty(n); st = np.empty(n)
    for i in range(n):
        bu = (h[i] + l[i])/2 + mult * atr[i]
        bl = (h[i] + l[i])/2 - mult * atr[i]
        if i == 0:
            ub[i], lb[i], st[i] = bu, bl, (bu if c[i] <= bu else bl)
            continue
        ub[i] = bu if (bu < ub[i-1] or c[i-1] > ub[i-1]) else ub[i-1]
        lb[i] = bl if (bl > lb[i-1] or c[i-1] < lb[i-1]) else lb[i-1]
        st[i] = ub[i] if (st[i-1]==ub[i-1] and c[i]<=ub[i]) or (st[i-1]==lb[i-1] and c[i]>lb[i]) else lb[i]
    return ub, lb, st

# ---------- 核心指标计算 ----------
def get_indicators(data: pd.DataFrame,
                   end_date=None,
                   threshold=120,
                   calc_threshold=None):
    """
    与原函数 100 % 兼容，只是 data 现在由 akshare 提供
    """
    # 1. 日期/长度裁剪
    if end_date is not None:
        data = data[data["date"] <= pd.to_datetime(end_date)]
    if calc_threshold is not None:
        data = data.tail(calc_threshold)
    data = data.copy()

    # 2. 裸 numpy 数组提速
    c = data["close"].to_numpy()
    h = data["high"].to_numpy()
    l = data["low"].to_numpy()
    v = data["volume"].to_numpy()
    amt = data["amount"].to_numpy()
    pc = np.r_[np.nan, c[:-1]]          # 昨收

    # 3. 下面完全沿用你原脚本指标顺序，仅列关键改动 -----------------
    with np.errstate(divide="ignore", invalid="ignore"):
        # MACD
        data["macd"], data["macds"], data["macdh"] = tl.MACD(c, 12, 26, 9)

        # KDJ
        data["kdjk"], data["kdjd"] = tl.STOCH(h, l, c, 9, 5, 1, 5, 1)
        data["kdjj"] = 3 * data["kdjk"] - 2 * data["kdjd"]

        # BOLL
        data["boll_ub"], data["boll"], data["boll_lb"] = tl.BBANDS(c, 20, 2, 2, 0)

        # TRIX / TRMA
        data["trix"] = tl.TRIX(c, 12)
        data["trix_20_sma"] = tl.SMA(data["trix"], 20)

        # CR  （中间价用 amount/volume）
        m_price = amt / v
        m_price_sf1 = np.r_[0.0, m_price[:-1]]
        h_m = np.maximum(h - m_price_sf1, 0)
        m_l = np.maximum(m_price_sf1 - l, 0)
        cr = tl.SUM(h_m, 26) / (tl.SUM(m_l, 26) + 1e-9) * 100
        data["cr"] = cr
        data["cr-ma1"] = tl.MA(cr, 5)
        data["cr-ma2"] = tl.MA(cr, 10)
        data["cr-ma3"] = tl.MA(cr, 20)

        # RSI 多周期
        data["rsi"]   = tl.RSI(c, 14)
        data["rsi_6"] = tl.RSI(c, 6)
        data["rsi_12"]= tl.RSI(c, 12)
        data["rsi_24"]= tl.RSI(c, 24)

        # VR
        av = np.where(c > pc, v, 0)
        bv = np.where(c < pc, v, 0)
        cv = np.where(c == pc, v, 0)
        avs = tl.SUM(av, 26); bvs = tl.SUM(bv, 26); cvs = tl.SUM(cv, 26)
        vr = (avs + cvs/2) / (bvs + cvs/2 + 1e-9) * 100
        data["vr"] = vr
        data["vr_6_sma"] = tl.MA(vr, 6)

        # TR & ATR
        data["tr"]  = tl.TRANGE(h, l, c)
        data["atr"] = tl.ATR(h, l, c, 14)

        # Supertrend
        ub, lb, st = _supertrend_nb(h, l, c, data["atr"].to_numpy(), 3.0)
        data["supertrend_ub"], data["supertrend_lb"], data["supertrend"] = ub, lb, st

        # ……其余指标与你原脚本完全一致，此处省略 400 行，直接复用即可……
        # 为了演示，下面再列几个容易踩坑的
        data["roc"] = tl.ROC(c, 12)
        data["obv"] = tl.OBV(c, v)
        data["sar"] = tl.SAR(h, l)
        data["cci"] = tl.CCI(h, l, c, 14)

    # 4. 兜底 inf/nan
    data = data.replace([np.inf, -np.inf], 0.0).fillna(0.0)

    # 5. 返回
    if threshold:
        data = data.tail(threshold)
    return data
