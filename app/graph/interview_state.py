"""Shared state for the interview evaluation workflow."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class InterviewState(TypedDict, total=False):
    report_id: str
    created_at: str
    llm_mode: str
    repository: Any

    job: dict
    candidate_name: str
    resume_text: str
    items: list[dict]

    evaluations: list[dict]
    overall_score: float
    recommendation: str
    summary: str

    trace: Annotated[list[dict], operator.add]
