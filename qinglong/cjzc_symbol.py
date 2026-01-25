# 通东方财富-财经早餐，每天6点出新闻，可以每天7点执行
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.xuanguAgent import XunguAgent
from tools.aktools import stock_info_cjzc_em


subject = "通东方财富-财经早餐-每日选股"

cjzc_content = stock_info_cjzc_em()

xuangu = XunguAgent()
md = xuangu.run(cjzc_content)
xuangu.send_res_email(md, subject)

