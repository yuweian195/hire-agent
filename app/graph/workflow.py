"""Compiled LangGraph screening workflow."""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.graph import nodes
from app.graph.state import ScreeningState


@lru_cache(maxsize=1)
def get_graph():
    builder = StateGraph(ScreeningState)

    builder.add_node("parse_resume", nodes.parse_resume_node)
    builder.add_node("extract_skills", nodes.extract_skills_node)
    builder.add_node("evaluate_dimensions", nodes.evaluate_dimensions_node)
    builder.add_node("calculate_total_score", nodes.calculate_score_node)
    builder.add_node("match_jd", nodes.match_jd_node)
    builder.add_node("compliance_check", nodes.compliance_check_node)
    builder.add_node("generate_recommendation", nodes.generate_recommendation_node)
    builder.add_node("generate_questions", nodes.generate_questions_node)
    builder.add_node("save_results", nodes.save_results_node)

    builder.set_entry_point("parse_resume")
    builder.add_edge("parse_resume", "extract_skills")
    builder.add_edge("extract_skills", "evaluate_dimensions")
    builder.add_edge("evaluate_dimensions", "calculate_total_score")
    builder.add_edge("calculate_total_score", "match_jd")
    builder.add_edge("match_jd", "compliance_check")
    builder.add_edge("compliance_check", "generate_recommendation")
    builder.add_conditional_edges(
        "generate_recommendation",
        nodes.route_after_recommendation,
        {
            "generate_questions": "generate_questions",
            "save_results": "save_results",
        },
    )
    builder.add_edge("generate_questions", "save_results")
    builder.add_edge("save_results", END)

    return builder.compile()
