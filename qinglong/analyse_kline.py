# 每日飙升榜选股，可以每周跑，也可以每天跑
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import akshare as ak
import pandas as pd
import pandas as pd
from tools import get_trade_date, get_a_symbol_info
from datetime import datetime


from agents.vlAgent import VlAgent
from loguru import logger

logger.remove()                                     # 去掉默认全局配置
logger.add(sys.stderr, level="INFO") 

exclude_symbol = os.environ.get("exclude_symbol", "").split("|")
position_symbol = os.environ.get("position_symbol", "").split("|")
toaddrs = os.environ.get("position_symbol", "").split("|")
# 热榜选股
def analysis_task():
    vl_agent = VlAgent()
    for symbol in position_symbol:
        vl_agent.set_symbol(symbol, "")
        md = vl_agent.run(f"分析{symbol}")
        vl_agent.send_res_email(md, subject=f"持仓盘中分析-{symbol}", table=True, toaddrs=[toaddrs[0]])

def daily_task():
    now = datetime.now().strftime("%Y%m%d")
    # if now not in get_trade_date():
    #     logger.info("未在交易日，跳过")
    #     return
    analysis_task()
    
    
if __name__ == "__main__":
    daily_task()