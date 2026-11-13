"""Screening service: job loading, graph invocation and response mapping."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path

from app.config import get_settings
from app.db import ScreeningRepository, get_repository
from app.graph.workflow import get_graph
from app.llm.client import LLMClient, get_llm_client
from app.schemas import (
    BatchScreenItem,
    BatchScreenRequest,
    BatchScreenResponse,
    JobRequirements,
    Recommendation,
    ScreeningListItem,
    ScreeningResponse,
    ScreeningStage,
    ScreenRequest,
)
from app.tools.skill_matcher import extract_skills


class ScreeningService:
    def __init__(
        self,
        repository: ScreeningRepository | None = None,
        llm: LLMClient | None = None,
        jobs_dir: Path | None = None,
    ) -> None:
        self.repository = repository or get_repository()
        self.llm = llm or get_llm_client()
        self.jobs_dir = Path(jobs_dir or get_settings().jobs_dir)

    def list_jobs(self) -> list[JobRequirements]:
        jobs: list[JobRequirements] = []
        if not self.jobs_dir.exists():
            return jobs
        for path in sorted(self.jobs_dir.glob("*.json")):
            try:
                jobs.append(JobRequirements.model_validate_json(path.read_text("utf-8")))
            except Exception:
                continue
        return jobs

    def get_job(self, job_id: str) -> JobRequirements | None:
        for job in self.list_jobs():
            if job.id == job_id:
                return job
        return None

    def _job_from_text(self, jd_text: str) -> JobRequirements:
        lines = [line.strip() for line in jd_text.splitlines() if line.strip()]
        title = lines[0] if lines else "自定义岗位"
        years_match = re.search(r"(\d+)\s*年(?:以上)?(?:工作)?经验", jd_text)
        salary_match = re.search(
            r"(\d{2,3})\s*[-~至到]\s*(\d{2,3})\s*[kK千]", jd_text
        )
        salary_min = int(salary_match.group(1)) * 1000 if salary_match else None
        salary_max = int(salary_match.group(2)) * 1000 if salary_match else None
        education = next(
            (level for level in ("博士", "硕士", "本科", "大专") if level in jd_text),
            "本科",
        )
        skills = extract_skills(jd_text)
        return JobRequirements(
            id=f"custom-{uuid.uuid4().hex[:6]}",
            title=title,
            min_years=int(years_match.group(1)) if years_match else 0,
            education=education,
            salary_min=salary_min,
            salary_max=salary_max,
            required_skills=skills[:8],
            preferred_skills=skills[8:12],
            description=jd_text,
        )

    def resolve_job_ref(
        self, job_id: str | None, jd_text: str | None
    ) -> JobRequirements:
        if job_id:
            job = self.get_job(job_id)
            if job:
                return job
        if jd_text:
            return self._job_from_text(jd_text)
        raise ValueError("请提供 job_id 或 jd_text")

    def resolve_job(self, payload: ScreenRequest) -> JobRequirements:
        return self.resolve_job_ref(payload.job_id, payload.jd_text)

    def screen(self, payload: ScreenRequest) -> ScreeningResponse:
        job = self.resolve_job(payload)
        screening_id = uuid.uuid4().hex[:12]
        created_at = datetime.now().isoformat(timespec="seconds")

        initial_state = {
            "screening_id": screening_id,
            "created_at": created_at,
            "llm_mode": self.llm.mode,
            "repository": self.repository,
            "resume_text": payload.resume_text,
            "job": job.model_dump(),
            "stage": ScreeningStage.SCREENING.value,
            "trace": [],
        }
        final_state = get_graph().invoke(initial_state)

        response = ScreeningResponse(
            id=screening_id,
            candidate_name=final_state["parsed_resume"].get("name") or "未命名候选人",
            job_id=job.id,
            job_title=job.title,
            total_score=final_state["total_score"],
            recommendation=Recommendation(final_state["recommendation"]),
            recommendation_reason=final_state["recommendation_reason"],
            summary=final_state.get("summary", ""),
            dimension_scores=final_state["dimension_scores"],
            skill_match=final_state["skill_match"],
            job_match=final_state["job_match"],
            compliance=final_state["compliance"],
            questions=final_state.get("questions", []),
            parsed_resume=final_state["parsed_resume"],
            trace=final_state["trace"],
            llm_mode=final_state.get("llm_mode", self.llm.mode),
            stage=ScreeningStage(final_state.get("stage", ScreeningStage.SCREENING.value)),
            created_at=created_at,
        )
        return response

    def screen_batch(self, payload: BatchScreenRequest) -> BatchScreenResponse:
        job = self.get_job(payload.job_id)
        if job is None:
            raise ValueError(f"岗位不存在：{payload.job_id}")

        results = [
            self.screen(ScreenRequest(resume_text=text, job_id=payload.job_id))
            for text in payload.resume_texts
        ]
        results.sort(key=lambda item: (-item.total_score, item.candidate_name))
        items = [
            BatchScreenItem(rank=index, screening=result)
            for index, result in enumerate(results, start=1)
        ]
        return BatchScreenResponse(
            job_id=job.id,
            job_title=job.title,
            total=len(items),
            items=items,
        )

    def update_stage(self, screening_id: str, stage: ScreeningStage) -> ScreeningResponse | None:
        if not self.repository.update_stage(screening_id, stage.value):
            return None
        return self.get_screening(screening_id)

    def list_recent(self, limit: int = 20) -> list[ScreeningListItem]:
        return [
            ScreeningListItem(
                id=item["id"],
                candidate_name=item["candidate_name"],
                job_id=item["job_id"],
                job_title=item["job_title"],
                total_score=item["total_score"],
                recommendation=Recommendation(item["recommendation"]),
                match_rate=item["match_rate"],
                stage=ScreeningStage(item.get("stage", ScreeningStage.SCREENING.value)),
                created_at=item["created_at"],
            )
            for item in self.repository.list_recent(limit)
        ]

    def get_screening(self, screening_id: str) -> ScreeningResponse | None:
        payload = self.repository.get(screening_id)
        if payload is None:
            return None
        return ScreeningResponse.model_validate(payload)


_service: ScreeningService | None = None


def get_service() -> ScreeningService:
    global _service
    if _service is None:
        _service = ScreeningService()
    return _service
