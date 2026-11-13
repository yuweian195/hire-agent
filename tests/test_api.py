from fastapi.testclient import TestClient

import app.main as main


def test_health_endpoint():
    client = TestClient(main.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["jobs"] == 2


def test_jobs_endpoint():
    client = TestClient(main.app)
    response = client.get("/jobs")

    assert response.status_code == 200
    assert {job["id"] for job in response.json()} == {"java-senior", "llm-app"}


def test_screen_endpoint(monkeypatch, service, read_resume):
    monkeypatch.setattr(main, "get_service", lambda: service)
    client = TestClient(main.app)
    response = client.post(
        "/screen",
        json={
            "resume_text": read_resume("zhangwei.txt"),
            "job_id": "java-senior",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidate_name"] == "张伟"
    assert payload["recommendation"] == "recommend"
    assert len(payload["dimension_scores"]) == 6


def test_batch_and_stage_endpoints(monkeypatch, service, read_resume):
    monkeypatch.setattr(main, "get_service", lambda: service)
    client = TestClient(main.app)
    response = client.post(
        "/screen/batch",
        json={
            "job_id": "java-senior",
            "resume_texts": [read_resume("zhangwei.txt"), read_resume("wangqiang.txt")],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["items"][0]["rank"] == 1
    assert payload["items"][0]["screening"]["candidate_name"] == "张伟"

    screening_id = payload["items"][0]["screening"]["id"]
    stage_response = client.patch(
        f"/screenings/{screening_id}/stage", json={"stage": "interview"}
    )
    assert stage_response.status_code == 200
    assert stage_response.json()["stage"] == "interview"

    report = client.get(f"/screenings/{screening_id}/report")
    assert report.status_code == 200
    assert "候选人筛选报告" in report.text


def test_interview_endpoints(monkeypatch, interview_service, sample_interview):
    monkeypatch.setattr(main, "get_interview_service", lambda: interview_service)
    client = TestClient(main.app)
    response = client.post(
        "/interview/evaluate",
        json={
            "job_id": sample_interview["job_id"],
            "candidate_name": sample_interview["candidate_name"],
            "items": sample_interview["items"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidate_name"] == "张伟"
    assert payload["recommendation"] == "pass"
    assert len(payload["answer_evaluations"]) == 3

    report_id = payload["id"]
    detail = client.get(f"/interview/{report_id}")
    assert detail.status_code == 200
    report = client.get(f"/interview/{report_id}/report")
    assert report.status_code == 200
    assert "面试评估报告" in report.text

    listing = client.get("/interviews")
    assert listing.status_code == 200
    assert listing.json()[0]["id"] == report_id
