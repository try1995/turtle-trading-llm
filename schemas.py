"""
LangGraph state schemas and data models for the agent orchestration graph.
"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """State flowing through the LangGraph analysis graph."""

    # User input
    question: str

    # Generated execution plan: list of {name, symbol, tasks: [{assigned_agent, task_details}]}
    plans: list[dict]

    # Iteration tracking for plan execution
    current_plan_index: int
    current_task_index: int

    # Accumulated results from each agent, keyed by agent name (e.g., "dataAgent")
    agent_results: dict[str, str]

    # LangChain message history for the currently executing agent
    messages: Annotated[list, add_messages]

    # Collected tool call results (raw strings)
    tool_call_results: list[str]

    # Backtesting configuration
    backtest: bool
    backtest_date: str

    # Current stock being analyzed
    symbol: str
    symbol_name: str

    # Date description string (e.g., "当前时间是：20260204，星期3")
    date_desc: str

    # Whether to use cached results
    use_cache: bool

    # Human-in-the-loop feedback for plan revision
    human_feedback: Optional[str]

    # Final assembled output
    final_output: str

    # Previous investment suggestion (for backtesting)
    last_invest_suggestion: str
