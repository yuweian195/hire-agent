"""Human-readable job-fit calculation built on top of skill matching."""

from __future__ import annotations

from app.schemas import JobMatch, JobRequirements, ParsedResume, SkillMatch

_EDUCATION_RANK = {"高中": 0, "大专": 1, "本科": 2, "硕士": 3, "博士": 4}


def build_job_match(
    parsed: ParsedResume, job: JobRequirements, skill_match: SkillMatch
) -> JobMatch:
    required_years = max(job.min_years, 1)
    experience_rate = min(1.0, parsed.years_experience / required_years)

    actual_rank = _EDUCATION_RANK.get(parsed.education_level, 0)
    required_rank = _EDUCATION_RANK.get(job.education, 2)
    education_rate = 1.0 if actual_rank >= required_rank else 0.6

    overall = (
        0.55 * skill_match.overall_rate
        + 0.30 * experience_rate
        + 0.15 * education_rate
    )
    overall = min(overall, 0.98)

    gaps: list[str] = []
    if skill_match.missing:
        gaps.append(f"缺少 {len(skill_match.missing)} 项必备技能：{'、'.join(skill_match.missing)}")
    if parsed.years_experience < required_years:
        gaps.append(f"经验少 {required_years - parsed.years_experience:g} 年")
    if actual_rank < required_rank:
        gaps.append(f"学历低于{job.education}要求")

    if gaps:
        analysis = "；".join(gaps)
    else:
        analysis = "核心技能、经验年限与学历均达到岗位要求，无明显硬性缺口。"

    return JobMatch(
        overall_rate=round(overall, 4),
        skill_rate=skill_match.overall_rate,
        experience_rate=round(experience_rate, 4),
        education_rate=round(education_rate, 4),
        analysis=analysis,
    )
