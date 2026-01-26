import os
from .baseAgent import baseAgent
from prompt import sys_option_prompt, sys_tool_prompt
from loguru import logger
from tools.all_types import EmAllagents
from tools import get_func_schema, save_response, stock_news_em, symbol_tavily_search


class PublicOptionAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.name = EmAllagents.publicOptionAgent.name
        self.model = os.environ.get(self.name+"Model", self.model)
        self.tools = [stock_news_em, symbol_tavily_search]
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
    
    @save_response
    def act(self, messages, response_message):
        messages, tool_call_res = self.act_with_tools(messages, response_message)
        return tool_call_res
    
    @save_response
    def run(self, question):
        logger.info(f"{self.name}：当前执行任务：{question}")
        messages = [
            {"role": "system", "content": sys_tool_prompt},
            {
                "role": "user",
                "content": self.get_date_desc()[0]
            },
            {
                "role": "user",
                "content": question
            },
        ]
        response_message = self.invork_with_tools(messages)
        tool_call_res = self.act(messages, response_message)
        new_messages=[
            {"role": "system", "content": sys_option_prompt},
            {
                "role": "user",
                "content": "\n\n".join(tool_call_res)
            }
        ]
        final_response_stream_res = self.invork(new_messages)
        return final_response_stream_res
    