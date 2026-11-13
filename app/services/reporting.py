"""Markdown report rendering for screening and interview results."""

from __future__ import annotations

from app.schemas import InterviewReport, ScreeningResponse

_REC_LABEL = {"recommend": "推荐", "hold": "待定", "reject": "淘汰"}
_INTERVIEW_LABEL = {"pass": "通过", "hold": "待定", "reject": "不通过"}


def screening_markdown(result: ScreeningResponse) -> str:
    lines = [
        f"# 候选人筛选报告：{result.candidate_name}",
        "",
        f"- 应聘岗位：{result.job_title}",
        f"- 综合评分：**{result.total_score:.2f}/10**",
        f"- 筛选结论：**{_REC_LABEL.get(result.recommendation.value, result.recommendation.value)}**",
        f"- JD 匹配度：{result.job_match.overall_rate:.0%}",
        f"- 必备技能命中：{result.skill_match.required_rate:.0%}",
        f"- 流程状态：{result.stage.value}",
        "",
        "## 六维评分",
        "",
        "| 维度 | 分数 | 权重 | 说明 |",
        "|---|---:|---:|---|",
    ]
    for item in result.dimension_scores:
        lines.append(f"| {item.label} | {item.score:.1f} | {item.weight:.0%} | {item.reason} |")
    lines += [
        "",
        "## 技能覆盖",
        "",
        f"- 已命中：{'、'.join(result.skill_match.matched) or '无'}",
        f"- 缺失：{'、'.join(result.skill_match.missing) or '无'}",
        "",
        "## 筛选结论",
        "",
        result.summary or result.recommendation_reason,
        "",
    ]
    if result.questions:
        lines += ["## 建议面试题", ""]
        for index, question in enumerate(result.questions, start=1):
            lines.append(f"{index}. **{question.category}**：{question.question}")
            if question.intent:
                lines.append(f"   - 考察意图：{question.intent}")
    return "\n".join(lines) + "\n"


def interview_markdown(report: InterviewReport) -> str:
    lines = [
        f"# 面试评估报告：{report.candidate_name}",
        "",
        f"- 应聘岗位：{report.job_title}",
        f"- 面试平均分：**{report.overall_score:.2f}/10**",
        f"- 面试结论：**{_INTERVIEW_LABEL.get(report.recommendation.value, report.recommendation.value)}**",
        "",
        "## 总体评价",
        "",
        report.summary,
        "",
        "## 逐题评估",
        "",
    ]
    for index, item in enumerate(report.answer_evaluations, start=1):
        dimensions = "；".join(f"{key} {value:.1f}" for key, value in item.dimensions.items())
        lines += [
            f"### {index}. {item.question}",
            "",
            f"- 得分：**{item.score:.2f}/10**",
            f"- 维度：{dimensions}",
            f"- 优势：{'；'.join(item.strengths) or '无'}",
            f"- 风险：{'；'.join(item.weaknesses) or '无'}",
            f"- 追问建议：{item.follow_up}",
            "",
        ]
    return "\n".join(lines) + "\n"
