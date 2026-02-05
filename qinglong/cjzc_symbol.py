# 通东方财富-财经早餐，每天6点出新闻，可以每天7点执行
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
import pandas as pd
from loguru import logger
from datetime import datetime
from json_repair import repair_json
from agents.xuanguAgent import XunguAgent
from agents.planAgent import PlanAgent
from tools.aktools import stock_info_cjzc_em, get_trade_date
from tools.base_tool import push_server_jio
from qinglong.sql_symbol import xuangu_process_news_before, xuangu_process_news_after


def xuangu_task():
    subject = "通东方财富-财经早餐-每日选股"

    _, cjzc_content = stock_info_cjzc_em()

    df = xuangu_process_news_before([cjzc_content], subject)
    
    xuangu_process_news_after(df)

def daily_task():
    now = datetime.now().strftime("%Y%m%d")
    if now not in get_trade_date():
        logger.info("未在交易日，跳过")
        return
    xuangu_task()


if __name__ == "__main__":
    daily_task()