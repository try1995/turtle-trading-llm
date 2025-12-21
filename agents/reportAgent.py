from tools import *
from .baseAgent import baseAgent
from prompt import sys_report_prompt
from llm import client
from loguru import logger

class reportAgent(baseAgent):
    def __init__(self):
        self.tools = [stock_research_report_em, stock_research_report_markdown]
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
        
    def invork(self, message, max_step=10):
            messages = [
                {"role": "system", "content": sys_report_prompt},
                {
                    "role": "user",
                    "content": get_date_desc()
                },
                {
                    "role": "user",
                    "content": message
                },
            ]

            # self.invork_with_tools(messages, max_step)
            self.invork_with_tools_stepbystep(messages, max_step=max_step)
            