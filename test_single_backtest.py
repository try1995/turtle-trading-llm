from agents.planAgent import PlanAgent
from backtest import get_last_invest

date = "20251203"
plan = PlanAgent()
plan.set_backtest(date, last_invest_suggestion=get_last_invest("20250704")[0])
plan.run("分析601601行情情况, 提供交易建议", human_in_loop=False)