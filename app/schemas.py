"""Pydantic models shared by the API, the agent workflow and the UI."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Recommendation(StrEnum):
    RECOMMEND = "recommend"
    HOLD = "hold"
    REJECT = "reject"


class ScreeningStage(StrEnum):
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    TALENT_POOL = "talent_pool"


class InterviewRecommendation(StrEnum):
    PASS = "pass"
    HOLD = "hold"
    REJECT = "reject"


class WorkExperience(BaseModel):
    company: str = ""
    title: str = ""
    start: str = ""
    end: str = ""


class ParsedResume(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    education_level: str = ""
    school: str = ""
    school_tier: str = ""
    major: str = ""
    years_experience: float = 0.0
    current_title: str = ""
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    work_history: list[WorkExperience] = Field(default_factory=list)


class JobRequirements(BaseModel):
    id: str
    title: str
    department: str = ""
    seniority: str = ""
    min_years: int = 0
    education: str = "本科"
    salary_min: int | None = None
    salary_max: int | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    description: str = ""
    weights: dict[str, float] | None = None


class DimensionScore(BaseModel):
    key: str
    label: str
    score: float
    weight: float
    reason: str


class SkillMatch(BaseModel):
    overall_rate: float
    required_rate: float
    preferred_rate: float
    matched: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    preferred_matched: list[str] = Field(default_factory=list)


class JobMatch(BaseModel):
    overall_rate: float
    skill_rate: float
    experience_rate: float
    education_rate: float
    analysis: str = ""


class ComplianceResult(BaseModel):
    passed: bool = True
    issues: list[str] = Field(default_factory=list)
    sanitized_text: str = ""


class InterviewQuestion(BaseModel):
    category: str
    question: str
    intent: str = ""
    difficulty: str = "medium"


class TraceStep(BaseModel):
    node: str
    label: str
    status: str = "ok"
    duration_ms: int = 0
    summary: str = ""


class ScreenRequest(BaseModel):
    resume_text: str = Field(min_length=10)
    job_id: str | None = None
    jd_text: str | None = None


class BatchScreenRequest(BaseModel):
    job_id: str
    resume_texts: list[str] = Field(min_length=1, max_length=50)


class BatchScreenItem(BaseModel):
    rank: int
    screening: ScreeningResponse


class BatchScreenResponse(BaseModel):
    job_id: str
    job_title: str
    total: int
    items: list[BatchScreenItem] = Field(default_factory=list)


class InterviewItem(BaseModel):
    question: str = Field(min_length=4)
    answer: str = Field(min_length=1)
    category: str = ""
    intent: str = ""


class InterviewEvaluateRequest(BaseModel):
    items: list[InterviewItem] = Field(min_length=1, max_length=20)
    job_id: str | None = None
    jd_text: str | None = None
    candidate_name: str = ""
    resume_text: str = ""


class AnswerEvaluation(BaseModel):
    question: str
    answer: str
    score: float
    dimensions: dict[str, float] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    follow_up: str = ""


class InterviewReport(BaseModel):
    id: str
    candidate_name: str
    job_id: str
    job_title: str
    overall_score: float
    recommendation: InterviewRecommendation
    answer_evaluations: list[AnswerEvaluation] = Field(default_factory=list)
    summary: str = ""
    llm_mode: str = "offline"
    trace: list[TraceStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class InterviewListItem(BaseModel):
    id: str
    candidate_name: str
    job_id: str
    job_title: str
    overall_score: float
    recommendation: InterviewRecommendation
    created_at: datetime


class ScreeningResponse(BaseModel):
    id: str
    candidate_name: str
    job_id: str
    job_title: str
    total_score: float
    recommendation: Recommendation
    recommendation_reason: str
    summary: str = ""
    dimension_scores: list[DimensionScore] = Field(default_factory=list)
    skill_match: SkillMatch
    job_match: JobMatch
    compliance: ComplianceResult
    questions: list[InterviewQuestion] = Field(default_factory=list)
    parsed_resume: ParsedResume
    trace: list[TraceStep] = Field(default_factory=list)
    llm_mode: str = "offline"
    stage: ScreeningStage = ScreeningStage.SCREENING
    created_at: datetime = Field(default_factory=datetime.now)


class ScreeningListItem(BaseModel):
    id: str
    candidate_name: str
    job_id: str
    job_title: str
    total_score: float
    recommendation: Recommendation
    match_rate: float
    stage: ScreeningStage = ScreeningStage.SCREENING
    created_at: datetime


class StageUpdateRequest(BaseModel):
    stage: ScreeningStage


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_mode: str
    jobs: int
    ats: str = "off"
