import json
from llm import client
from loguru import logger
from prompt import sys_xuangu_prompt
from .baseAgent import baseAgent
from tools.all_types import EmAllagents
from tools import *


class XunguAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.tools = []
        self.name = EmAllagents.xuanguAgent.name
        self.model = os.environ.get(self.name+"Model", self.model)
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
    
    @save_response
    def act(self, messages, response_message):
        messages, tool_call_res = self.act_with_tools(messages, response_message)
        return tool_call_res

    
    @save_response
    def run(self, question):
        logger.info(f"{self.name}：当前执行任务：xuangu")
        new_messages=[
            {"role": "system", "content": sys_xuangu_prompt},
            {
                "role": "user",
                "content": f"用户提供数据如下：{question}"
            }
        ]
        response_stream_res = self.invork(new_messages)
        return response_stream_res

