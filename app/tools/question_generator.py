"""Rule-based interview question generation.

Questions are derived from the JD's required skills, the candidate's missing
skills and their strongest projects, so the output is specific enough to use in
a real interview rather than generic prompt filler.
"""

from __future__ import annotations

from app.schemas import InterviewQuestion, JobRequirements, ParsedResume, SkillMatch


def generate_questions(
    parsed: ParsedResume,
    job: JobRequirements,
    match: SkillMatch,
    total_score: float,
) -> list[InterviewQuestion]:
    top_skills = match.matched[:3] or job.required_skills[:3]
    missing = match.missing[:2]
    project = parsed.projects[0] if parsed.projects else ""
    questions: list[InterviewQuestion] = []

    if top_skills:
        questions.append(
            InterviewQuestion(
                category="技术深度",
                question=(
                    f"你的简历体现了 {'、'.join(top_skills)} 的使用经验。"
                    f"请选一个你主导解决的技术问题，说明背景、方案取舍和最终效果。"
                ),
                intent="验证技能是真实使用过，还是只停留在关键词层面",
                difficulty="hard",
            )
        )

    if project:
        questions.append(
            InterviewQuestion(
                category="项目复盘",
                question=(
                    f"围绕「{project}」这个项目，如果让你重新做一次，"
                    f"你会保留什么、改掉什么？请给出判断依据。"
                ),
                intent="考察复盘能力和技术判断力",
                difficulty="medium",
            )
        )

    if missing:
        questions.append(
            InterviewQuestion(
                category="能力补齐",
                question=(
                    f"岗位要求 {'、'.join(missing)}，但简历中没有直接体现。"
                    f"请说明你目前的掌握程度，以及如果入职，前三个月会如何补齐。"
                ),
                intent="确认缺口是否可控，观察学习路径是否具体",
                difficulty="medium",
            )
        )

    questions.append(
        InterviewQuestion(
            category="行为面试",
            question=(
                "讲一次你和产品/业务方在方案上意见不一致的经历。"
                "你当时如何对齐目标、如何推动决策？"
            ),
            intent="考察跨团队沟通与推动能力",
            difficulty="medium",
        )
    )

    questions.append(
        InterviewQuestion(
            category="场景设计",
            question=(
                f"假设你入职后负责「{job.title}」相关系统，"
                f"线上核心接口 P99 延迟突然翻倍，你会按什么顺序排查？"
            ),
            intent="考察线上问题定位思路和工程素养",
            difficulty="hard" if total_score >= 8 else "medium",
        )
    )

    questions.append(
        InterviewQuestion(
            category="岗位理解",
            question=(
                f"结合你的经历，你认为「{job.title}」这个岗位入职后前三个月"
                f"最需要解决的一个问题是什么？你会如何验证自己的判断？"
            ),
            intent="考察业务理解与目标拆解能力",
            difficulty="medium",
        )
    )

    return questions
