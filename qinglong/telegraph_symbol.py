
# 财联社-电报-重要-实时推送，建议每3分钟一次，晚上20分钟一次
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger
from json_repair import repair_json
from agents.xuanguAgent import XunguAgent
from agents.planAgent import PlanAgent
from tools.aktools import stock_info_global_cls
from tools.base_tool import push_server_jio
from config import cache_dir
import json

def xuangu_task():
    subject = "财联社-电报-重要-实时推送"
    cache_file_path = os.path.join(cache_dir, "财联社_电报数据")
    telegraph_content_raw = stock_info_global_cls()
    telegraph_content = json.loads(telegraph_content_raw)

    val_content = []
    if telegraph_content:
        if os.path.exists(cache_file_path):
            with open(cache_file_path,"r") as f:
                cache_data = json.load(f)
            if cache_data == telegraph_content:
                logger.info("重复数据不推送！")
                return
            for value in telegraph_content:
                if value not in cache_data:
                    val_content.append(value)
        else:
            val_content = telegraph_content
        if val_content:
            xuangu = XunguAgent()
            md = xuangu.run(json.dumps(val_content))
            xuangu.send_res_email(md.split("```<split>```")[0], subject)

            datas_json = repair_json(md, return_objects=True)
            for data in datas_json:
                symbol = data["股票代码"]
                if data["舆情情绪"] == "极度正面" and symbol != "未提及":
                    try:
                        push_server_jio(f"极度正面{symbol}出现了！", desp=json.dumps(data, ensure_ascii=False))
                    except Exception as e:
                        logger.error(e)
                    plan = PlanAgent()
                    maxretry = 3
                    while maxretry:
                        try:
                            plan.run(f"详细分析{data['涉及公司名称']}({symbol})行情情况，提供交易建议", human_in_loop=False)
                            plan.send_allres_email(subject=f"极度正面{data['涉及公司名称']}({symbol})分析")
                            break
                        except Exception as e:
                            logger.error(e)
                            maxretry -= 1
            
            with open(cache_file_path, "w") as f:
                f.write(telegraph_content_raw)
        else:
            logger.info("没有新东西")


if __name__ == "__main__":
    xuangu_task()