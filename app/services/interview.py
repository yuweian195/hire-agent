"""Interview evaluation service."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from app.db import ScreeningRepository, get_repository
from app.graph.interview_workflow import get_interview_graph
from app.llm.client import LLMClient, get_llm_client
from app.schemas import (
    InterviewEvaluateRequest,
    InterviewListItem,
    InterviewRecommendation,
    InterviewReport,
)
from app.services.screening import ScreeningService


class InterviewService:
    def __init__(
        self,
        repository: ScreeningRepository | None = None,
        llm: LLMClient | None = None,
        jobs_dir: Path | None = None,
    ) -> None:
        self.repository = repository or get_repository()
        self.llm = llm or get_llm_client()
        self.screening = ScreeningService(
            repository=self.repository,
            llm=self.llm,
            jobs_dir=jobs_dir,
        )

    def evaluate(self, payload: InterviewEvaluateRequest) -> InterviewReport:
        job = self.screening.resolve_job_ref(payload.job_id, payload.jd_text)
        report_id = uuid.uuid4().hex[:12]
        created_at = datetime.now().isoformat(timespec="seconds")

        initial_state = {
            "report_id": report_id,
            "created_at": created_at,
            "llm_mode": self.llm.mode,
            "repository": self.repository,
            "job": job.model_dump(),
            "candidate_name": payload.candidate_name,
            "resume_text": payload.resume_text,
            "items": [item.model_dump() for item in payload.items],
            "trace": [],
        }
        final_state = get_interview_graph().invoke(initial_state)

        return InterviewReport(
            id=report_id,
            candidate_name=final_state["candidate_name"],
            job_id=job.id,
            job_title=job.title,
            overall_score=final_state["overall_score"],
            recommendation=InterviewRecommendation(final_state["recommendation"]),
            answer_evaluations=final_state["evaluations"],
            summary=final_state["summary"],
            llm_mode=final_state.get("llm_mode", self.llm.mode),
            trace=final_state["trace"],
            created_at=created_at,
        )

    def get_report(self, report_id: str) -> InterviewReport | None:
        payload = self.repository.get_interview(report_id)
        if payload is None:
            return None
        return InterviewReport.model_validate(payload)

    def list_recent(self, limit: int = 20) -> list[InterviewListItem]:
        return [
            InterviewListItem(
                id=item["id"],
                candidate_name=item["candidate_name"],
                job_id=item["job_id"],
                job_title=item["job_title"],
                overall_score=item["overall_score"],
                recommendation=InterviewRecommendation(item["recommendation"]),
                created_at=item["created_at"],
            )
            for item in self.repository.list_interviews(limit)
        ]


_service: InterviewService | None = None


def get_interview_service() -> InterviewService:
    global _service
    if _service is None:
        _service = InterviewService()
    return _service
