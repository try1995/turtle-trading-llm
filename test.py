from tools import *

def test_daily():
    ret = stock_zh_a_hist("601601.sh", start_date='20251212', end_date='20251212')
    assert ret == [{'ts_code': '601601.SH', 'trade_date': '20251212', 'open': 37.7, 'high': 38.36, 'low': 37.33, 'close': 38.24, 'pre_close': 37.47, 'change': 0.77, 'pct_chg': 2.055, 'vol': 385222.38, 'amount': 1461251.687}]


if __name__ == "__main__":
    ret = get_func_schema(stock_zh_a_hist)
    print(ret)