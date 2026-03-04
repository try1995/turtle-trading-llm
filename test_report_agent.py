from agents.reportAgent import ReportAgent

agent = ReportAgent()
agent.set_symbol("601601","太保科技")
ret = agent.run("分析601601研报数据")
print(ret)