# 一年执行一次即可
import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


import json
import config
from tools.aktools import get_trade_date

ret = get_trade_date(use_cache=False)
with open(os.path.join(config.cache_dir, "tradeData"), "w") as f:
    f.write(json.dumps(ret, ensure_ascii=False, indent=4))