from agents.planAgent import PlanAgent

plan = PlanAgent()
ret = plan.run("详细分析603259，提供交易建议")
plan.send_allres_email(subject="测试")