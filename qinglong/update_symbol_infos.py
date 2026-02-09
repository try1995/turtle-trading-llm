# 一年执行一次即可
import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


import json
import requests

from dotenv import load_dotenv
from tools.sql_utils import *

load_dotenv()

url = "https://api.zhituapi.com/hs/list/all?token="+os.environ.get("ZT_TOKEN")

response = requests.get(url)

datas = response.json()

# with open("symbol","r") as f:
#     datas = json.load(f)

all_data = []
for data in datas:
    all_data.append(AStockInfos(
        symbol = data["dm"].split(".")[0],
        name = data["mc"],
        jys = data["jys"]
    ))

clear_record(AStockInfos)
add_records(all_data)
