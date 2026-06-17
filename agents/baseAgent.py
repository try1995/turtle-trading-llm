import os
import json
from time import sleep
from json_repair import repair_json
from llm import client  # Legacy — retained for backward compat
from loguru import logger
from abc import ABC, abstractmethod
from datetime import datetime
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
    # Multi-key failover helpers
    # =========================================================================

    def _is_quota_error(self, e: Exception) -> bool:
        """Check if *e* is a quota/auth error that should trigger key rotation."""
        from llm_factory import is_quota_error as _check
        return _check(e)

    def _send_all_keys_exhausted_email(self, last_error: Exception) -> None:
        """Send an email notification when all API keys have been exhausted."""
        subject = f"[严重] API Key 全部耗尽 — {self.name}"
        dear = "管理员"
        body = (
            f"<h3>API Key 全部耗尽</h3>"
            f"<p><b>Agent:</b> {self.name}</p>"
            f"<p><b>Symbol:</b> {self.symbol}({self.symbol_name})</p>"
            f"<p><b>错误信息:</b> {last_error}</p>"
            f"<p><b>时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
            f"<p>系统已耗尽所有 API Key 仍无法完成调用，请及时补充额度。</p>"
        )
        toaddrs = os.environ.get("toaddrs", "").split("|")
        if toaddrs and toaddrs[0]:
            self.send_res_email(body, subject, toaddrs=toaddrs, dear=dear)

    def _recreate_llm_with_key(self, key_index: int) -> None:
        """Recreate ``_llm`` (chat) instance with the *key_index*-th API key."""
        from llm_factory import _create_chat_model_with_key as _create

        model = os.environ.get(self.name + "Model", os.environ.get("model", "qwen-plus-latest"))
        self._llm = _create(key_index, model=model, streaming=True)

    def _recreate_tool_llm_with_key(self, key_index: int) -> None:
        """Recreate ``_tool_llm`` / ``_llm_with_tools`` with *key_index*-th key."""
        from llm_factory import _create_chat_model_with_key as _create

        model = os.environ.get("toolCallModel")
        if not model:
            model = os.environ.get(self.name + "Model", os.environ.get("model", "qwen-plus-latest"))
        self._tool_llm = _create(key_index, model=model, streaming=False)
        if self._langchain_tools:
            self._llm_with_tools = self._tool_llm.bind_tools(self._langchain_tools)

    # =========================================================================
    # Legacy LLM invocation methods (backward compatible)
    # =========================================================================

    def invork(self, messages, **kwargs):
        """Legacy streaming invocation using raw OpenAI client."""
        from llm_factory import ALL_API_KEYS as keys

        for key_idx in range(len(keys)):
            try:
                # Recreate client with current key on retry
                if key_idx > 0:
                    client.close()
                    # Cannot easily mutate the httpx client in openai v2;
                    # create a fresh instance instead.
                    from llm_factory import DEFAULT_BASE_URL
                    client.__init__(
                        api_key=keys[key_idx],
                        base_url=DEFAULT_BASE_URL,
                    )

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
            except Exception as e:
                if self._is_quota_error(e) and key_idx < len(keys) - 1:
                    logger.warning(f"invork: API key {key_idx} failed, trying next... ({e})")
                    continue
                # Last key or non-quota error
                if self._is_quota_error(e):
                    self._send_all_keys_exhausted_email(e)
                raise

    def invork_with_tools(self, messages):
        """Legacy tool-calling invocation using raw OpenAI client."""
        from llm_factory import ALL_API_KEYS as keys

        for key_idx in range(len(keys)):
            try:
                if key_idx > 0:
                    client.close()
                    # Cannot easily mutate the httpx client in openai v2;
                    # create a fresh instance instead.
                    from llm_factory import DEFAULT_BASE_URL
                    client.__init__(
                        api_key=keys[key_idx],
                        base_url=DEFAULT_BASE_URL,
                    )

                response = client.chat.completions.create(
                    model=self.tool_call_mdoel,
                    messages=messages,
                    tools=self.tools_regist,
                    tool_choice="auto"
                )
                response_message = response.choices[0].message
                return response_message
            except Exception as e:
                if self._is_quota_error(e) and key_idx < len(keys) - 1:
                    logger.warning(f"invork_with_tools: API key {key_idx} failed, trying next... ({e})")
                    continue
                if self._is_quota_error(e):
                    self._send_all_keys_exhausted_email(e)
                raise

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
        from llm_factory import ALL_API_KEYS as keys

        self._init_langchain()
        for key_idx in range(len(keys)):
            try:
                if key_idx > 0:
                    self._recreate_llm_with_key(key_idx)

                response = self._llm.stream(messages)
                result = ""
                for chunk in response:
                    if chunk.content:
                        result += chunk.content
                        print(chunk.content, end="")
                return result
            except Exception as e:
                if self._is_quota_error(e) and key_idx < len(keys) - 1:
                    logger.warning(f"_invoke_llm: API key {key_idx} failed, trying next... ({e})")
                    continue
                if self._is_quota_error(e):
                    self._send_all_keys_exhausted_email(e)
                raise

    def _invoke_llm_with_tools(self, messages: list):
        """
        Invoke LLM with tool binding and return the LangChain AIMessage.
        """
        from llm_factory import ALL_API_KEYS as keys

        self._init_langchain()
        if self._llm_with_tools is None:
            raise ValueError(f"Agent {self.name} has no tools bound. "
                             "Set self._langchain_tools before calling.")

        for key_idx in range(len(keys)):
            try:
                if key_idx > 0:
                    self._recreate_tool_llm_with_key(key_idx)
                return self._llm_with_tools.invoke(messages)
            except Exception as e:
                if self._is_quota_error(e) and key_idx < len(keys) - 1:
                    logger.warning(f"_invoke_llm_with_tools: API key {key_idx} failed, trying next... ({e})")
                    continue
                if self._is_quota_error(e):
                    self._send_all_keys_exhausted_email(e)
                raise

    def _execute_tool_calls(self, ai_message) -> list[ToolMessage]:
        """
        Execute all tool calls from a LangChain AIMessage natively.

        Returns list of ``ToolMessage`` objects that can be appended directly
        back into the conversation, letting the LLM continue reasoning in the
        same turn (LangChain native pattern).
        """
        tool_messages: list[ToolMessage] = []
        for tool_call in ai_message.tool_calls:
            tool_call_id = tool_call["id"]
            func_name = tool_call["name"]
            func_args = tool_call["args"]
            max_retry = 3

            # Find the LangChain tool object
            langchain_tool = None
            for t in self._langchain_tools:
                if t.name == func_name:
                    langchain_tool = t
                    break

            if langchain_tool is None:
                logger.error(f"Tool not found: {func_name}")
                tool_messages.append(ToolMessage(
                    content="工具未找到",
                    tool_call_id=tool_call_id,
                    name=func_name,
                ))
                continue

            logger.info(
                f"Executing tool: {func_name}\n"
                f"Parameters: {json.dumps(func_args, ensure_ascii=False)}\n"
            )

            response = None
            while max_retry:
                try:
                    response = langchain_tool.invoke(func_args)
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
            tool_messages.append(ToolMessage(
                content=str(response),
                tool_call_id=tool_call_id,
                name=func_name,
            ))

        return tool_messages

    def _execute_agent_loop(
        self,
        question: str,
        analysis_prompt: str,
        context_extra: str = ""
    ) -> str:
        """
        Execute the standard two-phase agent loop using LangChain natively.

        Phase 1: Tool data collection — LLM with bound tools decides which
                 tools to call; results are passed back as ``ToolMessage``
                 objects in a native LangChain tool-calling turn.
        Phase 2: Analysis — The tool results are summarized and fed to the
                 LLM with the agent-specific analysis prompt.

        Args:
            question: The user's question or task description.
            analysis_prompt: The role-specific system prompt for Phase 2.
            context_extra: Extra context to append to the tool-phase user message.

        Returns:
            The final streaming LLM analysis text.
        """
        from prompt import sys_tool_prompt

        self._init_langchain()

        # ---- Phase 1: Tool data collection (native LangChain) ----
        tool_msgs: list[ToolMessage] = []
        if self._langchain_tools:
            phase1_messages: list = [
                SystemMessage(content=sys_tool_prompt),
                HumanMessage(content=self.get_date_desc()[0]),
                HumanMessage(
                    content=f"{question}：{self.symbol_name}({self.symbol})"
                    + (f"\n\n{context_extra}" if context_extra else "")
                ),
            ]

            ai_msg = self._invoke_llm_with_tools(phase1_messages)
            tool_msgs = self._execute_tool_calls(ai_msg)

        # ---- Phase 2: Analysis ----
        tool_summary = "\n\n".join(
            f"{msg.name}:\n{msg.content}" for msg in tool_msgs
        )
        phase2_messages = [
            SystemMessage(content=analysis_prompt),
            HumanMessage(
                content=f"基于用户提供的数据分析：{self.symbol_name}({self.symbol})\n"
                        f"用户提供数据如下：{tool_summary}"
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
