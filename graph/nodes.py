"""
LangGraph node functions for the agent orchestration graph.

Each node takes the current AgentState and returns a partial update.
"""
import os
from typing import Literal
from loguru import logger
from json_repair import repair_json
from langchain_core.messages import SystemMessage, HumanMessage

from .state import AgentState
from tools.base_tool import get_cache, save_response, get_market
from tools.all_types import EmAllagents
from prompt import sys_plan_prompt


# Global reference to planAgent — set during graph creation
_plan_agent = None


def set_plan_agent(plan_agent):
    """Register the planAgent instance for node access."""
    global _plan_agent
    _plan_agent = plan_agent


def plan_node(state: AgentState) -> dict:
    """
    Generate the execution plan via LLM.

    Uses sys_plan_prompt to decompose the user's question into a structured
    JSON plan assigning tasks to agents. Supports human-in-the-loop feedback
    when state.human_feedback is set.
    """
    question = state.get("question", "")
    human_feedback = state.get("human_feedback")
    use_cache = state.get("use_cache", True)
    symbol = state.get("symbol", "")
    human_in_loop = state.get("human_feedback") is not None

    # Check plan cache first
    plan_raw = None
    if use_cache:
        cache_res = get_cache(_plan_agent.get_date_desc()[1], symbol, EmAllagents.planAgent.name)
        if cache_res != "无结果":
            logger.info("PlanAgent: loaded plan from cache")
            plan_raw = cache_res

    if not plan_raw:
        messages = [
            SystemMessage(content=sys_plan_prompt),
            HumanMessage(content=question),
        ]

        stream = _plan_agent._llm.stream(messages)
        plan_raw = ""
        for chunk in stream:
            if chunk.content:
                plan_raw += chunk.content
                print(chunk.content, end="")

        # Handle human-in-the-loop if needed
        if human_in_loop and human_feedback:
            _messages = messages + [
                HumanMessage(content=f"Previous plan - {plan_raw}"),
                HumanMessage(content=human_feedback),
            ]
            stream = _plan_agent._llm.stream(_messages)
            plan_raw = ""
            for chunk in stream:
                if chunk.content:
                    plan_raw += chunk.content
                    print(chunk.content, end="")

    plans = repair_json(plan_raw, return_objects=True)
    if not isinstance(plans, list):
        logger.error(f"plan_node: LLM returned non-list plan (type={type(plans).__name__}), treating as empty")
        plans = []

    return {
        "plans": plans,
        "current_plan_index": 0,
        "current_task_index": 0,
        "human_feedback": None,
    }


def agent_run_node(state: AgentState) -> dict:
    """
    Run the current agent for the current task.

    Looks up the agent from planAgent's agent_dict by task['assigned_agent'],
    checks cache, and runs the agent's run() method.
    """
    plans = state.get("plans", [])
    plan_idx = state.get("current_plan_index", 0)
    task_idx = state.get("current_task_index", 0)
    use_cache = state.get("use_cache", True)
    agent_results = dict(state.get("agent_results", {}))

    # Guard: empty plan list (e.g. LLM returned unparseable/empty plan)
    if not plans or plan_idx >= len(plans):
        logger.error(f"Empty plan list or plan_idx {plan_idx} >= {len(plans)}. Skipping agent run.")
        return {"agent_results": agent_results}

    plan = plans[plan_idx]
    symbol = str(plan.get("symbol", "")).split(".")[0]
    name = plan.get("name", "")
    tasks = plan.get("tasks", [])
    if not tasks or task_idx >= len(tasks):
        logger.error(f"Empty tasks list for plan[{plan_idx}] or task_idx {task_idx} >= {len(tasks)}.")
        return {"agent_results": agent_results}

    task = tasks[task_idx]
    agent_name = task.get("assigned_agent", "")
    agent_task = task.get("task_details", "")

    if not agent_name or agent_name not in _plan_agent.agent_dict:
        logger.error(f"Invalid or unknown agent: '{agent_name}' in plan[{plan_idx}].tasks[{task_idx}]")
        return {"agent_results": agent_results}

    _plan_agent.set_symbol(symbol, name)
    agent = _plan_agent.agent_dict[agent_name]

    result = "无结果"
    if use_cache:
        result = _plan_agent.get_cache_res(symbol, agent_name)
        if result == "无结果":
            try:
                result = agent.run(agent_task)
            except Exception as e:
                logger.error(f"Error running agent {agent_name}: {e}")
    else:
        try:
            result = agent.run(agent_task)
        except Exception as e:
            logger.error(f"Error running agent {agent_name}: {e}")

    agent_results[agent_name] = result
    logger.info("*" * 99)

    return {
        "agent_results": agent_results,
        "symbol": symbol,
        "symbol_name": name,
    }


def result_node(state: AgentState) -> dict:
    """
    Advance the task counter after a successful agent run.
    """
    plan_idx = state.get("current_plan_index", 0)
    task_idx = state.get("current_task_index", 0)
    plans = state.get("plans", [])

    # Guard: empty or exhausted plans
    if not plans or plan_idx >= len(plans):
        return {"current_plan_index": plan_idx, "current_task_index": task_idx}

    # Advance to next task
    task_idx += 1
    current_plan = plans[plan_idx]
    tasks = current_plan.get("tasks", [])

    # If all tasks for this plan are done, advance to next plan
    if tasks and task_idx >= len(tasks):
        task_idx = 0
        plan_idx += 1

    return {
        "current_plan_index": plan_idx,
        "current_task_index": task_idx,
    }


def next_task_router(state: AgentState) -> Literal["agent_run", "aggregate"]:
    """
    Route to the next agent run or to aggregation.

    Returns 'agent_run' if more tasks remain, 'aggregate' if all done.
    """
    plans = state.get("plans", [])
    plan_idx = state.get("current_plan_index", 0)

    if not plans:
        return "aggregate"
    if plan_idx < len(plans):
        return "agent_run"
    return "aggregate"


def aggregate_node(state: AgentState) -> dict:
    """
    Assemble all results into final markdown, save plan cache, prepare email content.

    This node reads cached results from all agents and assembles a comprehensive
    markdown document. Email sending is handled separately by planAgent's
    send_allres_email() method.
    """
    if _plan_agent is None:
        logger.error("aggregate_node: _plan_agent is not set. Call set_plan_agent() first.")
        return {"final_output": ""}

    symbol = state.get("symbol", _plan_agent.symbol)
    symbol_name = state.get("symbol_name", _plan_agent.symbol_name)

    # No symbol set — nothing to aggregate
    if not symbol:
        return {"final_output": ""}

    cur_date = _plan_agent.get_date_desc()[1]

    hight_format = '\n\n### <span style="color: red;">{agent} POWER BY {model} </span>\n\n'

    invest_agent_res = get_cache(cur_date, symbol, EmAllagents.investmentAgent.name)
    invest_agent_res += hight_format.format(
        agent=EmAllagents.investmentAgent.name,
        model=_plan_agent.agent_dict[EmAllagents.investmentAgent.name].model)

    data_agent_res = get_cache(cur_date, symbol, EmAllagents.dataAgent.name)
    data_agent_res += hight_format.format(
        agent=EmAllagents.dataAgent.name,
        model=_plan_agent.agent_dict[EmAllagents.dataAgent.name].model)

    vl_agent_res = get_cache(cur_date, symbol, EmAllagents.vlAgent.name)
    vl_agent_res += hight_format.format(
        agent=EmAllagents.vlAgent.name,
        model=_plan_agent.agent_dict[EmAllagents.vlAgent.name].model)

    report_agent_res = get_cache(cur_date, symbol, EmAllagents.reportAgent.name)
    report_agent_res += hight_format.format(
        agent=EmAllagents.reportAgent.name,
        model=_plan_agent.agent_dict[EmAllagents.reportAgent.name].model)

    public_agent_res = get_cache(cur_date, symbol, EmAllagents.publicOptionAgent.name)
    public_agent_res += hight_format.format(
        agent=EmAllagents.publicOptionAgent.name,
        model=_plan_agent.agent_dict[EmAllagents.publicOptionAgent.name].model)

    symbol_full = get_market(symbol) + symbol
    k_line = (f"![{symbol_name}]"
              f"(http://image.sinajs.cn/newchart/min/n/{symbol_full}.gif "
              f"'{symbol_name}')")

    md = ("\n\n# 投资建议：\n" + invest_agent_res +
          "\n\n# 行情及技术指标解析：\n" + data_agent_res +
          "\n\n# k线图解析：\n" + k_line + "\n\n" + vl_agent_res +
          "\n\n# 研报解析：\n" + report_agent_res +
          "\n\n# 舆情解析：\n" + public_agent_res)

    return {
        "final_output": md,
    }
