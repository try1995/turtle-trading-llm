import os
from loguru import logger
from prompt import sys_investment_prompt, sys_tool_prompt
from .baseAgent import baseAgent
from tools import get_func_schema, save_response, stock_value_em, get_cache, get_agent_res
from tools.all_types import EmAllagents


class InvestmentAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.tools = [get_agent_res]
        self.name = EmAllagents.investmentAgent.name
        self.model = os.environ.get(self.name+"Model", self.model)
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
            {"role": "system", "content": sys_investment_prompt},
            {
                "role": "user",
                "content": "\n\n".join(tool_call_res)
            }
        ]
        final_response_stream_res = self.invork(new_messages)
        return final_response_stream_res
    