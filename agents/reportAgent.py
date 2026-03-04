import os
from .baseAgent import baseAgent
from prompt import sys_report_prompt, sys_tool_prompt
from loguru import logger
from tools.all_types import EmAllagents
from tools import stock_research_report_ex, get_func_schema, save_response, save_func_response, get_func_response

class ReportAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.name = EmAllagents.reportAgent.name
        self.model = os.environ.get(self.name+"Model", self.model)
        self.tools = [stock_research_report_ex]
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
    
    @save_response
    def act(self, messages, response_message):
        messages, tool_call_res = self.act_with_tools(messages, response_message)
        return tool_call_res 

    @save_response
    def run(self, question):
        logger.info(f"{self.name}：当前执行任务：{self.symbol_name} {question}")
        messages = [
            {"role": "system", "content": sys_tool_prompt},
            {
                "role": "user",
                "content": self.get_date_desc()[0]
            },
            {
                "role": "user",
                "content": f"研报分析：{self.symbol_name}({self.symbol})"
            },
        ]
        response_message = self.invork_with_tools(messages)
        tool_call_res = self.act(messages, response_message)

        new_messages=[
            {"role": "system", "content": sys_report_prompt},
            {
                "role": "user",
                "content": "\n\n".join(tool_call_res)
            }
        ]
        
        final_response_stream_res = get_func_response("\n\n".join(tool_call_res))
        if not final_response_stream_res:
            final_response_stream_res = self.invork(new_messages)
            save_func_response("\n\n".join(tool_call_res), final_response_stream_res)
        return final_response_stream_res
                    

