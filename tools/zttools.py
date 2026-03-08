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
    描述：获取股票代码日线级别历史交易数据，建议时间间隔不超过90天

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


def zt_stock_macd(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    # period: Annotated[Literal["5", "15", "30", "60", "d", "w", "m", "y"], 
    #                   "分时级别：5=5分钟,15=15分钟,30=30分钟,60=60分钟,d=日线,w=周线,m=月线,y=年线"],
    # adjust: Annotated[Literal["n", "f", "b", "fr", "br"], 
    #                   "除权类型：n=不复权,f=前复权,b=后复权,fr=等比前复权,br=等比后复权(分钟级只能用n)"],
    start_date: Annotated[str, "开始时间 %Y%m%d，e.g. 20240101"],
    end_date: Annotated[str, "结束时间 %Y%m%d，e.g. 20240102"],
    # limit: Annotated[int, "最新条数，e.g. 50表示获取最新50条数据"] = 50
):
    """
    描述：根据《股票列表》得到的股票代码和分时级别获取历史MACD数据，交易时间升序
    
    输出参数-MACD指标数据

    名称        类型      描述
    交易时间     string   短分时级别格式为yyyy-MM-dd HH:mm:ss，日线级别为yyyy-MM-dd
    DIFF值      number   DIFF值
    DEA值       number   DEA值
    MACD值      number   MACD值
    EMA12值     number   EMA（12）值
    EMA26值     number   EMA（26）值
    """
    # 构建带市场标识的股票代码
    symbol_with_market = symbol + "." + get_market(symbol).upper()
    
    period = "d"
    adjust = "n"
    # 构建基础URL
    url = f"https://api.zhituapi.com/hs/history/macd/{symbol_with_market}/{period}/{adjust}?token={ZT_TOKEN}&st={start_date}&et={end_date}"
    
    url += f"&lt={50}"

    # 发送请求
    response = requests.get(url)
    data = response.json()
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列
    column_mapping = {
        't': '交易时间',
        'diff': 'DIFF值',
        'dea': 'DEA值',
        'macd': 'MACD值',
        'ema12': 'EMA12值',
        'ema26': 'EMA26值'
    }
    df = df.rename(columns=column_mapping)
    
    # 将所有列转换为object类型并转为字典列表
    df = df.astype(str).to_dict("records")
    
    return json.dumps(df, ensure_ascii=False)


def zt_stock_ma(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    # period: Annotated[Literal["5", "15", "30", "60", "d", "w", "m", "y"], 
    #                   "分时级别：5=5分钟,15=15分钟,30=30分钟,60=60分钟,d=日线,w=周线,m=月线,y=年线"],
    # adjust: Annotated[Literal["n", "f", "b", "fr", "br"], 
    #                   "除权类型：n=不复权,f=前复权,b=后复权,fr=等比前复权,br=等比后复权(分钟级只能用n)"],
    start_date: Annotated[str, "开始时间 %Y%m%d，e.g. 20240101"],
    end_date: Annotated[str, "结束时间 %Y%m%d，e.g. 20241231"],
):
    """
    描述：根据《股票列表》得到的股票代码和分时级别获取历史MA（移动平均线）数据，交易时间升序
    

    输出参数-MA指标数据

    名称        类型      描述
    交易时间     string   短分时级别格式为yyyy-MM-dd HH:mm:ss，日线级别为yyyy-MM-dd
    MA5值       number   5周期移动平均线值
    MA10值      number   10周期移动平均线值
    MA20值      number   20周期移动平均线值
    MA30值      number   30周期移动平均线值
    MA60值      number   60周期移动平均线值
    MA120值     number   120周期移动平均线值
    MA250值     number   250周期移动平均线值
    """
    # 构建带市场标识的股票代码
    symbol_with_market = symbol + "." + get_market(symbol).upper()
    
    # 构建基础URL
    period = "d"
    adjust = "n"
    url = f"https://api.zhituapi.com/hs/history/ma/{symbol_with_market}/{period}/{adjust}?token={ZT_TOKEN}&st={start_date}&et={end_date}"
    
    url += f"&lt={50}"
    # 发送请求
    response = requests.get(url)
    data = response.json()
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列
    column_mapping = {
        't': '交易时间',
        'ma5': 'MA5值',
        'ma10': 'MA10值',
        'ma20': 'MA20值',
        'ma30': 'MA30值',
        'ma60': 'MA60值',
        'ma120': 'MA120值',
        'ma250': 'MA250值'
    }
    df = df.rename(columns=column_mapping)
    
    # 将所有列转换为object类型并转为字典列表
    df = df.astype(str).to_dict("records")
    
    return json.dumps(df, ensure_ascii=False)


def zt_stock_boll(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    start_date: Annotated[str, "开始时间 %Y%m%d，e.g. 20240101"],
    end_date: Annotated[str, "结束时间 %Y%m%d，e.g. 20241231"],
):
    """
    描述：根据《股票列表》得到的股票代码和分时级别获取历史BOLL（布林带）数据，交易时间升序
    
    输出参数-BOLL指标数据

    名称        类型      描述
    交易时间     string   短分时级别格式为yyyy-MM-dd HH:mm:ss，日线级别为yyyy-MM-dd
    上轨        number   布林带上轨值(UP)
    中轨        number   布林带中轨值(MID)
    下轨        number   布林带下轨值(DOWN)
    """
    # 构建带市场标识的股票代码
    symbol_with_market = symbol + "." + get_market(symbol).upper()

    period = "d"
    adjust = "n"
    # 构建基础URL
    url = f"https://api.zhituapi.com/hs/history/boll/{symbol_with_market}/{period}/{adjust}?token={ZT_TOKEN}&st={start_date}&et={end_date}"
    
    url += f"&lt={50}"
    
    # 发送请求
    response = requests.get(url)
    data = response.json()
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列（注意：文档中u=上轨, d=下轨, m=中轨）
    column_mapping = {
        't': '交易时间',
        'u': '上轨',
        'm': '中轨',
        'd': '下轨'
    }
    df = df.rename(columns=column_mapping)
    
    # 调整列顺序：时间、上轨、中轨、下轨
    df = df[['交易时间', '上轨', '中轨', '下轨']]
    
    # 将所有列转换为object类型并转为字典列表
    df = df.astype(str).to_dict("records")
    
    return json.dumps(df, ensure_ascii=False)


def zt_stock_kdj(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    start_date: Annotated[str, "开始时间 %Y%m%d，e.g. 20240101"],
    end_date: Annotated[str, "结束时间 %Y%m%d，e.g. 20241231"],
):
    """
    描述：根据《股票列表》得到的股票代码和分时级别获取历史KDJ（随机指标）数据，交易时间升序
    
    更新频率：
    - 分钟级别数据盘中更新，分时越小越优先更新
      （如5分钟级别每5分钟更新，15分钟级别每15分钟更新，以此类推）
    - 日线及以上级别每日15:35更新
    
    请求频率限制：
    - 体验版：1分钟1000次
    - 包量版：1分钟300次
    - 包月版：1分钟1000次
    - 包年版：1分钟3000次
    - 至尊版：1分钟6000次

    输出参数-KDJ指标数据

    名称        类型      描述
    交易时间     string   短分时级别格式为yyyy-MM-dd HH:mm:ss，日线级别为yyyy-MM-dd
    K值         number   K值（快速确认线）
    D值         number   D值（慢速主干线）
    J值         number   J值（方向敏感线）
    """
    # 构建带市场标识的股票代码
    symbol_with_market = symbol + "." + get_market(symbol).upper()
    
    period = "d"
    adjust = "n"
    # 构建基础URL
    url = f"https://api.zhituapi.com/hs/history/kdj/{symbol_with_market}/{period}/{adjust}?token={ZT_TOKEN}&st={start_date}&et={end_date}"
    
    url += f"&lt={50}"
    
    # 发送请求
    response = requests.get(url)
    data = response.json()
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列
    column_mapping = {
        't': '交易时间',
        'k': 'K值',
        'd': 'D值',
        'j': 'J值'
    }
    df = df.rename(columns=column_mapping)
    
    # 将所有列转换为object类型并转为字典列表
    df = df.astype(str).to_dict("records")
    
    return json.dumps(df, ensure_ascii=False)


import requests
import pandas as pd
import json
from typing import Annotated

def zt_pool_dtgc(
    trade_date: Annotated[str, "交易日期，格式yyyy-MM-dd，从2019-11-28开始，e.g. 2024-01-15"]
):
    """
    描述：根据日期获取每天的跌停股票列表，根据封单资金升序
    
    输出参数-跌停股票数据

    名称        类型      描述
    代码        string   股票代码
    名称        string   股票名称
    价格        number   当前价格（元）
    跌幅        number   跌幅（%）
    成交额      number   成交额（元）
    流通市值    number   流通市值（元）
    总市值      number   总市值（元）
    动态市盈率   number   动态市盈率
    换手率      number   换手率（%）
    连续跌停次数 number   连续跌停次数
    最后封板时间 string   最后封板时间（HH:mm:ss）
    封单资金    number   封单资金（元）
    板上成交额   number   板上成交额（元）
    开板次数    number   开板次数
    """
    # 构建API请求URL
    url = f"https://api.zhituapi.com/hs/pool/dtgc/{trade_date}?token={ZT_TOKEN}"
    
    # 发送请求
    response = requests.get(url)
    data = response.json()
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列
    column_mapping = {
        'dm': '代码',
        'mc': '名称',
        'p': '价格',
        'zf': '跌幅',
        'cje': '成交额',
        'lt': '流通市值',
        'zsz': '总市值',
        'pe': '动态市盈率',
        'hs': '换手率',
        'lbc': '连续跌停次数',
        'lbt': '最后封板时间',
        'zj': '封单资金',
        'fba': '板上成交额',
        'zbc': '开板次数'
    }
    df = df.rename(columns=column_mapping)
    
    # 将所有列转换为object类型并转为字典列表
    df = df.astype(str).to_dict("records")
    
    return json.dumps(df, ensure_ascii=False)