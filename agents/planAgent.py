from loguru import logger
from llm import client
from copy import deepcopy
from prompt import sys_plan_prompt
from .dataAgent import DataAgent
from .reportAgent import ReportAgent
from .baseAgent import baseAgent
from .InvestmentAgent import InvestmentAgent
from json_repair import repair_json
from tools.all_types import EmAllagents


class PlanAgent:
    def __init__(self):
        self.name = EmAllagents.planAgent.name
        self.agent = [DataAgent, ReportAgent]
        self.agent_dict:dict[str, baseAgent] = {"dataAgent":DataAgent(), "reportAgent":ReportAgent()}
        self.agent_res = {}
        
    
    def invork(self, message, human_in_loop):
        messages = [
            {"role": "system", "content": sys_plan_prompt},
            {
                "role": "user",
                "content": message
            },
        ]
        stream = client.chat.completions.create(
            model="myllm:latest",
            messages=messages,
            stream=True,
        )
        plan = ""
        for event in stream:
            cur_content = event.choices[0].delta.content
            if cur_content:
                plan += cur_content
                print(cur_content, end="")
        
        if human_in_loop:
            while True:
                __messages = deepcopy(messages)
                human_input = input("\n\nneed replan? or give advice. if not, just input no\n\n")
                logger.debug(human_input)
                if human_input.strip().lower() != "no":
                    __messages.extend([
                        {
                            "role":"assistant",
                            "content": f"Previous plan - {plan}"
                        },
                        {
                            "role":"user",
                            "content":human_input
                        }]
                    )
                    stream = client.chat.completions.create(
                        model="myllm:latest",
                        messages=__messages,
                        stream=True,
                    )
                    plan = ""
                    for event in stream:
                        cur_content = event.choices[0].delta.content
                        if cur_content:
                            plan += cur_content
                            print(cur_content, end="")
                else:
                    break
        return plan
    
    def get_agent_res(self):
        res = "行情及技术指标:" + self.agent_res.get(EmAllagents.dataAgent.name, "无") + \
            "\n研报：" + self.agent_res.get(EmAllagents.reportAgent.name, "无") + \
            "\n舆情：" + self.agent_res.get(EmAllagents.publicOptionAgent.name, "无") 
        return res
                    

    def act(self, plan):
        # 这是一个pipeline
        for task in plan["subtasks"]:
            agent_name, agent_task = task['assigned_agent'], task['task_details']
            agent = self.agent_dict[agent_name]
            agent_res = agent.run(agent_task)
            self.agent_res[agent_name] = agent_res
            logger.info("*"*99)
            if agent_name == EmAllagents.investmentAgent.name:
                host_agent = InvestmentAgent()
                host_agent.run(self.get_agent_res())
        
    
    def run(self, question, human_in_loop=True):
        logger.info(f"{self.name}：当前执行任务：{question}")
        plan_raw = self.invork(question, human_in_loop)
        plan = repair_json(plan_raw, return_objects=True)
        self.act(plan)

