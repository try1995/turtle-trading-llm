import json
from llm import client
from loguru import logger
from prompt import sys_data_prompt
from .baseAgent import baseAgent
from tools.all_types import EmAllagents
from tools import *
from report.dataReport import data_report, Paragraph1, DataReport
from json_repair import repair_json


class DataAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.tools = [stock_zh_a_hist, get_indicators, stock_individual_fund_flow, stock_board_industry_summary_ths, stock_individual_info_em, stock_financial_report_sina]
        self.name = EmAllagents.dataAgent.name
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
    
    @save_response
    def act(self, messages, response_message):
        messages, tool_call_res = self.act_with_tools(messages, response_message)
        return tool_call_res

    
    @save_response
    def run(self, question):
        logger.info(f"{self.name}：当前执行任务：{question}")
        all_data = ""
        sub_task = ["基本面数据","技术面数据","行业与竞争数据"]
        for task in sub_task:
            logger.info(f"{self.name}：当前执行任务：{self.symbol} {task}")
            messages = [
                {"role": "system", "content": sys_data_prompt},
                {
                    "role": "user",
                    "content": self.get_date_desc()[0]
                },
                {
                    "role": "user",
                    "content": f"分析：{self.symbol}{task}"
                }
            ]
            response_message = self.invork_with_tools(messages)
            tool_call_res = self.act(messages, response_message)
            new_messages=[
                {"role": "system", "content": sys_data_prompt},
                {
                    "role": "user",
                    "content": "\n\n".join(tool_call_res)
                },
                {
                    "role": "user",
                    "content": f"分析：{self.symbol}{task}"
                }
            ]
            response_stream_res = self.invork(new_messages)
            all_data += '\n\n**' + task + '**\n\n' + response_stream_res
        return all_data
                    
    def set_backtest(self, cur_date):
        self.backtest = True
        self.backtest_date = cur_date
        # 这个查询回来的是实时信息
        self.tools.remove(stock_individual_info_em)
