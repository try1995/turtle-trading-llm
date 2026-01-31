# 新闻入数据库，包括财联社，持仓股票新闻
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
import json
import hashlib
from datetime import datetime
from tools.sql_utils import *
from tools.aktools import stock_news_em, stock_info_global_cls

position_symbol = os.environ.get("position_symbol", "").split("|")


def gen_md5(text):
    """生成字符串的 MD5"""
    md5 = hashlib.md5()
    md5.update(text.encode('utf-8'))
    return md5.hexdigest()


def telegraph_sql_task():
    telegraph_content_raw = stock_info_global_cls()
    telegraph_content = json.loads(telegraph_content_raw)
    if telegraph_content:
        all_record = []
        for content in telegraph_content:
            all_record.append(StockNews(
                id = gen_md5(content["标题"]),
                title = content["标题"],
                content = content["内容"]
            ))
        add_record(all_record)
        logger.info(f"财联社共插入{len(all_record)}条数据")

def position_sql_task():
    for symbol in position_symbol:
        stock_news_raw = stock_news_em(symbol)
        stock_news = json.loads(stock_news_raw)
        if stock_news:
            all_record = []
            for content in stock_news:
                publish_day = content["发布时间"][:10]
                if datetime.strptime(publish_day, "%Y-%m-%d").date() != datetime.today().date():
                    continue
                all_record.append(StockNews(
                    id = gen_md5(content["新闻标题"]),
                    title = content["新闻标题"],
                    content = content["新闻内容"],
                    stock_code = symbol,
                    source = content["文章来源"]
                ))
            add_record(all_record)
            logger.info(f"{symbol}共插入{len(all_record)}条数据")

def main():
    telegraph_sql_task()
    position_sql_task()

if __name__ == "__main__":
    main()
    
    