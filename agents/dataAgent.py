import json
from llm import client
from loguru import logger
from prompt import sys_data_prompt
from .baseAgent import baseAgent
from tools import stock_zh_a_hist, get_func_schema, get_date_desc

class DataAgent(baseAgent):
    def __init__(self):
        self.tools = [stock_zh_a_hist]
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
    

    def invork(self, message, max_step=10):
        messages = [
            {"role": "system", "content": sys_data_prompt},
            {
                "role": "user",
                "content": get_date_desc()
            },
            {
                "role": "user",
                "content": message
            },
        ]

        self.invork_with_tools(messages, max_step)
                    

