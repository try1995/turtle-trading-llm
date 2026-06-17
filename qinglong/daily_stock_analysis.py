# https://github.com/ZhuLinsen/daily_stock_analysis.git
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json

import requests
from loguru import logger
from tools import get_trade_date
from tools.zttools import zt_strong_stock_pool
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

anlysis_symbol_url = os.environ.get("anlysis_symbol_url", "")
anlysis_symbol_pasword = os.environ.get("anlysis_symbol_pasword", "")


def login():
    session = requests.Session()  # 创建会话对象保持状态
    data = {
    "password": anlysis_symbol_pasword,
    "passwordConfirm": "string"}
    ret = session.post(f"http://{anlysis_symbol_url}/api/v1/auth/login", json=data)
    logger.info(ret.json())
    return session


def analysis_stock(symbol=None):
    session = login()
    anlysis_symbol = symbol if symbol is not None else os.environ.get("anlysis_symbol", "")
    for _symbol in anlysis_symbol.split(","):
        data = {
            "async_mode": True,
            "force_refresh": False,
            "report_type": "detailed",
            "stock_code": _symbol
            }
        ret = session.post(f"http://{anlysis_symbol_url}/api/v1/analysis/analyze", json=data)
        logger.info(ret.json())
    session.post(f"http://{anlysis_symbol_url}/api/v1/auth/logout", json=data)


def get_previous_trade_date():
    """获取前一个交易日，参考 baseAgent.get_date_desc 逻辑
        - 交易日9:30之前 → 用 trade_date[-2]（前一个交易日）
        - 非交易日 → 用 trade_date[-1]（最后一个交易日）
    """
    now = datetime.now()
    trade_date = get_trade_date(end_date=now.strftime('%Y%m%d'))
    if now.strftime('%Y%m%d') in trade_date and now.hour <= 9 and now.minute < 30:
        return trade_date[-2]
    if now.strftime('%Y%m%d') not in trade_date:
        return trade_date[-1]
    # 交易日9:30之后，取前一个交易日
    idx = trade_date.index(now.strftime('%Y%m%d'))
    return trade_date[idx - 1] if idx > 0 else trade_date[-2]


def get_strong_stocks(date):
    """获取指定日期的强势股池列表，返回逗号分隔的股票代码字符串"""
    result = zt_strong_stock_pool(date)
    stocks = json.loads(result)
    symbols = [s["dm"] for s in stocks]
    logger.info(f"{date} 强势股池: {symbols}")
    return ",".join(symbols)


def daily_task():
    now = datetime.now().strftime("%Y%m%d")
    if now not in get_trade_date():
        logger.info("未在交易日，跳过")
        return
    prev_date = get_previous_trade_date()
    if prev_date is None:
        logger.info("无法获取前一个交易日")
        return
    symbols = get_strong_stocks(prev_date)
    if not symbols:
        logger.info(f"{prev_date} 没有强势股，跳过")
        return
    analysis_stock(symbol=symbols)
    
    
if __name__ == "__main__":
    daily_task()
