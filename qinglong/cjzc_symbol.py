# 通东方财富-财经早餐，每天6点出新闻，可以每天7点执行
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger
from datetime import datetime
from json_repair import repair_json
from agents.xuanguAgent import XunguAgent
from agents.planAgent import PlanAgent
from tools.aktools import stock_info_cjzc_em, get_trade_date


def xuangu_task():
    subject = "通东方财富-财经早餐-每日选股"

    url, cjzc_content = stock_info_cjzc_em()

    xuangu = XunguAgent()
    md = xuangu.run(cjzc_content)
    md += f"\n\n**url链接如下：**\n{url}"

    xuangu.send_res_email(md.split("```<split>```")[0], subject)

    datas_json = repair_json(md, return_objects=True)
    for data in datas_json:
        symbol = data["股票代码"]
        if data["舆情情绪"] == "极度正面" and symbol != "未提及":
            plan = PlanAgent()
            maxretry = 3
            while maxretry:
                try:
                    plan.run(f"详细分析{data["涉及公司名称"]}({symbol})行情情况，提供交易建议", human_in_loop=False)
                    plan.send_allres_email(subject=f"极度正面{data["涉及公司名称"]}({symbol})分析")
                    break
                except Exception as e:
                    logger.error(e)
                    maxretry -= 1
                            

def daily_task():
    # now = datetime.now().strftime("%Y%m%d")
    # if now not in get_trade_date():
    #     logger.info("未在交易日，跳过")
    #     return
    xuangu_task()


if __name__ == "__main__":
    daily_task()