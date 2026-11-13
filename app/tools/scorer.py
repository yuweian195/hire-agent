"""Six-dimension, explainable resume scoring.

Scores are intentionally rule-based so the same input always produces the same
output.  The LLM is used for qualitative summaries, never for the numbers, which
keeps screening auditable and testable.
"""

from __future__ import annotations

from datetime import date

from app.schemas import DimensionScore, JobRequirements, ParsedResume, SkillMatch

WEIGHTS: dict[str, float] = {
    "education": 0.15,
    "experience": 0.25,
    "skills": 0.25,
    "projects": 0.15,
    "stability": 0.10,
    "potential": 0.10,
}

LABELS: dict[str, str] = {
    "education": "学历背景",
    "experience": "工作经验",
    "skills": "技能匹配",
    "projects": "项目质量",
    "stability": "稳定性",
    "potential": "成长潜力",
}

_EDUCATION_SCORE = {"博士": 9.8, "硕士": 9.0, "本科": 7.5, "大专": 5.5, "高中": 3.5}
_EDUCATION_RANK = {"高中": 0, "大专": 1, "本科": 2, "硕士": 3, "博士": 4}

_DEPTH_KEYWORDS = (
    "主导",
    "架构",
    "重构",
    "从 0 到 1",
    "从0到1",
    "高并发",
    "性能优化",
    "落地",
    "开源",
    "团队负责",
)
_POTENTIAL_KEYWORDS = ("开源", "论文", "专利", "团队管理", "技术分享", "认证", "跨团队")


def _clamp(value: float, low: float = 1.0, high: float = 10.0) -> float:
    return round(max(low, min(high, value)), 1)


def score_education(parsed: ParsedResume, job: JobRequirements) -> DimensionScore:
    base = _EDUCATION_SCORE.get(parsed.education_level, 4.0)
    reason = f"最高学历为{parsed.education_level or '未识别'}"
    if parsed.school:
        reason += f"（{parsed.school}）"
    if parsed.school_tier == "985":
        base += 0.5
        reason += "，985 院校"
    elif parsed.school_tier == "211":
        base += 0.3
        reason += "，211 院校"

    required_rank = _EDUCATION_RANK.get(job.education, 2)
    actual_rank = _EDUCATION_RANK.get(parsed.education_level, 0)
    if actual_rank < required_rank:
        base -= 1.5
        reason += f"；低于岗位要求的{job.education}"
    else:
        reason += f"；满足岗位要求的{job.education}"

    return DimensionScore(
        key="education",
        label=LABELS["education"],
        score=_clamp(base),
        weight=WEIGHTS["education"],
        reason=reason,
    )


def score_experience(parsed: ParsedResume, job: JobRequirements) -> DimensionScore:
    years = parsed.years_experience
    required = max(job.min_years, 1)
    ratio = years / required if required else 1.0

    if ratio >= 2.0:
        score = 9.8
    elif ratio >= 1.5:
        score = 9.2
    elif ratio >= 1.2:
        score = 8.8
    elif ratio >= 1.0:
        score = 8.3
    elif ratio >= 0.8:
        score = 7.2
    elif ratio >= 0.6:
        score = 5.8
    else:
        score = 4.0

    reason = f"{years:g} 年工作经验，岗位要求 {job.min_years} 年以上"
    if years >= required:
        reason += "，达到要求"
    else:
        reason += f"，尚差 {required - years:g} 年"

    return DimensionScore(
        key="experience",
        label=LABELS["experience"],
        score=_clamp(score),
        weight=WEIGHTS["experience"],
        reason=reason,
    )


def score_skills(parsed: ParsedResume, match: SkillMatch) -> DimensionScore:
    score = 10.0 * (0.75 * match.required_rate + 0.25 * match.preferred_rate)
    if match.required_rate < 0.4:
        score = min(score, 5.5)

    reason = (
        f"必备技能命中 {len(match.matched)}/{len(match.matched) + len(match.missing)}"
        f"（{match.required_rate:.0%}）"
    )
    if match.missing:
        reason += f"，缺失：{'、'.join(match.missing[:4])}"
    if match.preferred_matched:
        reason += f"；加分项命中：{'、'.join(match.preferred_matched[:3])}"

    return DimensionScore(
        key="skills",
        label=LABELS["skills"],
        score=_clamp(score),
        weight=WEIGHTS["skills"],
        reason=reason,
    )


def score_projects(parsed: ParsedResume) -> DimensionScore:
    count = len(parsed.projects)
    if count >= 3:
        score = 8.0
    elif count == 2:
        score = 7.0
    elif count == 1:
        score = 6.0
    else:
        score = 4.5

    project_text = " ".join(parsed.projects)
    hits = [keyword for keyword in _DEPTH_KEYWORDS if keyword in project_text]
    score += min(2.0, 0.4 * len(hits))

    reason = f"识别到 {count} 个项目"
    if hits:
        reason += f"，包含 {'、'.join(hits[:4])} 等深度信号"
    else:
        reason += "，缺少主导/架构类深度信号"

    return DimensionScore(
        key="projects",
        label=LABELS["projects"],
        score=_clamp(score),
        weight=WEIGHTS["projects"],
        reason=reason,
    )


def _job_tenure_years(job) -> float:  # noqa: ANN001 - WorkExperience
    try:
        start_year = int(job.start[:4])
        end_year = date.today().year if job.end == "至今" else int(job.end[:4])
        return max(0.0, end_year - start_year)
    except (ValueError, TypeError):
        return 0.0


def score_stability(parsed: ParsedResume) -> DimensionScore:
    jobs = parsed.work_history
    count = len(jobs)
    if count <= 1:
        score = 8.5
        reason = "工作经历少于 2 段，暂无明显跳槽风险"
    else:
        tenures = [_job_tenure_years(item) for item in jobs]
        average = sum(tenures) / len(tenures)
        if average >= 3:
            score = 8.0
        elif average >= 2:
            score = 7.5
        elif average >= 1.5:
            score = 6.5
        else:
            score = 5.0
        reason = f"{count} 段工作经历，平均单段 {average:.1f} 年"
        if average < 1.5:
            reason += "，跳槽偏频繁"

    return DimensionScore(
        key="stability",
        label=LABELS["stability"],
        score=_clamp(score),
        weight=WEIGHTS["stability"],
        reason=reason,
    )


def score_potential(parsed: ParsedResume) -> DimensionScore:
    score = 6.5
    signals: list[str] = []

    if parsed.education_level in ("硕士", "博士"):
        score += 0.5
        signals.append("高学历")
    if parsed.school_tier in ("985", "211"):
        score += 0.4
        signals.append(f"{parsed.school_tier} 院校")
    if any(skill in parsed.skills for skill in ("LLM", "RAG", "LangGraph", "Prompt Engineering")):
        score += 0.5
        signals.append("AI 相关技能")
    if any(keyword in " ".join(parsed.projects) for keyword in _POTENTIAL_KEYWORDS):
        score += 0.4
        signals.append("开源/专利/团队类信号")
    if parsed.current_title and any(word in parsed.current_title for word in ("高级", "资深", "Lead")):
        score += 0.3
        signals.append("当前职级较高")
    if parsed.years_experience and parsed.years_experience < 2:
        score -= 0.5
        signals.append("经验年限较短")

    reason = "综合学历、技能趋势与项目信号"
    if signals:
        reason += f"：{'、'.join(signals)}"

    return DimensionScore(
        key="potential",
        label=LABELS["potential"],
        score=_clamp(score),
        weight=WEIGHTS["potential"],
        reason=reason,
    )


def evaluate_dimensions(
    parsed: ParsedResume, job: JobRequirements, match: SkillMatch
) -> list[DimensionScore]:
    return [
        score_education(parsed, job),
        score_experience(parsed, job),
        score_skills(parsed, match),
        score_projects(parsed),
        score_stability(parsed),
        score_potential(parsed),
    ]


def weighted_total(scores: list[DimensionScore]) -> float:
    total = sum(item.score * item.weight for item in scores)
    return round(total, 2)
