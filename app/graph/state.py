"""Shared state for the LangGraph screening workflow."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class ScreeningState(TypedDict, total=False):
    screening_id: str
    created_at: str
    llm_mode: str
    repository: Any

    resume_text: str
    job: dict

    parsed_resume: dict
    skills: list[str]
    skill_match: dict
    dimension_scores: list[dict]
    total_score: float
    job_match: dict
    compliance: dict

    recommendation: str
    recommendation_reason: str
    summary: str
    questions: list[dict]

    trace: Annotated[list[dict], operator.add]
