"""Client for the optional Java Spring Boot ATS integration service."""

from __future__ import annotations

import logging

import httpx

from app.schemas import JobRequirements, ParsedResume, ScreeningResponse

logger = logging.getLogger(__name__)


class AtsClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._transport = transport

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=self._transport,
        )

    def list_jobs(self) -> list[JobRequirements]:
        with self._client() as client:
            response = client.get("/api/jobs")
            response.raise_for_status()
            payload = response.json()
        return [
            JobRequirements(
                id=item["id"],
                title=item["title"],
                department=item.get("department", ""),
                seniority=item.get("seniority", ""),
                min_years=item.get("minYears", 0),
                education=item.get("education", "本科"),
                required_skills=item.get("requiredSkills", []),
                preferred_skills=item.get("preferredSkills", []),
                description=item.get("description", ""),
            )
            for item in payload
        ]

    def push_screening(self, result: ScreeningResponse, parsed: ParsedResume) -> bool:
        payload = {
            "candidateName": parsed.name or result.candidate_name,
            "candidateEmail": parsed.email or None,
            "jobId": result.job_id,
            "totalScore": result.total_score,
            "recommendation": result.recommendation.value,
            "matchRate": result.job_match.overall_rate,
            "stage": result.stage.value,
        }
        with self._client() as client:
            response = client.post("/api/screenings", json=payload)
            response.raise_for_status()
        return True
