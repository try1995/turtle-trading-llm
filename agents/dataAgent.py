import os
from loguru import logger
from prompt import sys_data_prompt, sys_tool_prompt
from .baseAgent import baseAgent
from tools.all_types import EmAllagents
from tools import *
from tools.langchain_tools import DATA_AGENT_TOOLS
from langchain_core.messages import SystemMessage, HumanMessage

class DataAgent(baseAgent):
    def __init__(self):
        super().__init__()
        # Legacy tool registration (backward compat with planAgent)
        self.tools = [zt_stock_hist_price, zt_stock_latest_price, zt_stock_info,
            zt_stock_kdj, zt_stock_boll, zt_stock_ma, zt_stock_macd,
            stock_individual_fund_flow,
            stock_board_industry_summary_ths,
            stock_financial_report_sina, stock_zh_growth_comparison_em,
            stock_zh_valuation_comparison_em, stock_zh_scale_comparison_em, stock_value_em]
        self.name = EmAllagents.dataAgent.name
        self.model = os.environ.get(self.name + "Model", self.model)
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__: fun for fun in self.tools}
        # LangChain tool integration
        self._langchain_tools = DATA_AGENT_TOOLS

    @save_response
    def act(self, messages, response_message):
        messages, tool_call_res = self.act_with_tools(messages, response_message)
        return tool_call_res

    @save_response
    def run(self, question):
        """Run using LangChain across 3 sub-tasks."""
        logger.info(f"{self.name}: executing task: {self.symbol_name} {question}")
        self._init_langchain()
        all_data = ""
        sub_task_names = ["基本面数据", "技术面数据", "同行对比"]

        for task_name in sub_task_names:
            logger.info(f"{self.name}: executing sub-task: {self.symbol_name} {task_name}")

            # Phase 1: Tool data collection per sub-task
            phase1_messages = [
                SystemMessage(content=sys_tool_prompt),
                HumanMessage(content=self.get_date_desc()[0]),
                HumanMessage(content=f"{task_name}分析：{self.symbol_name}({self.symbol})"),
            ]
            ai_msg = self._invoke_llm_with_tools(phase1_messages)
            tool_msgs = self._execute_tool_calls(ai_msg)
            res_str = "\n\n".join(m.content for m in tool_msgs)

            # Phase 2: Analysis
            phase2_messages = [
                SystemMessage(content=sys_data_prompt),
                HumanMessage(
                    content=f"基于用户提供的数据分析：{self.symbol_name}({self.symbol})"
                            f"{task_name}\n用户提供数据如下：{res_str}"
                ),
            ]
            sub_result = self._invoke_llm(phase2_messages)
            all_data += "\n\n**" + task_name + "**\n\n" + sub_result

        return all_data

    def get_analysis_prompt(self) -> str:
        return sys_data_prompt

    def set_backtest(self, cur_date):
        self.backtest = True
        self.backtest_date = cur_date
        # Remove real-time data tool during backtesting
        if stock_individual_info_em in self.tools:
            self.tools.remove(stock_individual_info_em)
