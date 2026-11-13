"""FastAPI service exposing the screening pipeline."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import get_repository
from app.schemas import (
    HealthResponse,
    JobRequirements,
    ScreeningListItem,
    ScreeningResponse,
    ScreenRequest,
)
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
    description="Resume screening agent: parsing, six-dimension scoring and interview questions.",
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


@app.get("/screenings", response_model=list[ScreeningListItem])
def list_screenings(limit: int = 20) -> list[ScreeningListItem]:
    return get_service().list_recent(limit=max(1, min(limit, 100)))


@app.get("/screenings/{screening_id}", response_model=ScreeningResponse)
def get_screening(screening_id: str) -> ScreeningResponse:
    result = get_service().get_screening(screening_id)
    if result is None:
        raise HTTPException(status_code=404, detail="筛选记录不存在")
    return result
