# 每日持仓分析, 建议设置每天盘后跑
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import akshare as ak
import pandas as pd
import pandas as pd
from tools.aktools import get_trade_date
from datetime import datetime


from agents.planAgent import PlanAgent
from loguru import logger

logger.remove()                                     # 去掉默认全局配置
logger.add(sys.stderr, level="INFO") 

exclude_symbol = os.environ.get("exclude_symbol", "").split("|")
position_symbol = os.environ.get("position_symbol", "").split("|")

# 持仓股票
def position_symbol_task():
    for symbol in position_symbol:
        plan = PlanAgent()
        plan.set_symbol(symbol)
        maxretry = 3
        while maxretry:
            try:
                plan.run(f"详细分析{symbol}行情情况，提供交易建议", human_in_loop=False)
                plan.send_allres_email(subject=f"持仓{symbol}分析")
                break
            except Exception as e:
                logger.error(e)
                maxretry -= 1

def daily_task():
    now = datetime.now().strftime("%Y%m%d")
    if now not in get_trade_date():
        logger.info("未在交易日，跳过")
        return
    position_symbol_task() 


if __name__ == "__main__":
    daily_task()