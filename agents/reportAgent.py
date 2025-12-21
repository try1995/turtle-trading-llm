from tools import *
from .baseAgent import baseAgent
from prompt import sys_report_prompt
from loguru import logger
from tools.all_types import EmAllagents

class ReportAgent(baseAgent):
    def __init__(self, max_step=10):
        self.name = EmAllagents.reportAgent.name
        self.max_step = max_step
        self.tools = [stock_research_report_em, stock_research_report_markdown]
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
    
    def act(self, messages, response_message):
        messages = self.act_with_tools_stepbystep(messages, response_message)
        return messages

    
    def run(self, question):
        logger.info(f"{self.name}：当前执行任务：{question}")
        messages = [
            {"role": "system", "content": sys_report_prompt},
            {
                "role": "user",
                "content": get_date_desc()
            },
            {
                "role": "user",
                "content": question
            },
        ]
        max_step = self.max_step
        while max_step:
            response_message = self.invork_with_tools(messages)
            finish, messages = self.act(messages, response_message)
            max_step -=1
            if finish:
                break
        final_response_stream_res = self.invork(messages)
        return final_response_stream_res
                    

