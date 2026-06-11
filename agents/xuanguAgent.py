import os
from loguru import logger
from prompt import sys_news_analysis_prompt, sys_xuangu_prompt
from .baseAgent import baseAgent
from tools.all_types import EmAllagents
from tools import *
from langchain_core.messages import SystemMessage, HumanMessage


class XunguAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.tools = []
        self.name = EmAllagents.xuanguAgent.name
        self.model = os.environ.get(self.name + "Model", self.model)
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__: fun for fun in self.tools}
        # No tools for this agent
        self._langchain_tools = []

    @save_response
    def act(self, messages, response_message):
        messages, tool_call_res = self.act_with_tools(messages, response_message)
        return tool_call_res

    @save_response
    def run(self, question):
        """Run news sentiment analysis via LangChain streaming."""
        logger.debug(f"current model: {self.model}")
        logger.info(f"{self.name}: executing task: xuangu")
        self._init_langchain()
        messages = [
            SystemMessage(content=sys_news_analysis_prompt),
            HumanMessage(content=f"用户提供数据如下：{question}"),
        ]
        return self._invoke_llm(messages)

    @save_response
    def run_find_symbol(self, question):
        """Run stock screening via LangChain streaming."""
        logger.debug(f"current model: {self.model}")
        logger.info(f"{self.name}: executing task: xuangu (find symbol)")
        self._init_langchain()
        messages = [
            SystemMessage(content=sys_xuangu_prompt),
            HumanMessage(content=f"用户提供数据如下：{question}"),
        ]
        return self._invoke_llm(messages)
