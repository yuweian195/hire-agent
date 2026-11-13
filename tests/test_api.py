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
