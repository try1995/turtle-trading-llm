import os
from tools import *
import tempfile
import requests
import talib as ta

def test_daily():
    ret = stock_zh_a_hist("601601.sh", start_date='20251212', end_date='20251212')
    assert ret == [{'ts_code': '601601.SH', 'trade_date': '20251212', 'open': 37.7, 'high': 38.36, 'low': 37.33, 'close': 38.24, 'pre_close': 37.47, 'change': 0.77, 'pct_chg': 2.055, 'vol': 385222.38, 'amount': 1461251.687}]


def test_stock_research_report_em():
    return stock_research_report_em("601601", cur_date='20251212')

def test_markitdown():
    from markitdown import MarkItDown

    md = MarkItDown(docintel_endpoint="<document_intelligence_endpoint>")

    url = "https://pdf.dfcfw.com/pdf/H3_AP202511091778101835_1.pdf"

    with tempfile.TemporaryDirectory() as tempdir:
        ret = requests.get(url)
        file_path = os.path.join(tempdir, "temp.pdf")
        with open(file_path, 'wb') as f:
            f.write(ret.content)
        result = md.convert(file_path)
        return result.text_content
        
def test_get_indicators():
    df = get_indicators("601601", cur_date="20251201")
    return df

def get_trade_date():
    # 交易日历
    tool_trade_date_hist_sina_df = ak.tool_trade_date_hist_sina()
    return tool_trade_date_hist_sina_df


def get_stock_info():
    # 以贵州茅台为例，code 后复权请带前缀 sh/sz
    df = ak.stock_individual_info_em(symbol="600519")
    return df

def test_stock_yjbb_em_df():
    return stock_yjbb_em("601601", "20240331")


if __name__ == "__main__":
    # ret = get_func_schema(stock_zh_a_hist)
    # ret = test_stock_research_report_em()
    # ret = test_markitdown()
    # ret = test_get_indicators()
    # ret = get_trade_date()
    # ret = get_stock_info()
    # ret = test_stock_yjbb_em_df()
    # print(ret)

    stock_individual_fund_flow_df = ak.stock_individual_fund_flow(stock="601601", market="sh")
    print(stock_individual_fund_flow_df)
