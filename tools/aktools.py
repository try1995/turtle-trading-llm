import os
import config
import requests
import tempfile
import json
import talib as ta
from datetime import datetime, timedelta
import akshare as ak
import pandas as pd
from .base_tool import markdownpdf, fetch_url_content, get_market, save_func_response, get_func_response
from loguru import logger
from typing import Annotated


def stock_zh_a_hist(
    symbol: Annotated[str, "股票代码，e.g. 603777"],
    start_date: Annotated[str, "开始日期 %Y%m%d，e.g. 20210301"],
    end_date: Annotated[str, "结束日期 %Y%m%d，e.g. 20210616"],
    period: Annotated[str, "周期，choice of {'daily','weekly','monthly'}，默认 daily"]="daily",
    adjust: Annotated[str, "复权方式，默认不复权；qfq: 前复权；hfq: 后复权"]="",
):
    """
    描述：沪深京 A 股日频率历史行情（基于智兔API）

    输出参数-历史行情数据

    名称	类型	描述
    交易时间	object	交易日
    开盘价	float64	开盘价
    收盘价	float64	收盘价
    最高价	float64	最高价
    最低价	float64	最低价
    成交量	int64	注意单位: 手
    成交额	float64	注意单位: 元
    """
    from .zttools import zt_stock_hist_price
    return zt_stock_hist_price(symbol, start_date, end_date)



def stock_research_report_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"],
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
    stock_research_report_em_df = ak.stock_research_report_em(symbol)
    stock_research_report_em_df["日期"] = pd.to_datetime(stock_research_report_em_df["日期"])
    df_filter = stock_research_report_em_df[stock_research_report_em_df["日期"] <= cur_date].head(10)
    # return df_filter
    record = df_filter.astype(str).to_dict("records")
    return json.dumps(record, ensure_ascii=False)


def stock_research_report_markdown(report_urls: Annotated[str, "英文逗号分隔的报告PDF链接， eg.http://1.pdf,http://2.pdf"]):
    """
    返回研报的PDF解析结果，输出示例如下：
    第一家研报解析结果：
    xxx
    
    第二家研报解析结果：
    xxx
    """
    ret = get_func_response(report_urls)
    if ret:
        return ret
    report_res = []
    for index, report_url in enumerate(report_urls.split(",")):
        with tempfile.TemporaryDirectory() as tempdir:
            ret = requests.get(report_url)
            file_path = os.path.join(tempdir, "temp.pdf")
            with open(file_path, 'wb') as f:
                f.write(ret.content)
                result = markdownpdf(file_path)
            report_res.append(f"第{index+1}家研报解析结果:\n"+result)
    save_func_response(report_urls, "\n\n".join(report_res))
    return "\n\n".join(report_res) if report_res else "无研报结果"


def stock_research_report_ex(symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"],):
    """
    返回研报的PDF解析结果，输出示例如下：
    第一家研报解析结果：
    xxx
    
    第二家研报解析结果：
    xxx
    """
    rets = stock_research_report_em(symbol, cur_date)
    urls = []
    for ret in json.loads(rets)[:3]:
        urls.append(ret["报告PDF链接"])
    return stock_research_report_markdown(",".join(urls))
        

# 被智兔接口取代
def get_indicators(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"],
    data_range: Annotated[int, "时间跨度,建议不低于90天，e.g. 90"],
):
    """
    描述：获取指定股票代码的技术分析指标
    
    输出参数-技术分析指标

    名称	类型	描述
    日期	object	交易日
    MA20    float64  20日均线
    RSI14    float64 14日相对强弱指标
    MACD     float64 MACD线
    MACDsig  float64 MACD信号线
    MACDhist   float64 MACD柱状图
    ATR14   float64  14日真实波动幅度均值
    OBV     float64  能量潮
    """
    # end_date   = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.strptime(cur_date, '%Y%m%d') - timedelta(days=data_range)).strftime("%Y%m%d")
    # 改用智兔API获取历史行情
    from .zttools import _zt_get, get_market
    symbol_market = symbol + "." + get_market(symbol).upper()
    url = f"https://api.zhituapi.com/hs/history/{symbol_market}/d/n?token=__TOKEN__&st={start_date}&et={cur_date}"
    response = _zt_get(url)
    df = pd.DataFrame(response.json())
    df = df.drop(columns=['sf', "pc"], errors='ignore')

    # 列名映射（zttools原始列: t=时间, o=开盘, h=最高, l=最低, c=收盘, v=成交量）
    df = df.rename(columns={
        "c": "close",
        "o": "open",
        "h": "high",
        "l": "low",
        "v": "volume"
    })

    # 转数值类型用于TA-Lib计算
    for col in ["close", "open", "high", "low", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["close", "open", "high", "low"])

    # 3. 计算常见指标（示例）
    close = df["close"].values
    high  = df["high"].values
    low   = df["low"].values
    vol   = df["volume"].values

    df["MA20"]   = ta.SMA(close, timeperiod=20)
    df["RSI14"]  = ta.RSI(close, timeperiod=14)
    df["MACD"], df["MACDsig"], df["MACDhist"] = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    df["ATR14"]  = ta.ATR(high, low, close, timeperiod=14)
    df["OBV"]    = ta.OBV(close, vol)

    df = df.drop(columns=["close","open","high","low","volume"], errors="ignore")
    # 保留交易时间列
    if "t" in df.columns:
        df = df.rename(columns={"t": "日期"})
    record = df.astype(str).to_dict("records")
    return json.dumps(record, ensure_ascii=False)


def stock_yjbb_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"]
):
    """
    描述: 东方财富-数据中心-年报季报-业绩报表

    获取指定 date 的业绩报告数据
    
    输出参数

    名称	类型	描述
    序号	int64	-
    股票代码	object	-
    股票简称	object	-
    每股收益	float64	注意单位: 元
    营业总收入-营业总收入	float64	注意单位: 元
    营业总收入-同比增长	float64	注意单位: %
    营业总收入-季度环比增长	float64	注意单位: %
    净利润-净利润	float64	注意单位: 元
    净利润-同比增长	float64	注意单位: %
    净利润-季度环比增长	float64	注意单位: %
    每股净资产	float64	注意单位: 元
    净资产收益率	float64	注意单位: %
    每股经营现金流量	float64	注意单位: 元
    销售毛利率	float64	注意单位: %
    所处行业	object	-
    最新公告日期	object	-
    """
    stock_yjbb_em_df = ak.stock_yjbb_em(date=cur_date)
    record = stock_yjbb_em_df[stock_yjbb_em_df["股票代码"]==symbol].astype(str).to_dict("records")
    return json.dumps(record, ensure_ascii=False)



def stock_individual_fund_flow(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"]
):
    """
    描述: 获取指定股票的交易日的资金流数据，若交易日未结束，则自动获取到上一个交易日数据

    输出参数

    名称	类型	描述
    日期	object	-
    收盘价	float64	-
    涨跌幅	float64	注意单位: %
    主力净流入-净额	float64	-
    主力净流入-净占比	float64	注意单位: %
    超大单净流入-净额	float64	-
    超大单净流入-净占比	float64	注意单位: %
    大单净流入-净额	float64	-
    大单净流入-净占比	float64	注意单位: %
    中单净流入-净额	float64	-
    中单净流入-净占比	float64	注意单位: %
    小单净流入-净额	float64	-
    小单净流入-净占比	float64	注意单位: %

    """
    cur_date = datetime.strptime(cur_date, "%Y%m%d").strftime("%Y-%m-%d")
    stock_individual_fund_flow_df = ak.stock_individual_fund_flow(stock=symbol, market=get_market(symbol))
    stock_individual_fund_flow_df = stock_individual_fund_flow_df.astype(str)
    record = stock_individual_fund_flow_df[stock_individual_fund_flow_df["日期"]==cur_date]
    if record.empty:
        # 1.说明当天交易日没结束，需要获取的是前一个交易日的数据
        # 2.运行在一个非交易日时间，取最新的交易日的数据
        record = stock_individual_fund_flow_df.tail(1)
    if record.empty:
        return "{}"
    record = record.to_dict("records")[0]
    return json.dumps(record, ensure_ascii=False)


def get_trade_date(start_date="20201212", end_date="20901212", use_cache=True):
    # 交易日历,这个接口最好缓存，否则频繁报错 qinglong/update_trade_date.py
    if use_cache:
        with open(os.path.join(config.cache_dir, "tradeData"), "r") as f:
            data = json.load(f)
        trade_df = pd.DataFrame({'date': data})
        trade_df['trade_date'] = pd.to_datetime(trade_df['date'], format='%Y%m%d', errors='coerce')
    else:
        trade_df = ak.tool_trade_date_hist_sina()
        trade_df["trade_date"] = pd.to_datetime(trade_df["trade_date"], errors='coerce')
    ret = trade_df[(trade_df["trade_date"] >= start_date) & (trade_df["trade_date"] <= end_date)]
    return ret["trade_date"].dt.strftime('%Y%m%d').to_list()


def stock_value_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"]
):
    """
    描述: 获取指定交易日的股票估值分析，若交易日未结束，则自动获取到上一个交易日数据

    输出参数

    名称	类型	描述
    数据日期	object	-
    当日收盘价	float64	注意单位: 元
    当日涨跌幅	float64	注意单位: %
    总市值	float64	注意单位: 元
    流通市值	float64	注意单位: 元
    总股本	float64	注意单位: 股
    流通股本	float64	-
    PE(TTM)	float64	-
    PE(静)	float64	-
    市净率	float64	-
    PEG值	float64	-
    市现率	float64	-
    市销率	float64	-
    """
    cur_date = datetime.strptime(cur_date, "%Y%m%d").strftime("%Y-%m-%d")
    df_val = ak.stock_value_em(symbol).astype(str)
    record = df_val[df_val["数据日期"]==cur_date]
    if record.empty:
        # 1.说明当天交易日没结束，需要获取的是前一个交易日的数据
        # 2.运行在一个非交易日时间，取最新的交易日的数据
        record = df_val.tail(1)
    if record.empty:
        return "{}"
    record = record.to_dict("records")[0]
    return json.dumps(record, ensure_ascii=False)

# 经常出问题，使用智兔接口替换zt_stock_info
def stock_individual_info_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
):
    """
    描述: 查询股票信息

    输出参数

    名称            类型      描述
    最新            float64   当日收盘价，单位：元
    股票代码        object    -
    股票简称        object    -
    总股本          float64   单位：股
    流通股          float64   流通股本
    总市值          float64   单位：元
    流通市值        float64   单位：元
    行业            object    -
    上市时间        object    数据日期
    """
    stock_individual_info_em_df = ak.stock_individual_info_em(symbol)
    record = stock_individual_info_em_df.set_index('item')['value'].to_dict()
    return json.dumps(record, ensure_ascii=False)


def stock_individual_basic_info_xq(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
):
    """
    描述: 查询股票信息

    输出参数

    名称            类型      描述
    最新            float64   当日收盘价，单位：元
    股票代码        object    -
    股票简称        object    -
    总股本          float64   单位：股
    流通股          float64   流通股本
    总市值          float64   单位：元
    流通市值        float64   单位：元
    行业            object    -
    上市时间        object    数据日期
    """
    stock_individual_info_em_df = ak.stock_individual_basic_info_xq(get_market(symbol).upper()+symbol)
    record = stock_individual_info_em_df.set_index('item')['value'].to_dict()
    return json.dumps(record, ensure_ascii=False)

def stock_news_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
):
    """
    描述: 查询指定个股的新闻资讯数据
    
    输出参数

    名称	类型	描述
    关键词	object	-
    新闻标题	object	-
    新闻内容	object	-
    发布时间	object	-
    文章来源	object	-
    """
    stock_news_em_df = ak.stock_news_em(symbol).drop(columns=["新闻链接"]).sort_values(by='发布时间', ascending=False)
    record = stock_news_em_df.to_dict("records")
    return json.dumps(record, ensure_ascii=False)


def stock_financial_report_sina(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
):
    """
    描述: 财务报表-三大报表
    
    三种报表类型：资产负债表, 利润表, 现金流量表
    
    输出参数

    名称	类型	描述
    报告日	object	报告日期
    流动资产	object	-
    ...	object	-
    类型	object	-
    更新日期	object	-
    """

    market = get_market(symbol)
    balance_sheet1 = ak.stock_financial_report_sina(stock=market+symbol, symbol="资产负债表").to_dict("records")[0]
    balance_sheet2 = ak.stock_financial_report_sina(stock=market+symbol, symbol="利润表").to_dict("records")[0]
    balance_sheet3 = ak.stock_financial_report_sina(stock=market+symbol, symbol="现金流量表").to_dict("records")[0]
    record = {
        "资产负债表": balance_sheet1,
        "利润表": balance_sheet2,
        "现金流量表": balance_sheet3
    }
    return json.dumps(record, ensure_ascii=False)


def stock_board_industry_summary_ths(
    symbol: Annotated[str, "股票代码，e.g. 000001"]
):
    """
    描述: 同行比较-查询指定股票所在行业涨跌信息

    输出参数

    名称	类型	描述
    板块	object	-
    涨跌幅	object	注意单位: %
    总成交量	float64	注意单位: 万手
    总成交额	float64	注意单位: 亿元
    净流入	float64	注意单位: 亿元
    上涨家数	float64	-
    下跌家数	float64	-
    均价	float64	-
    领涨股	float64	-
    领涨股-最新价	object	-
    领涨股-涨跌幅	object	注意单位: %
    """
    industry = json.loads(stock_individual_info_em(symbol))["行业"]
    stock_board_industry_summary_ths_df = ak.stock_board_industry_summary_ths().drop(columns=["序号"])
    record = stock_board_industry_summary_ths_df[stock_board_industry_summary_ths_df["板块"]==industry].to_dict("records")[0]
    return json.dumps(record, ensure_ascii=False)


def stock_zh_growth_comparison_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"]
):
    """
    描述: 同行比较-成长性比较
    
    输出参数

    名称	类型	描述
    代码	object	-
    简称	object	-
    基本每股收益增长率-3年复合	float64	-
    基本每股收益增长率-24A	float64	-
    基本每股收益增长率-TTM	float64	-
    基本每股收益增长率-25E	float64	-
    基本每股收益增长率-26E	float64	-
    基本每股收益增长率-27E	float64	-
    营业收入增长率-3年复合	float64	-
    营业收入增长率-24A	float64	-
    营业收入增长率-TTM	float64	-
    营业收入增长率-25E	float64	-
    营业收入增长率-26E	float64	-
    营业收入增长率-27E	float64	-
    净利润增长率-3年复合	float64	-
    净利润增长率-24A	float64	-
    净利润增长率-TTM	float64	-
    净利润增长率-25E	float64	-
    净利润增长率-26E	float64	-
    净利润增长率-27E	float64	-
    基本每股收益增长率-3年复合排名	float64	-
    """
    stock_zh_growth_comparison_em_df = ak.stock_zh_growth_comparison_em(symbol=get_market(symbol).upper()+symbol)
    record = stock_zh_growth_comparison_em_df.to_dict("records")
    return json.dumps(record, ensure_ascii=False)


def stock_zh_valuation_comparison_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"]
):
    """
    描述: 同行比较-估值比较
    
    输出参数

    名称	类型	描述
    排名	object	-
    代码	object	-
    简称	object	-
    PEG	float64	-
    市盈率-24A	float64	-
    市盈率-TTM	float64	-
    市盈率-25E	float64	-
    市盈率-26E	float64	-
    市盈率-27E	float64	-
    市销率-24A	float64	-
    市销率-TTM	float64	-
    市销率-25E	float64	-
    市销率-26E	float64	-
    市销率-27E	float64	-
    市净率-24A	float64	-
    市净率-MRQ	float64	-
    市现率1-24A	float64	-
    市现率1-TTM	float64	-
    市现率2-24A	float64	-
    市现率2-TTM	float64	-
    EV/EBITDA-24A	float64	-
    """
    stock_zh_valuation_comparison_em_df = ak.stock_zh_valuation_comparison_em(symbol=get_market(symbol).upper()+symbol)
    record = stock_zh_valuation_comparison_em_df.to_dict("records")
    return json.dumps(record, ensure_ascii=False)

def stock_zh_scale_comparison_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"]
):
    """
    描述: 同行比较-公司规模
    
    输出参数

    名称	类型	描述
    代码	object	-
    简称	object	-
    总市值	float64	-
    总市值排名	int64	-
    流通市值	float64	-
    流通市值排名	int64	-
    营业收入	float64	-
    营业收入排名	int64	-
    净利润	float64	-
    净利润排名	int64	-
    """
    stock_zh_scale_comparison_em_df = ak.stock_zh_scale_comparison_em(symbol=get_market(symbol).upper()+symbol)
    record = stock_zh_scale_comparison_em_df.to_dict("records")
    return json.dumps(record, ensure_ascii=False)

# -----------------------------------快讯------------------------------------------------
def stock_info_cjzc_em():
    # 方财富财经早餐，只取每天的一条资讯
    stock_info_cjzc_em_df = ak.stock_info_cjzc_em()
    url = stock_info_cjzc_em_df.to_dict("records")[0]["链接"]
    content = fetch_url_content(url)
    return url, content

def stock_info_global_cls():
    # 财联社-电报-重要
    stock_info_global_cls_df = ak.stock_info_global_ths().drop(columns=["链接","发布时间"])
    record = stock_info_global_cls_df.to_dict("records")
    return json.dumps(record, ensure_ascii=False)


# =============================================================================
# InvestmentAgent 投资框架计算工具
# =============================================================================

def _fetch_ohlcv(symbol: str, cur_date: str, calendar_days: int):
    """
    内部辅助函数：获取OHLCV历史数据并重命名为英文列，返回清理后的DataFrame。
    若获取失败则返回空DataFrame。
    """
    try:
        start_date = (datetime.strptime(cur_date, '%Y%m%d') - timedelta(days=calendar_days)).strftime("%Y%m%d")
        # 改用智兔API获取历史行情
        from .zttools import _zt_get, get_market
        symbol_market = symbol + "." + get_market(symbol).upper()
        url = f"https://api.zhituapi.com/hs/history/{symbol_market}/d/n?token=__TOKEN__&st={start_date}&et={cur_date}"
        response = _zt_get(url)
        data = response.json()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        # 删除多余列
        df = df.drop(columns=['sf', "pc"], errors='ignore')
        # 列映射: t=交易时间, o=开盘, h=最高, l=最低, c=收盘, v=成交量, a=成交额
        df = df.rename(columns={
            "t": "date",
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
            "a": "amount",
        })
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        df = df.dropna(subset=["close", "high", "low"])
        return df
    except Exception as e:
        logger.error(f"_fetch_ohlcv failed for {symbol}: {e}")
        return pd.DataFrame()


def stock_donchian_channel(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"],
):
    """
    描述：计算海龟交易法则的唐奇安通道(Donchian Channel)指标

    输出参数
    名称          类型      描述
    计算日期      object    当前计算日期
    最新收盘价    float64   单位：元
    通道上轨      float64   20日最高价，单位：元
    通道下轨      float64   20日最低价，单位：元
    通道中轨      float64   (上轨+下轨)/2，单位：元
    55日最低价    float64   用于中线止损判断，单位：元
    10日最低价    float64   用于短线离场判断，单位：元
    突破20日高点  str       是/否
    跌破10日低点  str       是/否
    跌破55日低点  str       是/否
    价格在通道内位置 float64  百分比，单位：%
    """
    df = _fetch_ohlcv(symbol, cur_date, 120)
    if df.empty or len(df) < 20:
        return json.dumps({"提示": "数据不足，无法计算唐奇安通道"}, ensure_ascii=False)

    close = df["close"].values
    high = df["high"].values
    low = df["low"].values

    latest_close = round(float(close[-1]), 2)

    # 20日通道
    high_20 = round(float(pd.Series(high).tail(20).max()), 2)
    low_20 = round(float(pd.Series(low).tail(20).min()), 2)
    mid_20 = round((high_20 + low_20) / 2, 2)

    # 止损参考位
    low_55 = round(float(pd.Series(low).tail(min(55, len(df))).min()), 2)
    low_10 = round(float(pd.Series(low).tail(min(10, len(df))).min()), 2)

    # 信号判断
    breakout_up = "是" if latest_close > high_20 else "否"
    breakdown_10 = "是" if latest_close < low_10 else "否"
    breakdown_55 = "是" if latest_close < low_55 else "否"

    # 通道内位置
    if high_20 != low_20:
        position_pct = round((latest_close - low_20) / (high_20 - low_20) * 100, 2)
    else:
        position_pct = 50.0

    record = {
        "计算日期": cur_date,
        "最新收盘价": latest_close,
        "通道上轨(20日高点)": high_20,
        "通道下轨(20日低点)": low_20,
        "通道中轨": mid_20,
        "55日最低价(中线止损)": low_55,
        "10日最低价(短线离场)": low_10,
        "突破20日高点": breakout_up,
        "跌破10日低点": breakdown_10,
        "跌破55日低点": breakdown_55,
        "价格在通道内位置(%)": position_pct,
    }
    return json.dumps(record, ensure_ascii=False)


def stock_atr_value(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"],
):
    """
    描述：计算ATR(平均真实波幅)及相关止损位，用于海龟交易和风险控制

    输出参数
    名称          类型      描述
    计算日期      object    当前计算日期
    最新收盘价    float64   单位：元
    ATR14         float64   14日平均真实波幅
    1倍ATR止损位  float64   收盘价 - 1*ATR14，单位：元
    1.5倍ATR止损位 float64  收盘价 - 1.5*ATR14，单位：元
    2倍ATR止损位  float64   收盘价 - 2*ATR14，单位：元
    波动率        float64   ATR/收盘价*100，单位：%
    """
    df = _fetch_ohlcv(symbol, cur_date, 60)
    if df.empty or len(df) < 15:
        return json.dumps({"提示": "数据不足，无法计算ATR"}, ensure_ascii=False)

    close = df["close"].values
    high = df["high"].values
    low = df["low"].values

    atr = ta.ATR(high, low, close, timeperiod=14)
    atr14 = round(float(atr[-1]), 2)
    latest_close = round(float(close[-1]), 2)

    record = {
        "计算日期": cur_date,
        "最新收盘价": latest_close,
        "ATR14": atr14,
        "1倍ATR止损位": round(latest_close - atr14, 2),
        "1.5倍ATR止损位": round(latest_close - atr14 * 1.5, 2),
        "2倍ATR止损位": round(latest_close - atr14 * 2, 2),
        "波动率(%)": round(atr14 / latest_close * 100, 2) if latest_close else 0,
    }
    return json.dumps(record, ensure_ascii=False)


def stock_trend_template(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"],
):
    """
    描述：执行马克·米勒维尼SEPA趋势模板检查，逐条判断是否通过

    输出参数
    名称                  类型      描述
    计算日期              object    当前计算日期
    最新收盘价            float64   单位：元
    MA150                 float64   150日均线，数据不足时为NaN
    MA200                 float64   200日均线，数据不足时为NaN
    52周最高价            float64   单位：元
    52周最低价            float64   单位：元
    规则1_价格高于MA150   str       是/否/数据不足
    规则2_价格高于MA200   str       是/否/数据不足
    规则3_MA150大于MA200  str       是/否/数据不足
    规则4_MA150趋势向上   str       是/否/数据不足
    规则5_距52周高点      float64   回撤百分比
    规则5_通过            str       是/否（回撤<25%视为通过）
    规则6_高于52周低点    float64   涨幅百分比
    规则6_通过            str       是/否（涨幅>30%视为通过）
    总通过数              int       通过数量（满分6）
    """
    df = _fetch_ohlcv(symbol, cur_date, 300)
    if df.empty:
        return json.dumps({"提示": "数据不足，无法执行SEPA趋势模板检查"}, ensure_ascii=False)

    close = df["close"].values

    latest_close = round(float(close[-1]), 2)
    high_52w = round(float(pd.Series(close).max()), 2)
    low_52w = round(float(pd.Series(close).min()), 2)

    # 均线计算
    def calc_ma(data, period):
        if len(data) < period:
            return None
        ma = ta.SMA(data, timeperiod=period)
        val = ma[-1]
        return round(float(val), 2) if not (val is None or val != val) else None  # NaN check

    ma150 = calc_ma(close, 150)
    ma200 = calc_ma(close, 200)

    # 规则评估
    pass_count = 0

    def check_rule(condition_str, pass_val):
        if pass_val is None:
            return "数据不足", False
        return ("是" if condition_str else "否"), condition_str

    # 规则1
    r1_str, r1_pass = check_rule(ma150 is not None and latest_close > ma150, ma150)
    if r1_pass:
        pass_count += 1

    # 规则2
    r2_str, r2_pass = check_rule(ma200 is not None and latest_close > ma200, ma200)
    if r2_pass:
        pass_count += 1

    # 规则3
    if ma150 is not None and ma200 is not None:
        r3_pass = ma150 > ma200
        r3_str = "是" if r3_pass else "否"
        if r3_pass:
            pass_count += 1
    else:
        r3_str = "数据不足"

    # 规则4: MA150 近1个月趋势向上（比较一个月前）
    if ma150 is not None and len(close) >= 170:
        ma150_1m_data = close[:-22] if len(close) >= 172 else close[:len(close)-22]
        if len(ma150_1m_data) >= 150:
            ma150_1m_ago = ta.SMA(ma150_1m_data, timeperiod=150)[-1]
            if ma150_1m_ago is not None and ma150_1m_ago == ma150_1m_ago:
                r4_pass = ma150 > float(ma150_1m_ago)
                r4_str = "是" if r4_pass else "否"
                if r4_pass:
                    pass_count += 1
            else:
                r4_str = "数据不足"
        else:
            r4_str = "数据不足"
    else:
        r4_str = "数据不足"

    # 规则5: 距52周高点回撤 < 25%
    if high_52w > 0:
        pct_from_high = round((high_52w - latest_close) / high_52w * 100, 2)
        r5_pass = pct_from_high < 25
        r5_str = "是" if r5_pass else "否"
        if r5_pass:
            pass_count += 1
    else:
        pct_from_high = 0
        r5_str = "数据不足"

    # 规则6: 高于52周低点 > 30%
    if low_52w > 0:
        pct_above_low = round((latest_close - low_52w) / low_52w * 100, 2)
        r6_pass = pct_above_low > 30
        r6_str = "是" if r6_pass else "否"
        if r6_pass:
            pass_count += 1
    else:
        pct_above_low = 0
        r6_str = "数据不足"

    record = {
        "计算日期": cur_date,
        "最新收盘价": latest_close,
        "MA150": ma150 if ma150 else "数据不足",
        "MA200": ma200 if ma200 else "数据不足",
        "52周最高价": high_52w,
        "52周最低价": low_52w,
        "规则1_价格高于MA150": r1_str,
        "规则2_价格高于MA200": r2_str,
        "规则3_MA150大于MA200": r3_str,
        "规则4_MA150趋势向上": r4_str,
        "规则5_距52周高点回撤(%)": pct_from_high,
        "规则5_通过(回撤<25%)": r5_str,
        "规则6_高于52周低点涨幅(%)": pct_above_low,
        "规则6_通过(涨幅>30%)": r6_str,
        "总通过数": pass_count,
    }
    return json.dumps(record, ensure_ascii=False)


def stock_volume_breakout(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"],
):
    """
    描述：检测成交量是否出现突破（放量），对比50日均量判断资金参与度

    输出参数
    名称              类型      描述
    计算日期          object    当前计算日期
    最新成交量        int64     单位：手
    50日均成交量      float64   单位：手
    量比              float64   最新成交量/50日均量
    是否放量          str       是/否（量比>1.5视为放量）
    近5日平均量比    float64   近5日量比均值
    量能趋势          str       放量/缩量/正常
    """
    df = _fetch_ohlcv(symbol, cur_date, 80)
    if df.empty or len(df) < 10:
        return json.dumps({"提示": "数据不足，无法分析成交量"}, ensure_ascii=False)

    vol = df["volume"].values

    vol_latest = int(vol[-1])
    if len(vol) >= 51:
        vol_50_avg = round(float(pd.Series(vol[-51:-1]).mean()), 0)
        vol_ratio = round(vol_latest / vol_50_avg, 2) if vol_50_avg > 0 else 1.0
    else:
        vol_50_avg = round(float(pd.Series(vol[:-1]).mean()), 0) if len(vol) > 1 else vol_latest
        vol_ratio = round(vol_latest / vol_50_avg, 2) if vol_50_avg > 0 else 1.0

    is_breakout = "是" if vol_ratio > 1.5 else "否"

    # 近5日量比均值
    ratios_5d = []
    for i in range(max(0, len(vol) - 5), len(vol)):
        if i >= 51:
            avg = pd.Series(vol[i - 50:i]).mean()
        elif i > 0:
            avg = pd.Series(vol[:i]).mean()
        else:
            continue
        ratios_5d.append(vol[i] / avg if avg > 0 else 1.0)
    avg_ratio_5d = round(float(pd.Series(ratios_5d).mean()), 2) if ratios_5d else vol_ratio

    if vol_ratio > 1.5:
        trend = "放量"
    elif vol_ratio < 0.7:
        trend = "缩量"
    else:
        trend = "正常"

    record = {
        "计算日期": cur_date,
        "最新成交量(手)": vol_latest,
        "50日均成交量(手)": vol_50_avg,
        "量比": vol_ratio,
        "是否放量(>1.5)": is_breakout,
        "近5日平均量比": avg_ratio_5d,
        "量能趋势": trend,
    }
    return json.dumps(record, ensure_ascii=False)


def stock_risk_metrics(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"],
):
    """
    描述：综合风险与估值指标，涵盖格雷厄姆价值检查、财务健康度和风险控制关键数据

    输出参数
    名称                    类型      描述
    计算日期                object    当前计算日期
    最新收盘价              float64   单位：元
    PE_TTM                  str       市盈率(TTM)，数据缺失时显示"数据不足"
    PB                      str       市净率，数据缺失时显示"数据不足"
    格雷厄姆数              str       PE*PB，<22.5为价值区间
    格雷厄姆检查            str       通过/未通过/数据不足
    PEG                     str       PEG值
    净资产收益率ROE         str       单位：%
    毛利率                  str       单位：%
    每股收益                str       单位：元
    每股净资产              str       单位：元
    每股经营现金流          str       单位：元
    净利润同比增长          str       单位：%
    营业总收入同比增长      str       单位：%
    总市值                  str       单位：元
    流通市值                str       单位：元
    风险收益比评估          str       有利/一般/不利/数据不足
    """
    result = {"计算日期": cur_date}

    # 获取估值数据
    try:
        val_json = stock_value_em(symbol, cur_date)
        val_data = json.loads(val_json)
    except Exception:
        val_data = {}

    # 获取业绩数据（利润率/ROE）
    try:
        yjbb_json = stock_yjbb_em(symbol, cur_date)
        yjbb_list = json.loads(yjbb_json)
        yjbb_data = yjbb_list[0] if yjbb_list else {}
    except Exception:
        yjbb_data = {}

    # --- 估值指标 ---
    close_price = val_data.get("当日收盘价", "数据不足")
    result["最新收盘价"] = close_price

    pe_str = val_data.get("PE(TTM)", "数据不足")
    pb_str = val_data.get("市净率", "数据不足")
    peg_str = val_data.get("PEG值", "数据不足")
    total_mv = val_data.get("总市值", "数据不足")
    float_mv = val_data.get("流通市值", "数据不足")

    result["PE_TTM"] = pe_str
    result["PB"] = pb_str
    result["PEG"] = peg_str

    # 格雷厄姆数
    try:
        pe_val = float(pe_str)
        pb_val = float(pb_str)
        graham_num = round(pe_val * pb_val, 2)
        result["格雷厄姆数"] = graham_num
        result["格雷厄姆检查"] = "通过" if (graham_num < 22.5 and pe_val < 25) else "未通过"
    except (ValueError, TypeError):
        result["格雷厄姆数"] = "数据不足"
        result["格雷厄姆检查"] = "数据不足"

    # --- 财务健康指标 ---
    result["净资产收益率ROE"] = yjbb_data.get("净资产收益率", "数据不足")
    result["毛利率"] = yjbb_data.get("销售毛利率", "数据不足")
    result["每股收益"] = yjbb_data.get("每股收益", "数据不足")
    result["每股净资产"] = yjbb_data.get("每股净资产", "数据不足")
    result["每股经营现金流"] = yjbb_data.get("每股经营现金流量", "数据不足")
    result["净利润同比增长"] = yjbb_data.get("净利润-同比增长", "数据不足")
    result["营业总收入同比增长"] = yjbb_data.get("营业总收入-同比增长", "数据不足")
    result["总市值"] = total_mv
    result["流通市值"] = float_mv

    # --- 风险收益比评估 ---
    try:
        roe = float(yjbb_data.get("净资产收益率", 0))
        net_growth = float(yjbb_data.get("净利润-同比增长", 0))
        peg = float(peg_str)
        gross_margin = float(yjbb_data.get("销售毛利率", 0))

        if roe > 15 and net_growth > 0 and peg < 1.5 and gross_margin > 20:
            result["风险收益比评估"] = "有利"
        elif roe > 8 and net_growth > -20 and gross_margin > 10:
            result["风险收益比评估"] = "一般"
        else:
            result["风险收益比评估"] = "不利"
    except (ValueError, TypeError):
        result["风险收益比评估"] = "数据不足"

    return json.dumps(result, ensure_ascii=False)


def stock_zt_pool_dtgc_em(
    date: Annotated[str, "交易日期，格式%%Y%%m%%d，e.g. 20241011"]
):
    """
    描述：东方财富网-行情中心-涨停板行情-跌停股池。获取指定日期的跌停股票列表，按封单资金升序。该接口只能获取最近30个交易日的数据。

    输出参数-跌停股池数据

    名称        类型      描述
    序号        int64     -
    代码        object    -
    名称        object    -
    涨跌幅      float64   单位: %
    最新价      float64   -
    成交额      int64     单位: 元
    流通市值    float64   -
    总市值      float64   -
    动态市盈率   float64   -
    换手率      float64   单位: %
    封单资金    int64     -
    最后封板时间  object   格式: HH:mm:ss
    板上成交额   int64     -
    连续跌停    int64     -
    开板次数    int64     -
    所属行业    object    -
    """
    df = ak.stock_zt_pool_dtgc_em(date=date)
    df = df.astype(str)
    record = df.to_dict("records")
    return json.dumps(record, ensure_ascii=False)