# 智兔api https://www.zhituapi.com/hsstockapi.html
import os
import requests
import json
import pandas as pd
from .base_tool import get_market
from typing import get_type_hints, Optional, Any, List, Dict, Annotated
from collections import defaultdict


ZT_TOKEN = os.environ.get("ZT_TOKEN")

def zt_price_process(data):
    # 创建DataFrame
    df = pd.DataFrame(data)

    # 删除sf列
    df = df.drop(columns=['sf', "pc"])

    # 重命名列
    column_mapping = {
        't': '交易时间',
        'o': '开盘价',
        'h': '最高价',
        'l': '最低价',
        'c': '收盘价',
        'v': '成交量',
        'a': '成交额'
    }
    df = df.rename(columns=column_mapping)

    # 将所有列转换为object类型
    df = df.astype(str).to_dict("records")
    return json.dumps(df, ensure_ascii=False)

def zt_stock_latest_price(
    symbol: Annotated[str, "股票代码，e.g. 603777"]
):
    """
    描述：获取股票代码最新5分钟级别的交易数据

    输出参数-行情数据

    字段名称	数据类型	字段说明
    t	string	交易时间
    o	float	开盘价
    h	float	最高价
    l	float	最低价
    c	float	收盘价
    v	float	成交量
    a	float	成交额
    pc	float	前收盘价
    """
    symbol = symbol + "." + get_market(symbol).upper()
    url = f"https://api.zhituapi.com/hs/history/{symbol}/5/n?token={ZT_TOKEN}&limit=5"
    response = requests.get(url)
    data = response.json()
    return zt_price_process(data)
    

# 日线及以上级别每日15:30开始更新，预计17:10完成
def zt_stock_hist_price(
    symbol: Annotated[str, "股票代码，e.g. 603777"],
    start_date: Annotated[str, "开始日期 %Y%m%d，e.g. 20210301"],
    end_date: Annotated[str, "结束日期 %Y%m%d，e.g. 20210616"]
):
    """
    描述：获取股票代码日线级别历史交易数据

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
    symbol = symbol + "." + get_market(symbol).upper()
    url = f"https://api.zhituapi.com/hs/history/{symbol}/d/n?token={ZT_TOKEN}&st={start_date}&et={end_date}"
    response = requests.get(url)
    data = response.json()

    return zt_price_process(data)


# 貌似没什么用
#更新频率：每日下午16:30开始更新，预计20:00完成更新
def zt_stock_indicators(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    start_date: Annotated[str, "开始日期 %Y%m%d，e.g. 20240101"],
    end_date: Annotated[str, "结束日期 %Y%m%d，e.g. 20240131"]
):
    """
    描述：根据股票代码获取各项行情指标
    
    
    输出参数-行情指标数据

    名称      类型      描述
    更新时间   string   数据更新时间
    量比      float    量比
    1分钟涨速  float    1分钟涨速(%)
    5分钟涨速  float    5分钟涨速(%)
    3日涨幅    float    3日涨幅(%)
    5日涨幅    float    5日涨幅(%)
    10日涨幅   float    10日涨幅(%)
    3日换手    float    3日换手(%)
    5日换手    float    5日换手(%)
    10日换手   float    10日换手(%)
    """
    # 构建带市场标识的股票代码
    symbol = symbol + "." + get_market(symbol).upper()
    
    # 构建API请求URL
    url = f"https://api.zhituapi.com/hs/indicators/{symbol}?token={ZT_TOKEN}&st={start_date}&et={end_date}"
    
    # 发送请求
    response = requests.get(url)
    data = response.json()
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列
    column_mapping = {
        'time': '更新时间',
        'lb': '量比',
        'om': '1分钟涨速',
        'fm': '5分钟涨速',
        '3d': '3日涨幅',
        '5d': '5日涨幅',
        '10d': '10日涨幅',
        '3t': '3日换手',
        '5t': '5日换手',
        '10t': '10日换手'
    }
    df = df.rename(columns=column_mapping)
    
    # 将所有列转换为object类型并转为字典列表
    df = df.astype(str).to_dict("records")
    
    return json.dumps(df, ensure_ascii=False)


def zt_stock_info(
    symbol: Annotated[str, "股票代码，e.g. 000001"]
):
    """
    描述：依据股票代码获取股票的基础信息
    
    输出参数-股票基础信息

    名称        类型      描述
    市场代码     string   市场代码
    股票代码     string   不带市场标识的股票代码
    股票名称     string   股票名称
    上市日期     string   股票IPO日期
    前收盘价格   float    前收盘价格
    当日涨停价   float    当日涨停价
    当日跌停价   float    当日跌停价
    流通股本     float    流通股本
    总股本       float    总股本
    最小价格变动单位 float  最小价格变动单位
    股票停牌状态 int      <=0:正常交易（-1:复牌）; >=1停牌天数
    """
    # 构建带市场标识的股票代码
    symbol_with_market = symbol + "." + get_market(symbol).upper()
    
    # 构建API请求URL（注意：文档中是http，但建议用https）
    url = f"https://api.zhituapi.com/hs/instrument/{symbol_with_market}?token={ZT_TOKEN}"
    
    # 发送请求
    response = requests.get(url)
    data = response.json()
    
    # 由于返回的是单条数据，需要包装成列表再创建DataFrame
    if not isinstance(data, list):
        data = [data]
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列
    column_mapping = {
        'ei': '市场代码',
        'ii': '股票代码',
        'name': '股票名称',
        'od': '上市日期',
        'pc': '前收盘价格',
        'up': '当日涨停价',
        'dp': '当日跌停价',
        'fv': '流通股本',
        'tv': '总股本',
        'pk': '最小价格变动单位',
        'is': '股票停牌状态'
    }
    df = df.rename(columns=column_mapping)
    
    # 将所有列转换为object类型并转为字典列表
    df = df.astype(str).to_dict("records")
    
    return json.dumps(df, ensure_ascii=False)