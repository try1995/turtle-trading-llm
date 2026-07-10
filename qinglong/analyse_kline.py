# 每日飙升榜选股，可以每周跑，也可以每天跑
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import akshare as ak
import pandas as pd
import pandas as pd
from tools import get_trade_date, get_market
from datetime import datetime
from tools.all_types import Tenant

from agents.vlAgent import VlAgent
from tools.base_tool import push_server_jio
from loguru import logger
from tools.daily_stock_analysis import analysis_stock

logger.remove()                                     # 去掉默认全局配置
logger.add(sys.stderr, level="INFO") 


# 热榜选股
def analysis_task():
    vl_agent = VlAgent()
    for symbol in position_symbol:
        try:
            vl_agent.set_symbol(symbol, "")
            md = vl_agent.run(f"分析{symbol}")
            symbol = get_market(symbol) + symbol
            k_line = (f"![{symbol}]"
                    f"(http://image.sinajs.cn/newchart/min/n/{symbol}.gif "
                    f"'{symbol}')")
            md = k_line + "\n\n" + md
            if not push_server_jio(f"持仓盘中分析-{symbol}", md):
                vl_agent.send_res_email(md, subject=f"持仓盘中分析-{symbol}", table=True, toaddrs=toaddrs, dear=dear)
            analysis_stock(symbol)
        except Exception as e:
            logger.error(f"分析{symbol}失败: {e}")
            continue

def daily_task():
    now = datetime.now().strftime("%Y%m%d")
    if now not in get_trade_date():
        logger.info("未在交易日，跳过")
        return
    try:
        analysis_task()
    except Exception as e:
        logger.error(f"daily_task执行失败: {e}")
    
    
if __name__ == "__main__":
    # python analyse_kline.py '{"name":"汤总","toaddrs":"1635341612@qq.com","exclude_symbol":"000001","position_symbol":"601601"}'
    # 判断是否传入参数
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

            daily_task()
        else:
            logger.error(f"未定义环境变量{arg1}")
    else:
        logger.error("未定义tenant")
