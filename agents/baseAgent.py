import os
import json
from time import sleep
from json_repair import repair_json
from llm import client  # Legacy — retained for backward compat
from loguru import logger
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from markdown import markdown
from tools.send_email import send_message
from tools.aktools import get_trade_date
from tools.langchain_tools import get_langchain_tools_for_agent
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from dotenv import load_dotenv

load_dotenv()

class baseAgent(ABC):
    def __init__(self):
        self.name = ""
        self.tools = []
        self.tools_regist = []
        self.tools_dict = {}
        # Backtesting flags
        self.backtest = False
        self.backtest_date = ""
        # Stock symbol
        self.symbol = ""
        self.symbol_name = ""
        # Model configuration
        self.model = os.environ.get("model")
        self.tool_call_mdoel = os.environ.get("toolCallModel", self.model)
        # LangChain LLM instances — initialized lazily by subclasses
        self._llm = None
        self._tool_llm = None
        self._llm_with_tools = None
        self._langchain_tools = []

    @abstractmethod
    def act(self, *args, **kwargs):
        pass

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    # =========================================================================
    # Legacy LLM invocation methods (backward compatible)
    # =========================================================================

    def invork(self, messages, **kwargs):
        """Legacy streaming invocation using raw OpenAI client."""
        final_response_stream = client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=0.1,
            **kwargs
        )

        final_response_stream_res = ""
        for event in final_response_stream:
            cur_content = event.choices[0].delta.content
            if cur_content:
                final_response_stream_res += cur_content
                print(cur_content, end="")

        return final_response_stream_res

    def invork_with_tools(self, messages):
        """Legacy tool-calling invocation using raw OpenAI client."""
        response = client.chat.completions.create(
            model=self.tool_call_mdoel,
            messages=messages,
            tools=self.tools_regist,
            tool_choice="auto"
        )
        response_message = response.choices[0].message

        return response_message

    # =========================================================================
    # LangChain-based LLM invocation methods
    # =========================================================================

    def _init_langchain(self):
        """Initialize LangChain LLM instances on first use."""
        if self._llm is None:
            from llm_factory import create_chat_model, create_tool_model
            self._llm = create_chat_model(self.name)
            self._tool_llm = create_tool_model(self.name)
            self._langchain_tools = get_langchain_tools_for_agent(self.name)
            if self._langchain_tools:
                self._llm_with_tools = self._tool_llm.bind_tools(self._langchain_tools)
            else:
                self._llm_with_tools = None

    def _invoke_llm(self, messages: list) -> str:
        """Stream LangChain messages and return concatenated text."""
        self._init_langchain()
        response = self._llm.stream(messages)
        result = ""
        for chunk in response:
            if chunk.content:
                result += chunk.content
                print(chunk.content, end="")
        return result

    def _invoke_llm_with_tools(self, messages: list):
        """
        Invoke LLM with tool binding and return the LangChain AIMessage.
        """
        self._init_langchain()
        if self._llm_with_tools is None:
            raise ValueError(f"Agent {self.name} has no tools bound. "
                             "Set self._langchain_tools before calling.")
        return self._llm_with_tools.invoke(messages)

    def _execute_tool_call(self, tool_call) -> str:
        """
        Execute a single LangChain tool call and return the result string.

        Handles JSON argument parsing with json_repair fallback, and
        retries up to 3 times on failure.
        """
        func_name = tool_call["name"]
        func_args_raw = tool_call["args"]
        max_retry = 3

        # Parse arguments — tool_call["args"] is already a dict in LangChain,
        # but keep robustness for any string-formatted args
        if isinstance(func_args_raw, str):
            try:
                function_args = json.loads(func_args_raw)
            except Exception:
                logger.debug(func_args_raw)
                logger.info("executing repair_json")
                function_args = repair_json(func_args_raw, return_objects=True)
        else:
            function_args = func_args_raw

        # Find the LangChain tool object
        langchain_tool = None
        for t in self._langchain_tools:
            if t.name == func_name:
                langchain_tool = t
                break

        if langchain_tool is None:
            logger.error(f"Tool not found: {func_name}")
            return "工具未找到"

        # Get the label from the tool's description (first line)
        label = (langchain_tool.description or "").splitlines()[0].strip()
        if not label:
            label = func_name

        logger.info(
            f"Executing tool: {func_name}\n"
            f"Parameters: {json.dumps(function_args, ensure_ascii=False)}\n"
        )

        while max_retry:
            try:
                response = langchain_tool.invoke(function_args)
                # Unwrap if langchain tool returned a Content str
                if hasattr(response, 'content'):
                    response = response.content
            except Exception as e:
                max_retry -= 1
                sleep(3)
                if max_retry == 0:
                    logger.error(f"Tool execution failed: {e}")
                    response = "未获得"
            else:
                break

        logger.debug(f"Tool result: {str(response)[:500]}...")
        return label + "\n:" + str(response)

    def _execute_tool_calls(self, ai_message) -> list:
        """
        Execute all tool calls from a LangChain AIMessage.

        Returns list of (tool_call_id, name, result_string) tuples.
        """
        results = []
        for tool_call in ai_message.tool_calls:
            result = self._execute_tool_call(tool_call)
            results.append((tool_call["id"], tool_call["name"], result))
        return results

    def _execute_agent_loop(
        self,
        question: str,
        analysis_prompt: str,
        context_extra: str = ""
    ) -> str:
        """
        Execute the standard two-phase agent loop using LangChain.

        Phase 1: Tool data collection — LLM decides which tools to call,
                 execute them, and collect results.
        Phase 2: Analysis — LLM analyzes tool results with agent-specific prompt.

        Args:
            question: The user's question or task description.
            analysis_prompt: The role-specific system prompt for Phase 2.
            context_extra: Extra context to append to the tool-phase user message.

        Returns:
            The final streaming LLM analysis text.
        """
        from prompt import sys_tool_prompt

        self._init_langchain()

        # ---- Phase 1: Tool data collection ----
        phase1_messages = [
            SystemMessage(content=sys_tool_prompt),
            HumanMessage(content=self.get_date_desc()[0]),
            HumanMessage(content=f"{question}：{self.symbol_name}({self.symbol})"
                         + (f"\n\n{context_extra}" if context_extra else "")),
        ]

        if self._langchain_tools:
            ai_msg = self._invoke_llm_with_tools(phase1_messages)
            tool_results = self._execute_tool_calls(ai_msg)
            res_str = "\n\n".join(r[2] for r in tool_results)
        else:
            res_str = ""

        # ---- Phase 2: Analysis ----
        phase2_messages = [
            SystemMessage(content=analysis_prompt),
            HumanMessage(
                content=f"基于用户提供的数据分析：{self.symbol_name}({self.symbol})\n"
                        f"用户提供数据如下：{res_str}"
            ),
        ]

        return self._invoke_llm(phase2_messages)

    # =========================================================================
    # Legacy tool execution methods (backward compatible)
    # =========================================================================

    def exec_tools(self, fun, tool_call, max_retry=3):
        try:
            function_args = json.loads(tool_call.function.arguments)
        except Exception as e:
            logger.error(e)
            logger.debug(tool_call.function.arguments)
            logger.info("executing repair_json")
            function_args = repair_json(tool_call.function.arguments, return_objects=True)
        logger.info(f"current function description: {fun.__doc__.strip().splitlines()[0]}\n\
                    executing function: {tool_call.function.name}\n\
                    function args: {tool_call.function.arguments}\n")
        while max_retry:
            try:
                response = fun(**function_args)
            except Exception as e:
                max_retry -= 1
                sleep(3)
                if max_retry == 0:
                    logger.error(f"method execution failed: {e}, please check")
                    response = "未获得"
            else:
                break
        logger.debug(f"execution result: {response[:500]}...")
        response = fun.__doc__.strip().splitlines()[0] + "\n:" + response
        return response

    def act_with_tools(self, messages: list, response_message):
        tool_call_res = []
        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                fun = self.tools_dict.get(tool_call.function.name)
                if fun:
                    response = self.exec_tools(fun, tool_call)
                    tool_call_res.append(response)
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fun.__name__,
                        "content": response,
                    })
                else:
                    logger.error(f"error fun name from model: {fun.__name__}")
        else:
            logger.info("No tool calls were made by the model.")

        return messages, tool_call_res

    def act_with_tools_stepbystep(self, messages, response_message):
        if response_message.tool_calls:
            if len(response_message.tool_calls) > 1:
                response_message.tool_calls = [response_message.tool_calls[0]]
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                fun = self.tools_dict.get(tool_call.function.name)
                if fun:
                    response = self.exec_tools(fun, tool_call)
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fun.__name__,
                        "content": response,
                    })
                    return False, messages, response
                else:
                    logger.error(f"error fun name from model: {fun.__name__}")
                    return True, messages, ""
        else:
            logger.info("No tool calls were made by the model.")
            return True, messages, ""

    # =========================================================================
    # Configuration and utilities
    # =========================================================================

    def set_backtest(self, cur_date):
        self.backtest = True
        self.backtest_date = cur_date

    def set_symbol(self, symbol, symbol_name):
        self.symbol = symbol
        self.symbol_name = symbol_name

    def get_date_desc(self):
        if self.backtest:
            xinqi = datetime.strptime(self.backtest_date, "%Y%m%d").weekday() + 1
            return f"当前时间是：{self.backtest_date}，星期{xinqi}", self.backtest_date
        else:
            now = datetime.now()
            trade_date = get_trade_date(end_date=now.strftime('%Y%m%d'))
            if now.strftime('%Y%m%d') in trade_date:
                if datetime.now().hour <= 9 and datetime.now().minute < 30:
                    now = datetime.strptime(trade_date[-2], '%Y%m%d')
                    logger.info(f"{self.name}: trading day but before 9:30, "
                                f"using previous trading day")
            else:
                now = datetime.strptime(trade_date[-1], '%Y%m%d')
                logger.info(f"{self.name}: not a trading day, "
                            f"using previous trading day {trade_date[-1]}")
            xinqi = now.weekday() + 1
            return (f"当前时间是：{now.strftime('%Y%m%d')}，星期{xinqi}",
                    now.strftime("%Y%m%d"))

    def get_analysis_prompt(self) -> str:
        """
        Return the role-specific analysis prompt for this agent.
        Subclasses should override this to provide their prompt.
        """
        return ""

    @logger.catch
    def send_res_email(self, md, subject, table=False, toaddrs=None, dear="总裁"):
        css = """
            <style>
            table { border-collapse: collapse; }
            th, td { border: 1px solid #555; padding: 4px 8px; }
            </style>
            """
        html = markdown(md,
            extensions=[
                'markdown.extensions.tables',
                'markdown.extensions.toc',
                'markdown.extensions.codehilite'
            ])
        if table:
            html += css
        for toaddr in toaddrs:
            max_retry = 3
            while max_retry:
                try:
                    send_message(toaddrs=[toaddr], subject=subject,
                                 content=html, dear=dear)
                    break
                except Exception as e:
                    logger.error(e)
                    max_retry -= 1
                    sleep(3)
