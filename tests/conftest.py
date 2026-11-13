import json
from pathlib import Path

import pytest

from app.config import Settings
from app.db import ScreeningRepository
from app.llm.client import LLMClient
from app.services.interview import InterviewService
from app.services.screening import ScreeningService

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(llm_api_key="", database_path=tmp_path / "test.db")


@pytest.fixture
def service(settings: Settings) -> ScreeningService:
    return ScreeningService(
        repository=ScreeningRepository(settings.database_path),
        llm=LLMClient(settings),
        jobs_dir=ROOT / "data" / "jobs",
    )


@pytest.fixture
def interview_service(settings: Settings) -> InterviewService:
    return InterviewService(
        repository=ScreeningRepository(settings.database_path),
        llm=LLMClient(settings),
        jobs_dir=ROOT / "data" / "jobs",
    )


@pytest.fixture
def sample_interview() -> dict:
    return json.loads(
        (ROOT / "data" / "interviews" / "sample_java.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def read_resume():
    def _read(name: str) -> str:
        return (ROOT / "data" / "resumes" / name).read_text(encoding="utf-8")

    return _read
