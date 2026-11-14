"""FastAPI service exposing the screening pipeline."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.db import get_repository
from app.schemas import (
    BatchScreenRequest,
    BatchScreenResponse,
    HealthResponse,
    InterviewEvaluateRequest,
    InterviewListItem,
    InterviewReport,
    JobRequirements,
    ScreeningListItem,
    ScreeningResponse,
    ScreenRequest,
    StageUpdateRequest,
)
from app.services.interview import get_interview_service
from app.services.reporting import interview_markdown, screening_markdown
from app.services.screening import get_service
from app.tools.resume_parser import decode_text


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_repository()
    yield


settings = get_settings()
app = FastAPI(
    title="HireAgent API",
    version=settings.version,
    description="Recruiting agent: resume screening, batch ranking and interview evaluation.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    service = get_service()
    return HealthResponse(
        status="ok",
        version=settings.version,
        llm_mode=service.llm.mode,
        jobs=len(service.list_jobs()),
        ats="online" if service.ats is not None else "off",
    )


@app.get("/jobs", response_model=list[JobRequirements])
def list_jobs() -> list[JobRequirements]:
    return get_service().list_jobs()


@app.post("/screen", response_model=ScreeningResponse)
def screen(payload: ScreenRequest) -> ScreeningResponse:
    try:
        return get_service().screen(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/screen/upload", response_model=ScreeningResponse)
async def screen_upload(
    job_id: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
) -> ScreeningResponse:
    content = await file.read()
    text = decode_text(file.filename or "", content)
    if len(text.strip()) < 10:
        raise HTTPException(status_code=400, detail="未能从文件中解析出有效文本")
    try:
        return get_service().screen(ScreenRequest(resume_text=text, job_id=job_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/screen/batch", response_model=BatchScreenResponse)
def screen_batch(payload: BatchScreenRequest) -> BatchScreenResponse:
    try:
        return get_service().screen_batch(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/screenings/{screening_id}/stage", response_model=ScreeningResponse)
def update_screening_stage(
    screening_id: str, payload: StageUpdateRequest
) -> ScreeningResponse:
    result = get_service().update_stage(screening_id, payload.stage)
    if result is None:
        raise HTTPException(status_code=404, detail="筛选记录不存在")
    return result


@app.post("/interview/evaluate", response_model=InterviewReport)
def evaluate_interview(payload: InterviewEvaluateRequest) -> InterviewReport:
    try:
        return get_interview_service().evaluate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/interviews", response_model=list[InterviewListItem])
def list_interviews(limit: int = 20) -> list[InterviewListItem]:
    return get_interview_service().list_recent(limit=max(1, min(limit, 100)))


@app.get("/interview/{report_id}", response_model=InterviewReport)
def get_interview(report_id: str) -> InterviewReport:
    report = get_interview_service().get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="面试报告不存在")
    return report


@app.get("/interview/{report_id}/report", response_class=PlainTextResponse)
def get_interview_report(report_id: str) -> PlainTextResponse:
    report = get_interview_service().get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="面试报告不存在")
    return PlainTextResponse(
        interview_markdown(report),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="interview-{report_id}.md"'},
    )


@app.get("/screenings", response_model=list[ScreeningListItem])
def list_screenings(limit: int = 20) -> list[ScreeningListItem]:
    return get_service().list_recent(limit=max(1, min(limit, 100)))


@app.get("/screenings/{screening_id}", response_model=ScreeningResponse)
def get_screening(screening_id: str) -> ScreeningResponse:
    result = get_service().get_screening(screening_id)
    if result is None:
        raise HTTPException(status_code=404, detail="筛选记录不存在")
    return result


@app.get("/screenings/{screening_id}/report", response_class=PlainTextResponse)
def get_screening_report(screening_id: str) -> PlainTextResponse:
    result = get_service().get_screening(screening_id)
    if result is None:
        raise HTTPException(status_code=404, detail="筛选记录不存在")
    return PlainTextResponse(
        screening_markdown(result),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="screening-{screening_id}.md"'
        },
    )
