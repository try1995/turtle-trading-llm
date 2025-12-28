from agents.planAgent import PlanAgent

plan = PlanAgent()
plan.set_backtest("20251202")
plan.run("结合研报数据，分析601601行情情况,是否可以买入", human_in_loop=True)