import os
from .baseAgent import baseAgent
from prompt import sys_report_prompt, sys_tool_prompt
from loguru import logger
from tools.all_types import EmAllagents
from tools import stock_research_report_ex, get_func_schema, save_response, save_func_response, get_func_response
from tools.langchain_tools import REPORT_AGENT_TOOLS
from langchain_core.messages import SystemMessage, HumanMessage

class ReportAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.name = EmAllagents.reportAgent.name
        self.model = os.environ.get(self.name + "Model", self.model)
        # Legacy tool registration (backward compat)
        self.tools = [stock_research_report_ex]
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__: fun for fun in self.tools}
        # LangChain tool integration
        self._langchain_tools = REPORT_AGENT_TOOLS

    @save_response
    def act(self, messages, response_message):
        messages, tool_call_res = self.act_with_tools(messages, response_message)
        return tool_call_res

    @save_response
    def run(self, question):
        """Run using LangChain with MD5-based result caching."""
        logger.info(f"{self.name}: executing task: {self.symbol_name} {question}")
        self._init_langchain()

        # Phase 1: Tool data collection
        phase1_messages = [
            SystemMessage(content=sys_tool_prompt),
            HumanMessage(content=self.get_date_desc()[0]),
            HumanMessage(content=f"研报分析：{self.symbol_name}({self.symbol})"),
        ]
        ai_msg = self._invoke_llm_with_tools(phase1_messages)
        tool_results_list = self._execute_tool_calls(ai_msg)
        res_str = "\n\n".join(r[2] for r in tool_results_list)

        # Check MD5-based cache first
        final_response = get_func_response(res_str)
        if not final_response:
            # Phase 2: Analysis
            phase2_messages = [
                SystemMessage(content=sys_report_prompt),
                HumanMessage(content=res_str),
            ]
            final_response = self._invoke_llm(phase2_messages)
            save_func_response(res_str, final_response)

        return final_response

    def get_analysis_prompt(self) -> str:
        return sys_report_prompt
