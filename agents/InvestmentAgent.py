import os
from loguru import logger
from prompt import sys_investment_prompt, sys_tool_prompt
from .baseAgent import baseAgent
from tools import get_func_schema, save_response, get_agent_res
from tools.all_types import EmAllagents
from tools.langchain_tools import INVESTMENT_AGENT_TOOLS
from langchain_core.messages import SystemMessage, HumanMessage


class InvestmentAgent(baseAgent):
    def __init__(self):
        super().__init__()
        # Legacy tool registration (backward compat)
        self.tools = [get_agent_res]
        self.name = EmAllagents.investmentAgent.name
        self.model = os.environ.get(self.name + "Model", self.model)
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__: fun for fun in self.tools}
        # LangChain tool integration
        self._langchain_tools = INVESTMENT_AGENT_TOOLS

    @save_response
    def act(self, messages, response_message):
        messages, tool_call_res = self.act_with_tools(messages, response_message)
        return tool_call_res

    @save_response
    def run(self, question):
        """Run using LangChain standard two-phase agent loop."""
        logger.info(f"{self.name}: executing task: {self.symbol_name} {question}")
        self._init_langchain()

        # Phase 1: Tool data collection (reads other agents' cached results)
        phase1_messages = [
            SystemMessage(content=sys_tool_prompt),
            HumanMessage(content=self.get_date_desc()[0]),
            HumanMessage(content=f"{self.symbol_name}({self.symbol})\n\n{question}"),
        ]
        ai_msg = self._invoke_llm_with_tools(phase1_messages)
        tool_results_list = self._execute_tool_calls(ai_msg)
        res_str = "\n\n".join(r[2] for r in tool_results_list)

        # Phase 2: Investment analysis
        phase2_messages = [
            SystemMessage(content=sys_investment_prompt),
            HumanMessage(content=res_str),
        ]
        return self._invoke_llm(phase2_messages)

    def get_analysis_prompt(self) -> str:
        return sys_investment_prompt
