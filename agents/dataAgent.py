import json
from llm import client
from loguru import logger
from prompt import sys_data_prompt
from .baseAgent import baseAgent
from tools.all_types import EmAllagents
from tools import stock_zh_a_hist, get_func_schema, get_date_desc, get_indicators

class DataAgent(baseAgent):
    def __init__(self):
        self.tools = [stock_zh_a_hist, get_indicators]
        self.name = EmAllagents.dataAgent.name
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
    
    
    def act(self, messages, response_message):
        messages, tool_call_res = self.act_with_tools(messages, response_message)
        return tool_call_res

    
    def run(self, question):
        logger.info(f"{self.name}：当前执行任务：{question}")
        messages = [
            {"role": "system", "content": sys_data_prompt},
            {
                "role": "user",
                "content": get_date_desc()
            },
            {
                "role": "user",
                "content": question
            },
        ]
        response_message = self.invork_with_tools(messages)
        tool_call_res = self.act(messages, response_message)
        new_messages=[
            {"role": "system", "content": sys_data_prompt},
            {
                "role": "user",
                "content": "\n\n".join(tool_call_res)
            }
        ]
        final_response_stream_res = self.invork(new_messages)
        return final_response_stream_res
                    

