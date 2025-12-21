from tools import *
from .baseAgent import baseAgent
from prompt import sys_report_prompt
from llm import client
from loguru import logger

class ReportAgent(baseAgent):
    def __init__(self):
        self.name = "reportAgent"
        self.tools = [stock_research_report_em, stock_research_report_markdown]
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
    
    def act(self, messages, response_message):
            final_response_stream_plan = self.act_with_tools_stepbystep(messages, response_message)
            # messages.append(
            #     {
            #         "role":"assistant",
            #         "content": final_response_stream_plan
            #     }
            # )

    
    def run(self, question):
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
        response_message = self.invork_with_tools(messages)
        self.act(messages, response_message)
                    

