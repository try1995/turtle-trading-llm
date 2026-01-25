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


def get_stock_info():
    # 以贵州茅台为例，code 后复权请带前缀 sh/sz
    df = ak.stock_individual_info_em(symbol="600519")
    return df

def test_stock_yjbb_em_df():
    return stock_yjbb_em("601601", "20240331")

def test_stock_individual_fund_flow():
    return stock_individual_fund_flow("601601", "20251231")


def test_stock_value_em():
    return stock_value_em("601601", "20251231")

def test_stock_individual_info_em():
    return stock_individual_info_em("000001")

def test_stock_board_industry_summary_ths():
    return stock_board_industry_summary_ths("000001")


def test_stock_news_em():
    return stock_news_em("000001")


def test_stock_zh_growth_comparison_em():
    return stock_zh_growth_comparison_em("000001")


def test_stock_zh_valuation_comparison_em():
    return stock_zh_valuation_comparison_em("601601")


def test_stock_zh_scale_comparison_em():
    return stock_zh_scale_comparison_em("000001")

# if __name__ == "__main__":
    # ret = get_func_schema(stock_zh_a_hist)
    # ret = test_stock_research_report_em()
    # ret = test_markitdown()
    # ret = test_get_indicators()
    # ret = get_trade_date()
    # ret = get_stock_info()
    # ret = test_stock_yjbb_em_df()
    # ret = test_stock_individual_fund_flow()
    # ret = test_stock_value_em()
    # ret = test_stock_individual_info_em()
    # ret = test_stock_board_industry_summary_ths()
    # ret = test_stock_news_em()
    # print(ret)
    # import akshare as ak

    # stock_news_main_cx_df = ak.stock_news_main_cx()
    # print(stock_news_main_cx_df.head(2))
    # print(stock_news_main_cx_df["url"].to_list()[0])

    # import akshare as ak

    # ret = stock_financial_report_sina("601601")

    # 获取财务分析指标
    # indicators = ak.stock_financial_analysis_indicator(symbol="600600")
    # from report.dataReport import data_report
    # print(data_report[0].dict())
    # print(data_report.report[0].model_json_schema())

    # ret = test_stock_zh_growth_comparison_em()
    # ret = test_stock_zh_valuation_comparison_em()
    # import akshare as ak

    # stock_info_cjzc_em_df = ak.stock_info_cjzc_em()
    # print("第一个")
    # print(stock_info_cjzc_em_df.head(1).to_dict("records"))
    
    
    # stock_info_global_em_df = ak.stock_info_global_em()
    # print("第二个")
    # print(stock_info_global_em_df.head(6).to_dict())
    # stock_info_global_sina_df = ak.stock_info_global_sina()
    # print("第三个")
    # print(stock_info_global_sina_df.head(6).to_dict())
    # stock_info_global_futu_df = ak.stock_info_global_futu()
    # print("第四个")
    # print(stock_info_global_futu_df.head(6).to_dict())

    # stock_info_global_ths_df = ak.stock_info_global_ths()
    # print("第五个")
    # print(stock_info_global_ths_df.head(6).to_dict())
    
    # stock_info_global_cls_df = ak.stock_info_global_cls(symbol="全部")
    # print("第刘六个")
    # print(stock_info_global_cls_df.head(6).to_dict())
    

if __name__ == "__main__":
    url = stock_info_cjzc_em()
    content = fetch_url_content(url)
    print(content)