from loguru import logger
from llm import client
from copy import deepcopy
from enum import Enum
from prompt import sys_plan_prompt
from .dataAgent import DataAgent
from .reportAgent import ReportAgent
from .baseAgent import baseAgent
from json_repair import repair_json


class allagents(Enum):
    search_agent = 1
    

class PlanAgent:
    def __init__(self):
        self.name = "planAgent"
        self.agent = [DataAgent, ReportAgent]
        self.agent_dict:dict[str, baseAgent] = {"dataAgent":DataAgent(), "reportAgent":ReportAgent()}
        
    
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
                    

    def act(self, plan):
        # 这是一个pipeline
        logger.info(f"当前主要任务是：{plan['main_task']}")
        for task in plan["subtasks"]:
            logger.info(f"task['assigned_agent']：当前执行子任务：{task['task_details']}")
            agent = self.agent_dict[task["assigned_agent"]]
            agent.run(task["task_details"])
        
    
    def run(self, question, human_in_loop=True):
        plan_raw = self.invork(question, human_in_loop)
        plan = repair_json(plan_raw, return_objects=True)
        self.act(plan)

