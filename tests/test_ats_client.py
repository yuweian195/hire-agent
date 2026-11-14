import json
from types import SimpleNamespace

import httpx

from app.integrations.ats_client import AtsClient
from app.schemas import JobRequirements


def test_list_jobs_maps_java_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/jobs"
        return httpx.Response(
            200,
            json=[
                {
                    "id": "java-senior",
                    "title": "高级 Java 工程师",
                    "department": "交易技术部",
                    "seniority": "高级",
                    "minYears": 5,
                    "education": "本科",
                    "requiredSkills": ["Java", "Spring Cloud"],
                    "preferredSkills": ["Docker"],
                    "description": "交易中台",
                }
            ],
        )

    client = AtsClient("http://ats", transport=httpx.MockTransport(handler))
    jobs = client.list_jobs()

    assert len(jobs) == 1
    assert jobs[0].id == "java-senior"
    assert jobs[0].required_skills == ["Java", "Spring Cloud"]


def test_push_screening_sends_expected_payload():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/screenings"
        captured.update(json.loads(request.content))
        return httpx.Response(201, json={"id": "screening-1"})

    result = SimpleNamespace(
        candidate_name="张伟",
        job_id="java-senior",
        total_score=9.13,
        recommendation=SimpleNamespace(value="recommend"),
        job_match=SimpleNamespace(overall_rate=0.98),
        stage=SimpleNamespace(value="screening"),
    )
    parsed = SimpleNamespace(name="张伟", email="zhangwei@example.com")

    client = AtsClient("http://ats", transport=httpx.MockTransport(handler))
    assert client.push_screening(result, parsed) is True
    assert captured["candidateName"] == "张伟"
    assert captured["jobId"] == "java-senior"
    assert captured["recommendation"] == "recommend"
    assert captured["stage"] == "screening"


def test_service_prefers_remote_jobs(settings):
    from app.db import ScreeningRepository
    from app.services.screening import ScreeningService

    class FakeAts:
        def list_jobs(self):
            return [
                JobRequirements(
                    id="remote-job",
                    title="远程岗位",
                    required_skills=["Python"],
                )
            ]

    service = ScreeningService(
        repository=ScreeningRepository(settings.database_path),
        jobs_dir=settings.database_path.parent,
        ats=FakeAts(),
    )

    assert service.list_jobs()[0].id == "remote-job"
