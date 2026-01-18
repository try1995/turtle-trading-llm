from agents.planAgent import PlanAgent

plan = PlanAgent()
plan.set_symbol("603259")
ret = plan.run("详细分析603259，提供交易建议")
plan.send_allres_email(subject="603259")