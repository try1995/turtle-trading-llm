from agents.reportAgent import ReportAgent

agent = ReportAgent()
agent.set_symbol("601601")
ret = agent.run("分析601601研报数据")
print(ret)