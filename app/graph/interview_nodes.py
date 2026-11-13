"""LangGraph nodes for interview answer evaluation."""

from __future__ import annotations

import time

from app.config import get_settings
from app.db import get_repository
from app.graph.interview_state import InterviewState
from app.llm.client import get_llm_client
from app.schemas import (
    AnswerEvaluation,
    InterviewItem,
    InterviewRecommendation,
    JobRequirements,
)
from app.tools.answer_evaluator import evaluate_answer, overall_score
from app.tools.resume_parser import parse_resume


def _step(node: str, label: str, started: float, summary: str) -> dict:
    return {
        "node": node,
        "label": label,
        "status": "ok",
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "summary": summary,
    }


def prepare_context_node(state: InterviewState) -> dict:
    started = time.perf_counter()
    candidate = (state.get("candidate_name") or "").strip()
    if not candidate and state.get("resume_text"):
        candidate = parse_resume(state["resume_text"]).name
    candidate = candidate or "未命名候选人"
    summary = f"候选人 {candidate}｜{len(state['items'])} 道面试题"
    return {
        "candidate_name": candidate,
        "trace": [_step("prepare_context", "准备上下文", started, summary)],
    }


def evaluate_answers_node(state: InterviewState) -> dict:
    started = time.perf_counter()
    job = JobRequirements(**state["job"])
    llm = get_llm_client()
    evaluations: list[dict] = []

    for raw_item in state["items"]:
        item = InterviewItem(**raw_item)
        evaluation = evaluate_answer(item, job)
        if llm.enabled:
            feedback = llm.review_answer(
                item.question, item.answer, job, evaluation.dimensions
            )
            if feedback:
                evaluation.strengths = feedback["strengths"] or evaluation.strengths
                evaluation.weaknesses = feedback["weaknesses"] or evaluation.weaknesses
                evaluation.follow_up = feedback["follow_up"] or evaluation.follow_up
        evaluations.append(evaluation.model_dump())

    average = sum(item["score"] for item in evaluations) / max(1, len(evaluations))
    return {
        "evaluations": evaluations,
        "trace": [
            _step(
                "evaluate_answers",
                "逐题评估",
                started,
                f"完成 {len(evaluations)} 道题，平均 {average:.1f}/10",
            )
        ],
    }


def aggregate_node(state: InterviewState) -> dict:
    started = time.perf_counter()
    evaluations = [AnswerEvaluation(**item) for item in state["evaluations"]]
    score = overall_score(evaluations)
    settings = get_settings()
    if score >= settings.interview_pass_threshold:
        recommendation = InterviewRecommendation.PASS
    elif score >= settings.interview_hold_threshold:
        recommendation = InterviewRecommendation.HOLD
    else:
        recommendation = InterviewRecommendation.REJECT
    return {
        "overall_score": score,
        "recommendation": recommendation.value,
        "trace": [
            _step(
                "aggregate",
                "汇总面试结论",
                started,
                f"平均 {score:.2f}/10，结论 {recommendation.value}",
            )
        ],
    }


def generate_summary_node(state: InterviewState) -> dict:
    started = time.perf_counter()
    evaluations = [AnswerEvaluation(**item) for item in state["evaluations"]]
    strengths = list(
        dict.fromkeys(item for evaluation in evaluations for item in evaluation.strengths)
    )
    weaknesses = list(
        dict.fromkeys(item for evaluation in evaluations for item in evaluation.weaknesses)
    )
    job = JobRequirements(**state["job"])

    summary = ""
    llm = get_llm_client()
    if llm.enabled:
        summary = (
            llm.summarize_interview(
                state["candidate_name"],
                job,
                [item.score for item in evaluations],
                state["overall_score"],
                state["recommendation"],
                strengths,
                weaknesses,
            )
            or ""
        )
    if not summary:
        label = {
            "pass": "建议进入下一轮",
            "hold": "建议补充面试或由用人经理复核",
            "reject": "建议不进入下一轮",
        }.get(state["recommendation"], "建议人工复核")
        summary = (
            f"{state['candidate_name']} 的面试平均得分 {state['overall_score']:.1f}/10，{label}。"
            f"主要优势：{'；'.join(strengths[:2]) or '暂不明显'}。"
            f"主要风险：{'；'.join(weaknesses[:2]) or '暂无明显风险'}。"
        )

    return {
        "summary": summary,
        "trace": [_step("generate_summary", "生成面试结论", started, "面试结论已生成")],
    }


def save_report_node(state: InterviewState) -> dict:
    started = time.perf_counter()
    step = _step("save_report", "保存面试报告", started, "面试报告已写入 SQLite")
    trace = list(state.get("trace", [])) + [step]
    payload = {
        "id": state["report_id"],
        "candidate_name": state["candidate_name"],
        "job_id": state["job"]["id"],
        "job_title": state["job"]["title"],
        "overall_score": state["overall_score"],
        "recommendation": state["recommendation"],
        "answer_evaluations": state["evaluations"],
        "summary": state["summary"],
        "llm_mode": state.get("llm_mode", "offline"),
        "trace": trace,
        "created_at": state["created_at"],
    }
    repository = state.get("repository") or get_repository()
    repository.save_interview(
        {
            "id": payload["id"],
            "candidate_name": payload["candidate_name"],
            "job_id": payload["job_id"],
            "job_title": payload["job_title"],
            "overall_score": payload["overall_score"],
            "recommendation": payload["recommendation"],
            "created_at": payload["created_at"],
            "payload": payload,
        }
    )
    return {"trace": [step]}
