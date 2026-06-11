"""
LangChain-compatible tool wrappers for the existing tool functions.

Wraps functions from aktools.py, zttools.py, search.py, and base_tool.py
with the @tool decorator for use with LangChain ChatOpenAI.bind_tools().

Tool groups per agent:
- dataAgent: zt_stock_hist_price, zt_stock_latest_price, zt_stock_info,
  zt_stock_kdj, zt_stock_boll, zt_stock_ma, zt_stock_macd,
  stock_individual_fund_flow, stock_board_industry_summary_ths,
  stock_financial_report_sina, stock_zh_growth_comparison_em,
  stock_zh_valuation_comparison_em, stock_zh_scale_comparison_em, stock_value_em
- reportAgent: stock_research_report_ex
- publicOptionAgent: stock_news_em, symbol_tavily_search
- vlAgent: zt_stock_latest_price, zt_stock_hist_price
- investmentAgent: get_agent_res
"""
from langchain_core.tools import tool
from typing import Annotated
from .aktools import *
from .zttools import *
from .search import symbol_tavily_search
from .base_tool import get_agent_res

# =============================================================================
# DataAgent tools (14 functions)
# =============================================================================

@tool
def lc_zt_stock_hist_price(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    start_date: Annotated[str, "开始日期，格式：%Y%m%d，e.g. 20230101"],
    end_date: Annotated[str, "结束日期，格式：%Y%m%d，e.g. 20240101"],
    period: Annotated[str, "k线类型：ticK(1分钟线)、60(60分钟线)、d(日线)、w(周线)、m(月线)"] = "d",
    fq: Annotated[str, "复权类型：0(不复权)、1(前复权)、2(后复权)"] = "1",
) -> str:
    """获取股票的历史数据，返回包含日期、开盘价、收盘价、最高价、最低价及其对应均线的历史数据。"""
    return zt_stock_hist_price(symbol, start_date, end_date)


@tool
def lc_zt_stock_latest_price(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
) -> str:
    """获取股票的最新5分钟级别的数据，返回包含日期、开盘价、收盘价、最高价、最低价及其对应均线的实时数据。"""
    return zt_stock_latest_price(symbol)


@tool
def lc_zt_stock_info(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
) -> str:
    """获取股票的详细信息，包括总市值、流通市值、上市时间、涨停价、跌停价、是否停牌等。"""
    return zt_stock_info(symbol)


@tool
def lc_zt_stock_kdj(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    start_date: Annotated[str, "开始日期，格式：%Y%m%d，e.g. 20230101"],
    end_date: Annotated[str, "结束日期，格式：%Y%m%d，e.g. 20240101"],
    period: Annotated[str, "k线周期类型：d(日线)、w(周线)、m(月线)"] = "d",
) -> str:
    """获取股票的KDJ指标数据，KDJ用于判断股价的超买超卖状态，K线上穿D线视为买入信号，K线下穿D线视为卖出信号。"""
    return zt_stock_kdj(symbol, start_date, end_date)


@tool
def lc_zt_stock_boll(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    start_date: Annotated[str, "开始日期，格式：%Y%m%d，e.g. 20230101"],
    end_date: Annotated[str, "结束日期，格式：%Y%m%d，e.g. 20240101"],
    period: Annotated[str, "k线周期类型：d(日线)、w(周线)、m(月线)"] = "d",
) -> str:
    """获取股票的布林带（BOLL）指标数据，BOLL用于判断股价的波动范围和趋势强度，股价触及上轨可能是卖出信号，触及下轨可能是买入信号。"""
    return zt_stock_boll(symbol, start_date, end_date)


@tool
def lc_zt_stock_ma(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    start_date: Annotated[str, "开始日期，格式：%Y%m%d，e.g. 20230101"],
    end_date: Annotated[str, "结束日期，格式：%Y%m%d，e.g. 20240101"],
    period: Annotated[str, "k线周期类型：d(日线)、w(周线)、m(月线)"] = "d",
) -> str:
    """获取股票的均线(MA)数据，包含MA5、MA10、MA20、MA30、MA60、MA120、MA250等多条均线，用于判断股票趋势和支撑压力位。"""
    return zt_stock_ma(symbol, start_date, end_date)


@tool
def lc_zt_stock_macd(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    start_date: Annotated[str, "开始日期，格式：%Y%m%d，e.g. 20230101"],
    end_date: Annotated[str, "结束日期，格式：%Y%m%d，e.g. 20240101"],
    period: Annotated[str, "k线周期类型：d(日线)、w(周线)、m(月线)"] = "d",
) -> str:
    """获取股票的MACD指标数据，MACD用于判断股票的趋势和买卖时机，DIF上穿DEA视为买入信号，DIF下穿DEA视为卖出信号。"""
    return zt_stock_macd(symbol, start_date, end_date)


@tool
def lc_stock_individual_fund_flow(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
) -> str:
    """获取个股资金流向数据，包括主力净流入、大单净流入、中单净流入、小单净流入，用于判断资金进出情况。"""
    return stock_individual_fund_flow(symbol)


@tool
def lc_stock_board_industry_summary_ths(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
) -> str:
    """获取股票所属行业板块的概要信息，包括板块涨跌幅、板块内个股排名等。"""
    return stock_board_industry_summary_ths(symbol)


@tool
def lc_stock_financial_report_sina(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
) -> str:
    """获取新浪财经的财务报告数据，包含资产负债表、利润表、现金流量表的历年数据。"""
    return stock_financial_report_sina(symbol)


@tool
def lc_stock_zh_growth_comparison_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
) -> str:
    """获取股票的成长性对比数据，包括营收增长率、净利润增长率、毛利率增长率等，与同行业公司对比。"""
    return stock_zh_growth_comparison_em(symbol)


@tool
def lc_stock_zh_valuation_comparison_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
) -> str:
    """获取股票的估值对比数据，包括市盈率(PE)、市净率(PB)、市销率(PS)等，与同行业公司对比。"""
    return stock_zh_valuation_comparison_em(symbol)


@tool
def lc_stock_zh_scale_comparison_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
) -> str:
    """获取股票的规模对比数据，包括总市值、流通市值、营业收入、净利润等，与同行业公司对比。"""
    return stock_zh_scale_comparison_em(symbol)


@tool
def lc_stock_value_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
) -> str:
    """获取股票的估值指标数据，包括市盈率(PE)、市净率(PB)、PEG、股息率等关键估值指标。"""
    return stock_value_em(symbol)


# =============================================================================
# ReportAgent tools (1 function)
# =============================================================================

@tool
def lc_stock_research_report_ex(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
) -> str:
    """搜索并获取个股的最新一期研报内容，用于分析专业机构对个股的观点和预测。"""
    return stock_research_report_ex(symbol)


# =============================================================================
# PublicOptionAgent tools (2 functions)
# =============================================================================

@tool
def lc_stock_news_em(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    limit: Annotated[int, "获取的新闻数量上限，默认100"] = 100,
) -> str:
    """获取个股相关新闻信息，包括新闻标题、内容摘要、发布时间等，用于舆情分析。"""
    return stock_news_em(symbol)


@tool
def lc_symbol_tavily_search(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    symbol_name: Annotated[str, "股票名称，e.g. 中国太保"],
) -> str:
    """搜索股票相关的网络舆情信息，包括雪球、股吧等平台的讨论内容，用于了解市场情绪和舆情热度。"""
    return symbol_tavily_search(symbol, symbol_name)


# =============================================================================
# VlAgent tools (2 functions)
# =============================================================================

# VL agent uses the same lc_zt_stock_latest_price and lc_zt_stock_hist_price
# defined above. Reuse them.


# =============================================================================
# InvestmentAgent tools (1 function)
# =============================================================================

@tool
def lc_get_agent_res(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"],
) -> str:
    """获取其他所有agent（dataAgent、reportAgent、publicOptionAgent、vlAgent）的运行结果，用于综合分析并生成投资建议。"""
    return get_agent_res(symbol, cur_date)


# =============================================================================
# Tool group definitions for each agent
# =============================================================================

# DataAgent: 14 tools
DATA_AGENT_TOOLS = [
    lc_zt_stock_hist_price,
    lc_zt_stock_latest_price,
    lc_zt_stock_info,
    lc_zt_stock_kdj,
    lc_zt_stock_boll,
    lc_zt_stock_ma,
    lc_zt_stock_macd,
    lc_stock_individual_fund_flow,
    lc_stock_board_industry_summary_ths,
    lc_stock_financial_report_sina,
    lc_stock_zh_growth_comparison_em,
    lc_stock_zh_valuation_comparison_em,
    lc_stock_zh_scale_comparison_em,
    lc_stock_value_em,
]

# ReportAgent: 1 tool
REPORT_AGENT_TOOLS = [
    lc_stock_research_report_ex,
]

# PublicOptionAgent: 2 tools
PUBLIC_OPTION_AGENT_TOOLS = [
    lc_stock_news_em,
    lc_symbol_tavily_search,
]

# VlAgent: 2 tools
VL_AGENT_TOOLS = [
    lc_zt_stock_latest_price,
    lc_zt_stock_hist_price,
]

# InvestmentAgent: 1 tool
INVESTMENT_AGENT_TOOLS = [
    lc_get_agent_res,
]

# XunguAgent: no tools
XUANGU_AGENT_TOOLS = []

# Mapping from agent name to tool list
AGENT_TOOLS_MAP = {
    "dataAgent": DATA_AGENT_TOOLS,
    "reportAgent": REPORT_AGENT_TOOLS,
    "publicOptionAgent": PUBLIC_OPTION_AGENT_TOOLS,
    "vlAgent": VL_AGENT_TOOLS,
    "investmentAgent": INVESTMENT_AGENT_TOOLS,
    "xuanguAgent": XUANGU_AGENT_TOOLS,
}


def get_langchain_tools_for_agent(agent_name: str) -> list:
    """
    Return the list of LangChain tools for a given agent name.

    Args:
        agent_name: The agent name (e.g., "dataAgent", "reportAgent").

    Returns:
        List of @tool-decorated functions for that agent.
    """
    return AGENT_TOOLS_MAP.get(agent_name, [])
