# 行业热点选择板块，板块里面筛选股票
import os
import akshare as ak
import pandas as pd
# 关注排行榜
# stock_hot_follow_xq_df = ak.stock_hot_follow_xq(symbol="最热门")
# 讨论排行榜
# stock_hot_tweet_xq_df = ak.stock_hot_tweet_xq(symbol="最热门")
# 交易排行榜

# 飙升榜-A股
# stock_hot_up_em_df = ak.stock_hot_up_em()
import pandas as pd
from tools.aktools import  get_trade_date
from datetime import datetime


from agents.planAgent import PlanAgent
from loguru import logger
import sys

logger.remove()                                     # 去掉默认全局配置
logger.add(sys.stderr, level="INFO") 


def daily_task():
    now = datetime.now().strftime("%Y%m%d")
    if now not in get_trade_date():
        logger.info("未在交易日，跳过")
        return
    stock_hot_deal_xq_df = ak.stock_hot_deal_xq(symbol="最热门")
    # 人气榜-A股
    stock_hot_rank_em_df = ak.stock_hot_rank_em()
    
    df = pd.merge(stock_hot_deal_xq_df.head(200), stock_hot_rank_em_df.head(200), how='inner')
    
    # 茅台太贵
    exclude_symbol = os.environ.get("exclude_symbol").split("|")
    # 持仓股票
    position_symbol = os.environ.get("position_symbol").split("|")

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
                
    for _, item in df.iterrows():
        symbol = item.股票代码[2:]
        stock_info = ak.stock_individual_info_em(symbol)
        stock_info_dict = stock_info.set_index('item')['value'].to_dict()
        if stock_info_dict["总市值"] < 800 * 100000000:  # 市值大于一千亿
            continue
        if symbol.startswith("3"):
            continue
        if symbol in exclude_symbol:
            continue
        if symbol in position_symbol:
            continue
        print(stock_info)
        plan = PlanAgent()
        plan.set_symbol(symbol)
        maxretry = 3
        while maxretry:
            try:
                plan.run(f"详细分析{symbol}行情情况，提供交易建议", human_in_loop=False)
                plan.send_allres_email(subject=f"{item.股票简称}分析")
                break
            except Exception as e:
                logger.error(e)
                maxretry -= 1
    


if __name__ == "__main__":
    daily_task()