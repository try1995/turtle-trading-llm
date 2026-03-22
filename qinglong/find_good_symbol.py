import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.sql_utils import *

from datetime import datetime, timedelta
from sqlalchemy import select
from agents.xuanguAgent import XunguAgent
from tools.all_types import Tenant

# 计算三天前的时间
three_days_ago = datetime.now() - timedelta(days=3)


def main():
    stmt = select(StockNews).where(StockNews.source=="财联社", \
                                   StockNews.created_at >= three_days_ago, \
                                    StockNews.sentiment.in_(["正面","极度正面"]))
    records = find_record(stmt)
    # print(records)
    if records:
        all_news = []
        for record in records:
            # print(record['StockNews'].created_at)
            all_news.append(f"新闻标题：{record['StockNews'].title}\n\n新闻影响板块:{record['StockNews'].affected_industry}\n\n影响逻辑说明:{record['StockNews'].impact_logic}\n\n可能关联的股票或者公司:{record['StockNews'].company_name} {record['StockNews'].symbol}")
        print(all_news)
        xuangu = XunguAgent()
        email_df = xuangu.run_find_symbol("\n\n".join(all_news))
        xuangu.send_res_email(email_df, "选股选股选股", table=True, toaddrs=toaddrs, dear=dear)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        logger.info(f"tenant参数：{arg1}")

        tenant_raw = os.environ.get(arg1, "")
        
        if tenant_raw:
            tenant = Tenant.model_validate_json(tenant_raw)
            dear = tenant.name
            toaddrs = tenant.toaddrs.split("|")
            exclude_symbol = tenant.exclude_symbol.split("|")
            position_symbol = tenant.position_symbol.split("|")      

            main()
        else:
            logger.error(f"未定义环境变量{arg1}")
    else:
        logger.error("未定义tenant")


