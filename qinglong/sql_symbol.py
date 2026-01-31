# 提取数据库中数据分析

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
from datetime import datetime
from loguru import logger
from json_repair import repair_json
from agents.xuanguAgent import XunguAgent
from agents.planAgent import PlanAgent
from tools.base_tool import push_server_jio
from tools.sql_utils import *
from tools.aktools import get_trade_date

max_notify_size = int(os.environ.get("max_notify_size", "5"))
position_symbol = os.environ.get("position_symbol", "").split("|")

def analyse_symbol(md):
    datas_json = repair_json(md, return_objects=True)
    for data in datas_json:
        id = data.pop("id")
        data["notifyed"] = True
        if "span" in data["sentiment"]:
            data["sentiment"] = data["sentiment"][data["sentiment"].find('>')+1:data["sentiment"].rfind('<')] 
        smt = update(StockNews).where(StockNews.id == id).values(
            **data
        )
        exec_record(smt)
        symbol = data["symbol"]
        if data["sentiment"] == "极度正面" and symbol != "未提及":
            try:
                push_server_jio(f"极度正面{symbol}出现了！", desp=json.dumps(data, ensure_ascii=False))
            except Exception as e:
                logger.error(e)
            plan = PlanAgent()
            maxretry = 3
            while maxretry:
                try:
                    plan.run(f"详细分析{data['company_name']}({symbol})行情情况，提供交易建议", human_in_loop=False)
                    plan.send_allres_email(subject=f"极度正面{data['company_name']}({symbol})分析")
                    break
                except Exception as e:
                    logger.error(e)
                    maxretry -= 1
    pass

def telegraph_task():
    subject = "财联社-电报-重要-间隔推送"
    smt = select(StockNews).where(StockNews.notifyed==False , StockNews.source=="财联社")
    records = find_record(smt)

    if records and len(records) >= max_notify_size:
        all_news = []
        for record in records:
            all_news.append(f"新闻id:{record['StockNews'].id}"+record['StockNews'].content)
        xuangu = XunguAgent()
        md = xuangu.run("\n\n".join(all_news))
        xuangu.send_res_email(md.split("```<split>```")[0], subject)
        
        analyse_symbol(md)
    else:
        logger.info("没有新东西")


def position_task():
    subject = "持仓新闻-实时推送"
    conditions = [StockNews.symbol.startswith(prefix) for prefix in position_symbol]
    stmt = select(StockNews).where(or_(*conditions), StockNews.notifyed==False)

    records = find_record(stmt)
    if records:
        all_news = []
        for record in records:
            all_news.append(f"新闻id:{record['StockNews'].id}"+record['StockNews'].content)
        xuangu = XunguAgent()
        md = xuangu.run("\n\n".join(all_news))
        xuangu.send_res_email(md.split("```<split>```")[0], subject)
        
        analyse_symbol(md)
    else:
        logger.info("没有新东西")

def main():
    now = datetime.now().strftime("%Y%m%d")
    if now not in get_trade_date():
        logger.info("未在交易日，发送最大窗口翻倍")
    global max_notify_size
    max_notify_size += max_notify_size
    telegraph_task()
    position_task()

if __name__ == "__main__":
    main()