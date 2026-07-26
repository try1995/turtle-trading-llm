import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.sql_utils import *

from sqlalchemy import select
from tools.all_types import Tenant
from tools.daily_stock_analysis import analysis_stock

def main():
    for symbol in position_symbol:
        try:
            analysis_stock(symbol)
        except Exception as e:
            logger.error(f"分析{symbol}失败: {e}")
            continue

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


