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
from tools.aktools import get_trade_date
from datetime import datetime


from agents.baseAgent import baseAgent
from agents.planAgent import PlanAgent
from loguru import logger

logger.remove()                                     # 去掉默认全局配置
logger.add(sys.stderr, level="INFO") 

exclude_symbol = os.environ.get("exclude_symbol", "").split("|")
position_symbol = os.environ.get("position_symbol", "").split("|")

# 热榜选股
def hot_symbol_task():
    stock_hot_up_em_df = ak.stock_hot_up_em()
    
    df = stock_hot_up_em_df.head(1)
    
    logger.info(df.to_markdown(index=False))
    
    if not df.empty:
        plan = PlanAgent()
        email_df = df.copy()
        email_df['涨跌幅'] = email_df['涨跌幅'].apply(
            lambda x: f'<span style="color: green;">{x}</span>' if x < 0 else f'<span style="color: red;">{x}</span>'
        )
        plan.send_res_email(email_df.to_markdown(index=False), subject="每日上升榜", table=True)
    
    for _, item in df.iterrows():
        symbol = item.代码[2:]
        # stock_info = ak.stock_individual_info_em(symbol)
        # stock_info_dict = stock_info.set_index('item')['value'].to_dict()
        # if stock_info_dict["总市值"] < 800 * 100000000:  # 市值大于一千亿
        #     continue
        if symbol.startswith("3"):
            continue
        if symbol in exclude_symbol:
            continue
        if symbol in position_symbol:
            continue
        plan = PlanAgent()
        maxretry = 3
        while maxretry:
            try:
                plan.run(f"详细分析{item.股票名称}({symbol})行情情况，提供交易建议", human_in_loop=False)
                plan.send_allres_email(subject=f"{item.股票名称}分析")
                break
            except Exception as e:
                logger.error(e)
                maxretry -= 1


def daily_task():
    now = datetime.now().strftime("%Y%m%d")
    if now not in get_trade_date():
        logger.info("未在交易日，跳过")
        return
    hot_symbol_task()
    
    
if __name__ == "__main__":
    daily_task()