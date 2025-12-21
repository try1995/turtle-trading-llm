from agents.dataAgent import DataAgent

agent = DataAgent()
ret = agent.run("分析601601最近三个月的行情情况")
print(ret)