"""Compiled LangGraph workflow for interview evaluation."""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.graph import interview_nodes
from app.graph.interview_state import InterviewState


@lru_cache(maxsize=1)
def get_interview_graph():
    builder = StateGraph(InterviewState)
    builder.add_node("prepare_context", interview_nodes.prepare_context_node)
    builder.add_node("evaluate_answers", interview_nodes.evaluate_answers_node)
    builder.add_node("aggregate", interview_nodes.aggregate_node)
    builder.add_node("generate_summary", interview_nodes.generate_summary_node)
    builder.add_node("save_report", interview_nodes.save_report_node)

    builder.set_entry_point("prepare_context")
    builder.add_edge("prepare_context", "evaluate_answers")
    builder.add_edge("evaluate_answers", "aggregate")
    builder.add_edge("aggregate", "generate_summary")
    builder.add_edge("generate_summary", "save_report")
    builder.add_edge("save_report", END)
    return builder.compile()
