from agents.dataAgent import DataAgent

agent = DataAgent()
agent.set_symbol("601601")
ret = agent.run("综合分析601601")
print(ret)