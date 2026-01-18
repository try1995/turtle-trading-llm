import os
import requests
import tempfile
import json
import talib as ta
from datetime import datetime, timedelta
import akshare as ak
import pandas as pd
from .base_tool import markdownpdf
from loguru import logger
from typing import get_type_hints, Optional, Any, List, Dict, Annotated


def stock_zh_a_hist(
    symbol: Annotated[str, "股票代码，e.g. 603777"],
    start_date: Annotated[str, "开始日期 %Y%m%d，e.g. 20210301"],
    end_date: Annotated[str, "结束日期 %Y%m%d，e.g. 20210616"],
    period: Annotated[str, "周期，choice of {'daily','weekly','monthly'}，默认 daily"]="daily",
    adjust: Annotated[str, "复权方式，默认不复权；qfq: 前复权；hfq: 后复权,不复权：看表面价格，忽略分红影响。前复权：看近期成本，适合短线。后复权：看真实收益，适合长线。"]="",
):
    """
    描述：沪深京 A 股日频率历史行情

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
    report_res = []
    for index, report_url in enumerate(report_urls.split(",")):
        with tempfile.TemporaryDirectory() as tempdir:
            ret = requests.get(report_url)
            file_path = os.path.join(tempdir, "temp.pdf")
            with open(file_path, 'wb') as f:
                f.write(ret.content)
            try:
                result = markdownpdf(file_path)
            except Exception as e:
                logger.error(e)
                result = "无结果"
            report_res.append(f"第{index+1}家研报解析结果:\n"+result)
    return "\n\n".join(report_res)


def get_indicators(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"],
    data_range: Annotated[int, "时间跨度,建议不低于90天，e.g. 90"] = 90,
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
    df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                            start_date=start_date, end_date=cur_date, adjust="qfq")

    # 2. 列名转英文，talib 只认英文
    df = df.rename(columns={
        "收盘": "close",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "成交量": "volume"
    })

    # 3. 计算常见指标（示例）
    close = df["close"].values
    high  = df["high"].values
    low   = df["low"].values
    vol   = df["volume"].values.astype(float)

    df["MA20"]   = ta.SMA(close, timeperiod=20)
    df["RSI14"]  = ta.RSI(close, timeperiod=14)
    df["MACD"], df["MACDsig"], df["MACDhist"] = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    df["ATR14"]  = ta.ATR(high, low, close, timeperiod=14)
    df["OBV"]    = ta.OBV(close, vol)

    df = df.drop(columns=["close","open","high","low","volume","股票代码", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"])
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


def get_market(code: str) -> str:
    """返回 'sh' / 'sz' / 'bj'"""
    code = code.strip()
    if code.startswith(('6', '9')):          # 6xxxxxx、900xxx
        return 'sh'
    if code.startswith(('0', '3')):          # 0xxxxxx、3xxxxxx
        return 'sz'
    # 其余按北交所处理（8xxxxxx 或 8 位代码）
    return 'bj'

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
    record = record.to_dict("records")[0]
    return json.dumps(record, ensure_ascii=False)


def get_trade_date(start_date="20201212", end_date="20901212"):
    # 交易日历
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
    record = record.to_dict("records")[0]
    return json.dumps(record, ensure_ascii=False)


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
