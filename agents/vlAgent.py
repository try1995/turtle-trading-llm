import os
import base64
import requests as req
from loguru import logger
from prompt import sys_tool_prompt, sys_vl_prompt
from .baseAgent import baseAgent
from tools.all_types import EmAllagents
from tools import *
from tools.langchain_tools import VL_AGENT_TOOLS
from langchain_core.messages import SystemMessage, HumanMessage


def url_to_base64(image_url):
    """Convert image URL to base64 data URI."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
    }
    response = req.get(image_url, headers=headers, timeout=30)
    response.raise_for_status()

    content_type = response.headers.get('content-type', 'image/jpeg')
    base64_data = base64.b64encode(response.content).decode('utf-8')

    return f"data:{content_type};base64,{base64_data}"


class VlAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.tools = [zt_stock_latest_price, zt_stock_hist_price]
        self.name = EmAllagents.vlAgent.name
        self.model = os.environ.get(self.name + "Model", self.model)
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__: fun for fun in self.tools}
        # LangChain tool integration
        self._langchain_tools = VL_AGENT_TOOLS

    def _init_langchain(self):
        """Override to use VL-specific model."""
        if self._llm is None:
            from llm_factory import create_chat_model, create_tool_model, create_vl_model
            self._tool_llm = create_tool_model(self.name)
            if self._langchain_tools:
                self._llm_with_tools = self._tool_llm.bind_tools(self._langchain_tools)
            else:
                self._llm_with_tools = None
            # VL agent uses a vision-capable model for Phase 2
            self._llm = create_vl_model(self.name)

    @save_response
    def act(self, messages, response_message):
        messages, tool_call_res = self.act_with_tools(messages, response_message)
        return tool_call_res

    @save_response
    def run(self, question):
        """Run using LangChain with multimodal image analysis."""
        logger.info(f"{self.name}: executing task: {self.symbol_name} {question}")
        self._init_langchain()

        # Phase 1: Tool data collection
        phase1_messages = [
            SystemMessage(content=sys_tool_prompt),
            HumanMessage(content=self.get_date_desc()[0]),
            HumanMessage(content=f"{question}：{self.symbol_name}({self.symbol})"),
        ]
        ai_msg = self._invoke_llm_with_tools(phase1_messages)
        tool_results_list = self._execute_tool_calls(ai_msg)
        res_str = "\n\n".join(r[2] for r in tool_results_list)

        # Phase 2: Multimodal analysis with K-line chart images
        market = get_market(self.symbol)
        symbol_full = market + self.symbol

        # Build multimodal message with base64-encoded charts
        user_content = [
            {"type": "image_url",
             "image_url": {"url": url_to_base64(
                 f"http://image.sinajs.cn/newchart/min/n/{symbol_full}.gif")}},
            {"type": "image_url",
             "image_url": {"url": url_to_base64(
                 f"http://image.sinajs.cn/newchart/daily/n/{symbol_full}.gif")}},
            {"type": "image_url",
             "image_url": {"url": url_to_base64(
                 f"http://image.sinajs.cn/newchart/weekly/n/{symbol_full}.gif")}},
            {"type": "text",
             "text": f"{self.get_date_desc()[0]}, "
                     f"根据用户上传的图片信息，分析股票的趋势信息。\n\n"
                     f"参考信息如下：{res_str}"},
        ]

        phase2_messages = [
            SystemMessage(content=sys_vl_prompt),
            HumanMessage(content=user_content),
        ]
        return self._invoke_llm(phase2_messages)

    def get_analysis_prompt(self) -> str:
        return sys_vl_prompt
