
import json
import akshare as ak
from typing import get_type_hints, Optional, Any, List, Dict, Annotated

from datetime import datetime

def get_date_desc():
    """
    获取当前时间描述，返回当前日期和星期几
    """
    now = datetime.now().strftime("%Y%m%d %H:%M:%S")
    xinqi = datetime.now().weekday() +1
    return f"当前时间是：{now}， 星期{xinqi}"


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

