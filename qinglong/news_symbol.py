# 新闻入数据库，包括财联社，持仓股票新闻，这里入库是为了方便后续分析-sql_symbol.py
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
from tools.all_types import Tenant
from loguru import logger


def gen_md5(text):
    """生成字符串的 MD5"""
    md5 = hashlib.md5()
    md5.update(text.encode('utf-8'))
    return md5.hexdigest()


@logger.catch
def telegraph_sql_task():
    telegraph_content_raw = stock_info_global_cls()
    telegraph_content = json.loads(telegraph_content_raw)
    if telegraph_content:
        for content in telegraph_content:
            record = StockNews(
                id = gen_md5(content["标题"]),
                title = content["标题"],
                content = content["内容"]
            )
            add_record(record)

@logger.catch
def position_sql_task(position_symbol):
    for symbol in position_symbol:
        stock_news_raw = stock_news_em(symbol)
        stock_news = json.loads(stock_news_raw)
        if stock_news:
            for content in stock_news:
                publish_day = content["发布时间"][:10]
                if datetime.strptime(publish_day, "%Y-%m-%d").date() != datetime.today().date():
                    continue
                record = StockNews(
                    id = gen_md5(content["新闻标题"]),
                    title = content["新闻标题"],
                    content = content["新闻内容"],
                    symbol = symbol,
                    source = content["文章来源"]
                )
                add_record(record)

def main(position_symbol):
    telegraph_sql_task()
    position_sql_task(position_symbol)

if __name__ == "__main__":
    # python news_symbol.py '{"name":"汤总","toaddrs":"1635341612@qq.com","exclude_symbol":"000001","position_symbol":"601601"}'
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        logger.info(f"tenant参数：{arg1}")

        tenant_raw = os.environ.get(arg1, "")

        if tenant_raw:
            tenant = Tenant.model_validate_json(tenant_raw)
            position_symbol = tenant.position_symbol.split("|")
            main(position_symbol)
        else:
            logger.error(f"未定义环境变量{arg1}")
    else:
        logger.error("未定义tenant")
    
    