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
from tools.base_tool import push_server_jio, get_env_vars
from tools.sql_utils import *
from tools.aktools import get_trade_date
from tools.all_types import Tenant
from qinglong.daily_stock_analysis import analysis_stock


max_notify_size = int(os.environ.get("max_notify_size", "5"))

color_map = {
    "极度负面":"darkseagreen",
    "极度正面":"darkred",
    # "正面":"red",
    # "负面":"green"
}

col_map = {
    '舆情情绪': 'sentiment',
    '情绪判断依据': 'sentiment_basis',
    '影响行业/板块': 'affected_industry',
    '影响逻辑说明': 'impact_logic',
    '公司名称': 'company_name',
    '股票代码': 'symbol',
    '风险与关注点': 'risk_focus',
    '新闻id': 'id'
}


def xuangu_process_news_after(df):
    del df["舆情摘要"]
    df = df.rename(columns=col_map)
    data_dict = df.to_dict("records")
    for data in data_dict:
        id = data.pop("id")
        data["notifyed"] = True
        smt = update(StockNews).where(StockNews.id == id).values(
            **data
        )
        exec_record(smt)
        symbol = data["symbol"]
        if data["sentiment"] == "极度正面":
            # try:
            #     smt = select(StockNews).where(StockNews.id == id)
            #     records = find_record(smt)
            #     push_server_jio(records[0]["StockNews"].title, desp=records[0]["StockNews"].__repr__())
            # except Exception as e:
            #     logger.error(e)
            if symbol != "未提及":
                analysis_stock(symbol)


def xuangu_process_news_before(all_news, subject, tenant=None):
    xuangu = XunguAgent()
    md = xuangu.run("\n\n".join(all_news))
    json_data = repair_json(md, return_objects=True)
    df = pd.DataFrame(json_data)
    
    email_df = df.copy()
    email_df = email_df[email_df['舆情情绪'].isin(color_map.keys())]
    email_df['舆情情绪'] = email_df['舆情情绪'].apply(
        lambda x: f'<span style="color: {color_map.get(x, "black")};">{x}</span>'
    )
    del email_df["id"]

    if email_df.empty:
        logger.info("没有需要发送的舆情数据")
        return df
    
    if tenant is None:
        tenants = get_env_vars()
        for _, v in tenants.items():
            logger.debug(v)
            tenant = Tenant.model_validate_json(v)
            dear = tenant.name
            toaddrs = tenant.toaddrs.split("|")
            
            xuangu.send_res_email(email_df.to_markdown(index=False), subject, table=True, toaddrs=toaddrs, dear=dear)
    else:
        tenant = Tenant.model_validate_json(tenant)
        dear = tenant.name
        toaddrs = tenant.toaddrs.split("|")
        # 使用舆情摘要作为邮件主题
        summary = email_df.iloc[0]['舆情摘要'] if '舆情摘要' in email_df.columns and not email_df.empty else subject
        summary_subject = f"热点：{summary[:50]}"
        xuangu.send_res_email(email_df.to_markdown(index=False), summary_subject, table=True, toaddrs=toaddrs, dear=dear)
    
    return df

def telegraph_task():
    subject = "财联社-电报-重要-间隔推送"
    smt = select(StockNews).where(StockNews.notifyed==False , StockNews.source=="财联社")
    records = find_record(smt)

    if records and len(records) >= max_notify_size:
        all_news = []
        for record in records:
            all_news.append(f"新闻id:{record['StockNews'].id}\n\n新闻标题：{record['StockNews'].title}\n\n新闻内容:{record['StockNews'].content}")

        df = xuangu_process_news_before(all_news[:20], subject)
        xuangu_process_news_after(df)
    else:
        logger.info("没有新东西")


def position_task():
    subject = "持仓新闻-实时推送"
    tenants = get_env_vars()
    for _, v in tenants.items():
        logger.debug(v)
        tenant = Tenant.model_validate_json(v)
        position_symbol = tenant.position_symbol.split("|")
        
        conditions = [StockNews.symbol.startswith(prefix) for prefix in position_symbol]
        stmt = select(StockNews).where(or_(*conditions), StockNews.notifyed==False)

        records = find_record(stmt)
        if records:
            all_news = []
            for record in records:
                all_news.append(f"新闻id:{record['StockNews'].id}\n\n新闻标题：{record['StockNews'].title}\n\n新闻内容:{record['StockNews'].content}")

            df = xuangu_process_news_before(all_news, subject, v)
            xuangu_process_news_after(df)
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
