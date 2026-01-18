from agents.publicOptionAgent import PublicOptionAgent

agent = PublicOptionAgent()
agent.set_symbol("601601")
ret = agent.run("分析601601舆情数据")