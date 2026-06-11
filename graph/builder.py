"""
Graph construction for the agent orchestration workflow.

Builds a LangGraph StateGraph that implements:
    plan_node → agent_run_node → result_node → next_task_router
                         ↑                          │
                         └──────── (loop) ──────────┘
                                                        │
                                                        ▼
                                                  aggregate_node → END
"""
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    plan_node,
    agent_run_node,
    result_node,
    next_task_router,
    aggregate_node,
    set_plan_agent,
)


def create_analysis_graph(plan_agent=None) -> StateGraph:
    """
    Build and compile the analysis orchestration graph.

    Args:
        plan_agent: The PlanAgent instance that manages agent lifecycle.

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    if plan_agent is not None:
        set_plan_agent(plan_agent)

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("plan", plan_node)
    workflow.add_node("agent_run", agent_run_node)
    workflow.add_node("save_result", result_node)
    workflow.add_node("aggregate", aggregate_node)

    # Set entry
    workflow.set_entry_point("plan")

    # Edges
    workflow.add_edge("plan", "agent_run")
    workflow.add_edge("agent_run", "save_result")

    # Conditional routing: loop or finish
    workflow.add_conditional_edges(
        "save_result",
        next_task_router,
        {
            "agent_run": "agent_run",
            "aggregate": "aggregate",
        },
    )

    workflow.add_edge("aggregate", END)

    return workflow.compile()
