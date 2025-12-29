import os
from loguru import logger
from tools import get_trade_date
from agents.planAgent import PlanAgent
from json_repair import repair_json

symbol = "601601"
backtest_start_date = "20250101"
backtest_end_date = "20251228"

def get_last_invest(date):
    file_path = f"{os.getcwd()}/.pyturtlecache/{date}/investmentAgent_run"
    if not os.path.exists(file_path):
        logger.warning(f"{date}历史数据不存在")
        return "", {}
    with open(file_path, "r") as f:
        invest_suggestion = f.read()
    invest_json = repair_json(invest_suggestion, return_objects=True)
    logger.info(f"{date}\n{invest_json}")
    return invest_suggestion, invest_json

def main():
    # 获取交易日历
    trade_dates = get_trade_date(backtest_start_date, backtest_end_date)
    logger.info(f"共获取到{len(trade_dates)}个交易日")
    trade_date_brefore = ""
    for trade_date in trade_dates:
        logger.info(f"当前交易日：{trade_date}")
        plan = PlanAgent()
        # 获取上一个交易日的建议，作为这个交易日的参考
        if trade_date_brefore:
            invest_suggestion, _ = get_last_invest(trade_date_brefore)
            plan.set_backtest(trade_date, invest_suggestion)
        else:
            plan.set_backtest(trade_date)
        trade_date_brefore = trade_date
        plan.run(f"分析{symbol}行情情况, 提供交易建议", human_in_loop=False)


if __name__ == "__main__":
    main()