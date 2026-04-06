# https://github.com/ZhuLinsen/daily_stock_analysis.git
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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


def daily_task():
    now = datetime.now().strftime("%Y%m%d")
    if now not in get_trade_date():
        logger.info("未在交易日，跳过")
        return
    analysis_stock()
    
    
if __name__ == "__main__":
    daily_task()
