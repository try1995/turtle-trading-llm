import json
from loguru import logger
from prompt import sys_investment_prompt
from .baseAgent import baseAgent
from tools import get_func_schema, get_date_desc
from tools.all_types import EmAllagents

class InvestmentAgent(baseAgent):
    def __init__(self):
        self.tools = []
        self.name = EmAllagents.investmentAgent.name
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
    
    def act(self, messages):
        self.invork(messages)
    
    def run(self, question):
        logger.info(f"{self.name}：当前执行任务：{question}")
        messages = [
            {"role": "system", "content": sys_investment_prompt},
            {
                "role": "user",
                "content": get_date_desc()
            },
            {
                "role": "user",
                "content": question
            },
        ]
        self.act(messages)
    