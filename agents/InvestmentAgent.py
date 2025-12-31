from loguru import logger
from prompt import sys_investment_prompt
from .baseAgent import baseAgent
from tools import get_func_schema, save_response, stock_value_em, get_cache
from tools.all_types import EmAllagents
from typing import Annotated


def get_agent_res(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"]
):
    """
    描述：获取agent的运行结果，包括dataAgent, reportAgent
    """
    data_agent_res = get_cache(cur_date, symbol, EmAllagents.dataAgent.name)
    report_agent_res = get_cache(cur_date, symbol, EmAllagents.reportAgent.name)
    public_agent_res = get_cache(cur_date, symbol, EmAllagents.publicOptionAgent.name)
    
    res = "行情及技术指标：" + data_agent_res + \
        "\n\n研报：" + report_agent_res + \
        "\n\n舆情：" + public_agent_res
    return res


class InvestmentAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.tools = [stock_value_em, get_agent_res]
        self.name = EmAllagents.investmentAgent.name
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
            {"role": "system", "content": sys_investment_prompt},
            {
                "role": "user",
                "content": self.get_date_desc()
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
    