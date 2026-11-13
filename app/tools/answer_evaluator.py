"""Rule-based interview answer evaluation.

Scores stay deterministic (and testable); the LLM is only used to enrich the
qualitative feedback.  Dimensions: relevance, depth, structure, communication.
"""

from __future__ import annotations

import re

from app.schemas import AnswerEvaluation, InterviewItem, JobRequirements

WEIGHTS = {
    "relevance": 0.35,
    "depth": 0.30,
    "structure": 0.20,
    "communication": 0.15,
}

_STRUCTURE_MARKERS = (
    "首先",
    "其次",
    "然后",
    "最后",
    "第一",
    "第二",
    "背景",
    "任务",
    "行动",
    "结果",
    "一是",
    "二是",
    "1.",
    "2.",
)
_DEPTH_MARKERS = (
    "因为",
    "所以",
    "通过",
    "方案",
    "取舍",
    "权衡",
    "根因",
    "架构",
    "拆分",
    "降级",
    "限流",
    "监控",
    "复盘",
)
_FILLERS = ("嗯", "那个", "就是说", "然后就是", "怎么说")


def _char_bigrams(text: str) -> set[str]:
    cleaned = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9+#.]", "", text.lower())
    return {cleaned[index : index + 2] for index in range(max(0, len(cleaned) - 1))}


def _clamp(value: float, low: float = 1.0, high: float = 10.0) -> float:
    return round(max(low, min(high, value)), 1)


def _score_relevance(answer: str, question: str, job: JobRequirements, category: str) -> float:
    from app.tools.skill_matcher import extract_skills

    question_terms = _char_bigrams(question)
    answer_terms = _char_bigrams(answer)
    overlap = len(question_terms & answer_terms) / max(1, len(question_terms))

    if category in ("行为面试", "岗位理解"):
        length_bonus = 1.0 if len(answer) >= 200 else 0.0
        return _clamp(5.5 + 2.5 * min(1.0, overlap * 2) + length_bonus)

    answer_skills = set(extract_skills(answer))
    required = set(job.required_skills)
    skill_hits = len(answer_skills & required) / max(1, len(required))
    return _clamp(4.5 + 3.0 * skill_hits + 2.0 * min(1.0, overlap * 2))


def _score_depth(answer: str) -> float:
    from app.tools.skill_matcher import extract_skills

    length_score = min(1.0, len(answer) / 260)
    numbers = len(
        re.findall(r"\d+(?:\.\d+)?\s*(?:%|ms|s|万|亿|QPS|TPS|倍|人|个|年)?", answer)
    )
    number_score = min(1.0, numbers / 3)
    tech_score = min(1.0, len(extract_skills(answer)) / 5)
    mechanism_hits = sum(1 for word in _DEPTH_MARKERS if word in answer)
    mechanism_score = min(1.0, mechanism_hits / 3)

    return _clamp(
        3.0 + 3.0 * length_score + 1.5 * number_score + 1.5 * tech_score + 1.0 * mechanism_score
    )


def _score_structure(answer: str) -> float:
    markers = sum(1 for word in _STRUCTURE_MARKERS if word in answer)
    length_bonus = 1.0 if len(answer) >= 220 else 0.0
    return _clamp(4.0 + 1.5 * min(4, markers) + length_bonus)


def _score_communication(answer: str) -> float:
    sentences = [item for item in re.split(r"[。！？!?]", answer) if item.strip()]
    average_length = sum(len(item) for item in sentences) / max(1, len(sentences))
    filler_hits = sum(answer.count(word) for word in _FILLERS)
    score = 8.0 - min(2.0, filler_hits * 0.5)
    if 10 <= average_length <= 45:
        score += 0.5
    return _clamp(score)


def evaluate_answer(item: InterviewItem, job: JobRequirements) -> AnswerEvaluation:
    answer = item.answer.strip()
    dimensions = {
        "relevance": _score_relevance(answer, item.question, job, item.category),
        "depth": _score_depth(answer),
        "structure": _score_structure(answer),
        "communication": _score_communication(answer),
    }
    score = round(sum(dimensions[key] * weight for key, weight in WEIGHTS.items()), 2)

    strengths: list[str] = []
    weaknesses: list[str] = []
    if dimensions["relevance"] >= 7.5:
        strengths.append("回答与岗位要求的技能点关联紧密")
    elif dimensions["relevance"] < 6.0:
        weaknesses.append("与岗位要求的关联不足，缺少相关技能或场景")
    if dimensions["depth"] >= 7.5:
        strengths.append("给出了具体数据、方案或取舍")
    elif dimensions["depth"] < 6.0:
        weaknesses.append("细节偏少，缺少可验证的数据或方案")
    if dimensions["structure"] >= 7.5:
        strengths.append("表达有清晰的结构")
    elif dimensions["structure"] < 6.0:
        weaknesses.append("回答结构偏散，建议用 STAR 或分点表达")
    if dimensions["communication"] >= 7.5:
        strengths.append("表达简洁、可读性好")
    elif dimensions["communication"] < 6.0:
        weaknesses.append("口头语或冗余表达偏多")

    if not strengths:
        strengths.append("回答基本切题")
    if not weaknesses:
        weaknesses.append("暂无明显短板，可继续追问深度")

    missing = [skill for skill in job.required_skills if skill not in answer]
    if missing:
        follow_up = f"请补充你在 {'、'.join(missing[:2])} 上的具体实践，并说明你承担的角色。"
    elif dimensions["depth"] < 6.5:
        follow_up = "请用 STAR 结构重讲一遍，并补充可量化的结果。"
    else:
        follow_up = "如果业务规模扩大 10 倍，你的方案需要做哪些调整？"

    return AnswerEvaluation(
        question=item.question,
        answer=item.answer,
        score=score,
        dimensions=dimensions,
        strengths=strengths,
        weaknesses=weaknesses,
        follow_up=follow_up,
    )


def overall_score(evaluations: list[AnswerEvaluation]) -> float:
    if not evaluations:
        return 0.0
    return round(sum(item.score for item in evaluations) / len(evaluations), 2)
