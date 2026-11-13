from app.schemas import (
    InterviewEvaluateRequest,
    InterviewItem,
    InterviewRecommendation,
    JobRequirements,
)
from app.tools.answer_evaluator import evaluate_answer


def _payload(sample: dict) -> InterviewEvaluateRequest:
    return InterviewEvaluateRequest(
        job_id=sample["job_id"],
        candidate_name=sample["candidate_name"],
        items=[InterviewItem(**item) for item in sample["items"]],
    )


def test_interview_report_is_generated_and_persisted(interview_service, sample_interview):
    report = interview_service.evaluate(_payload(sample_interview))

    assert report.candidate_name == "张伟"
    assert 7.0 <= report.overall_score <= 9.0
    assert report.recommendation == InterviewRecommendation.PASS
    assert len(report.answer_evaluations) == 3
    assert all(1 <= item.score <= 10 for item in report.answer_evaluations)
    assert report.summary
    assert [step.node for step in report.trace] == [
        "prepare_context",
        "evaluate_answers",
        "aggregate",
        "generate_summary",
        "save_report",
    ]

    loaded = interview_service.get_report(report.id)
    assert loaded is not None
    assert loaded.candidate_name == "张伟"
    assert loaded.overall_score == report.overall_score

    recent = interview_service.list_recent(5)
    assert recent[0].id == report.id


def test_structured_answer_scores_higher_than_vague_answer():
    job = JobRequirements(
        id="test",
        title="Java 工程师",
        required_skills=["Java", "Redis", "Kafka", "MySQL"],
    )
    structured = InterviewItem(
        question="请介绍一次高并发优化。",
        answer=(
            "背景：大促峰值 8 万 TPS。任务：我负责把 P99 降下来。"
            "行动：首先压测定位 Redis 热点，然后增加本地缓存，最后用 Kafka 异步削峰。"
            "结果：P99 从 420ms 降到 180ms，零超卖。"
        ),
        category="技术深度",
    )
    vague = InterviewItem(
        question="请介绍一次高并发优化。",
        answer="嗯，就是做了些优化，然后效果还可以吧。",
        category="技术深度",
    )

    structured_eval = evaluate_answer(structured, job)
    vague_eval = evaluate_answer(vague, job)

    assert structured_eval.score > vague_eval.score
    assert structured_eval.dimensions["depth"] > vague_eval.dimensions["depth"]
