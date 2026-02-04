from agents.planAgent import PlanAgent

plan = PlanAgent()
ret = plan.run("详细分析603259，提供交易建议", use_cache=False)
plan.send_allres_email(subject="603259")