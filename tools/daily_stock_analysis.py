# https://github.com/ZhuLinsen/daily_stock_analysis.git
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import akshare as ak
import pandas as pd
import requests
from loguru import logger
from tools import get_trade_date
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


def analysis_stock_sync(symbol=None, report_type="detailed", force_refresh=False, timeout=1200):
    """同步分析股票，阻塞等待分析结果返回。

    与 analysis_stock（异步 fire-and-forget）不同，
    本函数设置 async_mode=False，等待每个股票的分析完成并返回结果。

    Args:
        symbol: 股票代码，多个用逗号分隔。默认从环境变量 anlysis_symbol 读取。
        report_type: 报告类型，可选 simple/detailed/full/brief，默认 detailed。
        force_refresh: 是否强制刷新（忽略缓存）。
        timeout: 单个股票的超时秒数，默认 300。

    Returns:
        dict: {stock_code: analysis_result_dict, ...}
    """
    session = login()
    symbols = symbol if symbol is not None else os.environ.get("anlysis_symbol", "")
    results = {}

    for _symbol in symbols.split(","):
        _symbol = _symbol.strip()
        if not _symbol:
            continue

        data = {
            "async_mode": False,
            "force_refresh": force_refresh,
            "report_type": report_type,
            "stock_code": _symbol,
        }
        logger.info(f"开始同步分析: {_symbol}")
        try:
            ret = session.post(
                f"http://{anlysis_symbol_url}/api/v1/analysis/analyze",
                json=data,
                timeout=timeout,
            )
            ret.raise_for_status()
            resp = ret.json()
            logger.info(f"分析完成: {_symbol}, query_id={resp.get('query_id', 'N/A')}")
            results[_symbol] = resp
        except requests.Timeout:
            logger.error(f"分析超时: {_symbol} (>{timeout}s)")
            results[_symbol] = {"error": f"timeout_{timeout}s"}
        except requests.RequestException as e:
            logger.error(f"分析失败: {_symbol}, {e}")
            results[_symbol] = {"error": str(e)}

    session.post(f"http://{anlysis_symbol_url}/api/v1/auth/logout")
    return results