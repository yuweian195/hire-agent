"""LangGraph nodes for the resume screening workflow."""

from __future__ import annotations

import time

from app.config import get_settings
from app.db import get_repository
from app.graph.state import ScreeningState
from app.llm.client import get_llm_client
from app.schemas import (
    DimensionScore,
    JobMatch,
    JobRequirements,
    ParsedResume,
    Recommendation,
    SkillMatch,
)
from app.tools.compliance import check_jd_compliance
from app.tools.jd_matcher import build_job_match
from app.tools.question_generator import generate_questions as build_questions
from app.tools.resume_parser import parse_resume
from app.tools.scorer import evaluate_dimensions, weighted_total
from app.tools.skill_matcher import extract_skills, match_skills


def _step(node: str, label: str, started: float, summary: str, status: str = "ok") -> dict:
    return {
        "node": node,
        "label": label,
        "status": status,
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "summary": summary,
    }


def parse_resume_node(state: ScreeningState) -> dict:
    started = time.perf_counter()
    parsed = parse_resume(state["resume_text"])
    summary = (
        f"识别 {parsed.name or '未命名候选人'}｜"
        f"{parsed.education_level or '学历未识别'}｜"
        f"{parsed.years_experience:g} 年经验｜"
        f"{len(parsed.projects)} 个项目"
    )
    return {
        "parsed_resume": parsed.model_dump(),
        "trace": [_step("parse_resume", "解析简历", started, summary)],
    }


def extract_skills_node(state: ScreeningState) -> dict:
    started = time.perf_counter()
    parsed = ParsedResume(**state["parsed_resume"])
    skills = list(dict.fromkeys(parsed.skills + extract_skills(state["resume_text"])))
    summary = f"识别 {len(skills)} 项技能" + (f"：{'、'.join(skills[:6])}" if skills else "")
    return {
        "skills": skills,
        "trace": [_step("extract_skills", "提取技能", started, summary)],
    }


def evaluate_dimensions_node(state: ScreeningState) -> dict:
    started = time.perf_counter()
    parsed = ParsedResume(**state["parsed_resume"])
    job = JobRequirements(**state["job"])
    match = match_skills(state["skills"], job.required_skills, job.preferred_skills)
    dimensions = evaluate_dimensions(parsed, job, match)
    strongest = max(dimensions, key=lambda item: item.score)
    summary = (
        f"六维评分完成，必备技能命中 "
        f"{len(match.matched)}/{len(match.matched) + len(match.missing)}；"
        f"最高项 {strongest.label} {strongest.score}/10"
    )
    return {
        "skill_match": match.model_dump(),
        "dimension_scores": [item.model_dump() for item in dimensions],
        "trace": [_step("evaluate_dimensions", "六维评分", started, summary)],
    }


def calculate_score_node(state: ScreeningState) -> dict:
    started = time.perf_counter()
    dimensions = [DimensionScore(**item) for item in state["dimension_scores"]]
    total = weighted_total(dimensions)
    return {
        "total_score": total,
        "trace": [_step("calculate_total_score", "计算加权总分", started, f"加权总分 {total:.2f}/10")],
    }


def match_jd_node(state: ScreeningState) -> dict:
    started = time.perf_counter()
    parsed = ParsedResume(**state["parsed_resume"])
    job = JobRequirements(**state["job"])
    match = build_job_match(parsed, job, SkillMatch(**state["skill_match"]))
    summary = f"人岗匹配度 {match.overall_rate:.0%}；{match.analysis}"
    return {
        "job_match": match.model_dump(),
        "trace": [_step("match_jd", "人岗匹配", started, summary)],
    }


def compliance_check_node(state: ScreeningState) -> dict:
    started = time.perf_counter()
    job = JobRequirements(**state["job"])
    jd_text = "\n".join([job.description, *job.responsibilities])
    result = check_jd_compliance(jd_text)
    if result.passed:
        summary = "JD 合规检查通过，未发现歧视性条款"
    else:
        summary = f"发现 {len(result.issues)} 项合规风险：{'、'.join(result.issues)}"
    return {
        "compliance": result.model_dump(),
        "trace": [_step("compliance_check", "合规检查", started, summary)],
    }


def _fallback_summary(state: ScreeningState, recommendation: Recommendation) -> str:
    parsed = ParsedResume(**state["parsed_resume"])
    dimensions = [DimensionScore(**item) for item in state["dimension_scores"]]
    top = "、".join(item.label for item in sorted(dimensions, key=lambda d: d.score, reverse=True)[:2])
    total = state["total_score"]
    name = parsed.name or "该候选人"
    missing = state["skill_match"]["missing"]
    if recommendation == Recommendation.RECOMMEND:
        return f"{name}在{top}方面表现突出，综合评分 {total:.1f}/10，建议进入技术面试。"
    if recommendation == Recommendation.HOLD:
        gap = f"（缺少 {'、'.join(missing[:3])}）" if missing else ""
        return f"{name}的基础条件基本达标，但{gap or '部分维度'}存在缺口，建议先安排 30 分钟电话初筛。"
    return f"{name}与岗位核心要求差距较大，建议转入人才库或推荐其他更匹配的岗位。"


def generate_recommendation_node(state: ScreeningState) -> dict:
    started = time.perf_counter()
    settings = get_settings()
    total = state["total_score"]
    if total >= settings.recommend_threshold:
        recommendation = Recommendation.RECOMMEND
        reason = f"综合评分 {total:.2f}，达到推荐阈值 {settings.recommend_threshold:.1f}"
    elif total >= settings.hold_threshold:
        recommendation = Recommendation.HOLD
        reason = f"综合评分 {total:.2f}，处于待定区间 {settings.hold_threshold:.1f}-{settings.recommend_threshold:.1f}"
    else:
        recommendation = Recommendation.REJECT
        reason = f"综合评分 {total:.2f}，低于待定阈值 {settings.hold_threshold:.1f}"

    compliance = state["compliance"]
    if not compliance["passed"]:
        reason += f"；JD 存在合规风险（{'、'.join(compliance['issues'])}），相关条件未计入评分"

    summary = ""
    llm = get_llm_client()
    if llm.enabled:
        parsed = ParsedResume(**state["parsed_resume"])
        job = JobRequirements(**state["job"])
        summary = llm.summarize(
            parsed,
            job,
            [DimensionScore(**item) for item in state["dimension_scores"]],
            JobMatch(**state["job_match"]),
            total,
        ) or ""
    if not summary:
        summary = _fallback_summary(state, recommendation)

    return {
        "recommendation": recommendation.value,
        "recommendation_reason": reason,
        "summary": summary,
        "trace": [
            _step(
                "generate_recommendation",
                "生成筛选结论",
                started,
                f"{recommendation.value}：{reason}",
            )
        ],
    }


def generate_questions_node(state: ScreeningState) -> dict:
    started = time.perf_counter()
    parsed = ParsedResume(**state["parsed_resume"])
    job = JobRequirements(**state["job"])
    missing = state["skill_match"]["missing"]

    questions = None
    llm = get_llm_client()
    if llm.enabled:
        questions = llm.generate_questions(parsed, job, missing)
    if not questions:
        questions = build_questions(
            parsed, job, SkillMatch(**state["skill_match"]), state["total_score"]
        )

    return {
        "questions": [item.model_dump() for item in questions],
        "trace": [
            _step("generate_questions", "生成面试题", started, f"生成 {len(questions)} 道针对性面试题")
        ],
    }


def save_results_node(state: ScreeningState) -> dict:
    started = time.perf_counter()
    job = state["job"]
    parsed = state["parsed_resume"]
    step = _step("save_results", "保存结果", started, "筛选结果已写入 SQLite")
    trace = list(state.get("trace", [])) + [step]
    payload = {
        "id": state["screening_id"],
        "candidate_name": parsed.get("name") or "未命名候选人",
        "job_id": job["id"],
        "job_title": job["title"],
        "total_score": state["total_score"],
        "recommendation": state["recommendation"],
        "recommendation_reason": state["recommendation_reason"],
        "summary": state.get("summary", ""),
        "dimension_scores": state["dimension_scores"],
        "skill_match": state["skill_match"],
        "job_match": state["job_match"],
        "compliance": state["compliance"],
        "questions": state.get("questions", []),
        "parsed_resume": parsed,
        "trace": trace,
        "llm_mode": state.get("llm_mode", "offline"),
        "stage": state.get("stage", "screening"),
        "created_at": state["created_at"],
    }
    repository = state.get("repository") or get_repository()
    repository.save(
        {
            "id": payload["id"],
            "candidate_name": payload["candidate_name"],
            "job_id": payload["job_id"],
            "job_title": payload["job_title"],
            "total_score": payload["total_score"],
            "recommendation": payload["recommendation"],
            "match_rate": payload["job_match"]["overall_rate"],
            "stage": payload["stage"],
            "created_at": payload["created_at"],
            "payload": payload,
        }
    )
    return {"trace": [step]}


def route_after_recommendation(state: ScreeningState) -> str:
    if state["recommendation"] == Recommendation.RECOMMEND.value:
        return "generate_questions"
    return "save_results"
