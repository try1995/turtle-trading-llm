import json
from loguru import logger
from prompt import sys_investment_prompt
from .baseAgent import baseAgent
from tools import get_func_schema, save_response
from tools.all_types import EmAllagents

class InvestmentAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.tools = []
        self.name = EmAllagents.investmentAgent.name
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
    
    @save_response
    def act(self, messages):
        response = self.invork(messages)
        return response
    
    @save_response
    def run(self, question):
        logger.info(f"{self.name}：当前执行任务：{question}")
        messages = [
            {"role": "system", "content": sys_investment_prompt},
            {
                "role": "user",
                "content": self.get_date_desc()
            },
            {
                "role": "user",
                "content": question
            },
        ]
        return self.act(messages)
    