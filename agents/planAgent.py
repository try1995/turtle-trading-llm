import os
import json
import re
from loguru import logger
from copy import deepcopy
from prompt import sys_plan_prompt
from .dataAgent import DataAgent
from .reportAgent import ReportAgent
from .publicOptionAgent import PublicOptionAgent
from .baseAgent import baseAgent
from .InvestmentAgent import InvestmentAgent
from json_repair import repair_json
from tools.all_types import EmAllagents
from agents.vlAgent import VlAgent
from tools.base_tool import get_cache, save_response, get_market
from langchain_core.messages import SystemMessage, HumanMessage


class PlanAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.name = EmAllagents.planAgent.name
        self.model = os.environ.get(self.name + "Model", self.model)
        self.agent = [DataAgent, ReportAgent, PublicOptionAgent]
        self.agent_dict: dict[str, baseAgent] = {
            EmAllagents.dataAgent.name: DataAgent(),
            EmAllagents.reportAgent.name: ReportAgent(),
            EmAllagents.vlAgent.name: VlAgent(),
            EmAllagents.publicOptionAgent.name: PublicOptionAgent(),
            EmAllagents.investmentAgent.name: InvestmentAgent()}
        self.agent_res = {}
        self.last_invest_suggestion = ""
        self.use_cache = True
        # LangGraph — built lazily on first run
        self._graph = None

    def _init_langchain(self):
        """Initialize LangChain for plan generation."""
        if self._llm is None:
            from llm_factory import create_chat_model
            self._llm = create_chat_model(self.name)

    def _get_graph(self):
        """Lazy-init the LangGraph graph."""
        if self._graph is None:
            from graph.builder import create_analysis_graph
            # Ensure planAgent's own llm is initialized
            self._init_langchain()
            self._graph = create_analysis_graph(plan_agent=self)
        return self._graph

    def set_symbol(self, symbol, name):
        super().set_symbol(symbol, name)
        for _, v in self.agent_dict.items():
            v.set_symbol(symbol, name)

    def set_backtest(self, cur_date, last_invest_suggestion="无", use_cache=True):
        self.backtest = True
        self.use_cache = use_cache
        self.backtest_date = cur_date
        self.last_invest_suggestion = last_invest_suggestion
        for _, v in self.agent_dict.items():
            v.set_backtest(cur_date)

    def invork(self, message, human_in_loop):
        """
        Generate plan via LangChain streaming.

        Supports interactive human-in-the-loop feedback.
        Automatically retries with the next API key on quota/auth errors.
        """
        from llm_factory import ALL_API_KEYS as keys

        self._init_langchain()
        messages = [
            SystemMessage(content=sys_plan_prompt),
            HumanMessage(content=message),
        ]

        for key_idx in range(len(keys)):
            try:
                if key_idx > 0:
                    self._recreate_llm_with_key(key_idx)

                stream = self._llm.stream(messages)
                plan = ""
                for chunk in stream:
                    if chunk.content:
                        plan += chunk.content
                        print(chunk.content, end="")

                if human_in_loop:
                    while True:
                        _messages = deepcopy(messages)
                        human_input = input(
                            "\n\nneed replan? or give advice. if not, just input no\n\n"
                        )
                        logger.debug(human_input)
                        if human_input.strip().lower() != "no":
                            from langchain_core.messages import AIMessage
                            _messages.append(AIMessage(content=f"Previous plan - {plan}"))
                            _messages.append(HumanMessage(content=human_input))
                            stream = self._llm.stream(_messages)
                            plan = ""
                            for chunk in stream:
                                if chunk.content:
                                    plan += chunk.content
                                    print(chunk.content, end="")
                        else:
                            break
                return plan
            except Exception as e:
                if self._is_quota_error(e) and key_idx < len(keys) - 1:
                    logger.warning(f"planAgent.invork: API key {key_idx} failed, trying next... ({e})")
                    continue
                if self._is_quota_error(e):
                    self._send_all_keys_exhausted_email(e)
                raise

    def get_cache_res(self, symbol, agent_name):
        res = get_cache(self.get_date_desc()[1], symbol, agent_name)
        if res != "无结果":
            logger.info(f"{agent_name}: loaded cache successfully!!!")
        return res

    @staticmethod
    def _extract_first_json_array(text: str) -> list:
        """
        Extract the first JSON array `[...]` from a string.

        The LLM sometimes wraps JSON in markdown code fences (```json ... ```)
        or outputs extra content after the plan.  This method finds the outermost
        `[...]` pair, extracts the substring, and parses it — falling back to
        repair_json on the extracted text if standard parsing fails.

        Returns:
            Parsed list, or empty list if nothing parseable is found.
        """
        # Strip code fences first
        text = text.strip()

        # Try extracting content from ```json ... ``` blocks
        block_pattern = re.compile(
            r'```(?:json)?\s*\n?\s*(\[.*?\])\s*\n?\s*```',
            re.DOTALL
        )
        match = block_pattern.search(text)
        if match:
            candidate = match.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # Fallback: find the outermost [ ... ] directly
        start = text.find('[')
        if start == -1:
            logger.warning("No '[' found in plan output — falling back to repair_json")
            return repair_json(text, return_objects=True) or []

        # Track bracket depth to find the matching close
        depth = 0
        end = -1
        for i in range(start, len(text)):
            if text[i] == '[':
                depth += 1
            elif text[i] == ']':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        if end == -1:
            logger.warning("Unmatched '[' in plan output — falling back to repair_json")
            return repair_json(text, return_objects=True) or []

        raw = text[start:end]
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
            logger.warning(f"Extracted JSON is not a list (type={type(parsed).__name__}), falling back")
        except json.JSONDecodeError:
            logger.info("Standard JSON parse failed on extracted block, trying repair_json")
            pass

        # Last resort: repair_json on the extracted block
        repaired = repair_json(raw, return_objects=True)
        return repaired if isinstance(repaired, list) else []

    def act(self, plans):
        """
        Execute plan using LangGraph graph.

        Instead of the hand-written sequential loop, this now delegates
        to the compiled LangGraph graph.
        """
        if not plans:
            logger.warning("Empty plan list — skipping graph execution.")
            self.agent_res = {}
            return

        initial_state = {
            "question": "",
            "plans": plans,
            "current_plan_index": 0,
            "current_task_index": 0,
            "agent_results": {},
            "use_cache": self.use_cache,
            "backtest": self.backtest,
            "backtest_date": self.backtest_date,
            "symbol": self.symbol,
            "symbol_name": self.symbol_name,
            "last_invest_suggestion": self.last_invest_suggestion,
        }

        graph = self._get_graph()
        final_state = graph.invoke(initial_state)

        # Populate agent_res from final state
        self.agent_res = final_state.get("agent_results", {})

        for agent_name, res in self.agent_res.items():
            logger.info(f"{agent_name}: completed, result length={len(res) if res else 0}")

    @logger.catch
    @save_response
    def run(self, question, human_in_loop=False, use_cache=True, symbol=""):
        """
        Full analysis pipeline using LangGraph.

        1. Generate plan (or load from cache)
        2. Execute plan via the LangGraph graph
        3. Return the plan_raw string
        """
        logger.info(f"{self.name}: executing task: {question}")
        self.use_cache = use_cache
        self.symbol = symbol
        self._init_langchain()

        # Phase 1: Plan generation
        if self.use_cache:
            agent_res = self.get_cache_res(self.symbol, self.name)
            if agent_res == "无结果":
                plan_raw = self.invork(question, human_in_loop)
            else:
                plan_raw = agent_res
        else:
            plan_raw = self.invork(question, human_in_loop)

        # Extract the first JSON array [...] from the response.
        # LLM sometimes outputs extra content after the plan (e.g. "```json\n[]\n```"),
        # and repair_json may pick that empty array instead of the real plan.
        plans = self._extract_first_json_array(plan_raw)

        # Phase 2: Execute via LangGraph
        self.act(plans)

        return plan_raw
    
    def compose_email(self):
        cur_date = self.get_date_desc()[1]
        # hight_format = ('\n\n### <span style="color: red;">{agent} '
                        # 'POWER BY {model} </span>\n\n')
        hight_format = ('\n\n### {agent} POWER BY {model}\n\n')
        invest_agent_res = get_cache(cur_date, self.symbol,
                                     EmAllagents.investmentAgent.name)
        invest_agent_res += hight_format.format(
            agent=EmAllagents.investmentAgent.name,
            model=self.agent_dict[EmAllagents.investmentAgent.name].model)

        data_agent_res = get_cache(cur_date, self.symbol,
                                   EmAllagents.dataAgent.name)
        data_agent_res += hight_format.format(
            agent=EmAllagents.dataAgent.name,
            model=self.agent_dict[EmAllagents.dataAgent.name].model)

        vl_agent_res = get_cache(cur_date, self.symbol,
                                 EmAllagents.vlAgent.name)
        vl_agent_res += hight_format.format(
            agent=EmAllagents.vlAgent.name,
            model=self.agent_dict[EmAllagents.vlAgent.name].model)

        report_agent_res = get_cache(cur_date, self.symbol,
                                     EmAllagents.reportAgent.name)
        report_agent_res += hight_format.format(
            agent=EmAllagents.reportAgent.name,
            model=self.agent_dict[EmAllagents.reportAgent.name].model)

        public_agent_res = get_cache(cur_date, self.symbol,
                                     EmAllagents.publicOptionAgent.name)
        public_agent_res += hight_format.format(
            agent=EmAllagents.publicOptionAgent.name,
            model=self.agent_dict[EmAllagents.publicOptionAgent.name].model)

        symbol = get_market(self.symbol) + self.symbol
        k_line = (f"![{self.symbol_name}]"
                  f"(http://image.sinajs.cn/newchart/min/n/{symbol}.gif "
                  f"'{self.symbol_name}')")

        md = ("\n\n# 投资建议：\n" + invest_agent_res +
              "\n\n# 行情及技术指标解析：\n" + data_agent_res +
              "\n\n# k线图解析：\n" + k_line + "\n\n" + vl_agent_res +
              "\n\n# 研报解析：\n" + report_agent_res +
              "\n\n# 舆情解析：\n" + public_agent_res)
        return md

    def send_allres_email(self, subject, toaddrs=None, dear="总裁"):
        """Assemble and send comprehensive analysis email."""
        md = self.compose_email()
        
        if toaddrs is None:
            toaddrs = os.environ.get("toaddrs", "").split(",")
        if toaddrs:
            self.send_res_email(md, subject, table=True,
                                toaddrs=toaddrs, dear=dear)
        return md
