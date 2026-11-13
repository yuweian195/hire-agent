from app.schemas import Recommendation, ScreenRequest


def test_workflow_produces_trace_and_questions(service, read_resume):
    result = service.screen(
        ScreenRequest(resume_text=read_resume("zhangwei.txt"), job_id="java-senior")
    )

    assert result.recommendation == Recommendation.RECOMMEND
    assert result.total_score >= 8.0
    assert len(result.questions) == 5
    assert result.job_match.overall_rate >= 0.8

    nodes = [step.node for step in result.trace]
    assert nodes[0] == "parse_resume"
    assert nodes[-1] == "save_results"
    assert "generate_questions" in nodes
    assert nodes.index("generate_questions") < nodes.index("save_results")


def test_hold_candidate_skips_question_generation(service, read_resume):
    result = service.screen(
        ScreenRequest(resume_text=read_resume("zhaomin.txt"), job_id="java-senior")
    )

    assert result.recommendation == Recommendation.HOLD
    assert result.questions == []
    assert "generate_questions" not in [step.node for step in result.trace]


def test_custom_jd_text_is_supported(service, read_resume):
    jd = """
Python 后端工程师
3 年以上 Python 开发经验，熟悉 FastAPI、Redis 与 Docker。
薪资 25-35K。
"""
    result = service.screen(ScreenRequest(resume_text=read_resume("chenchen.txt"), jd_text=jd))

    assert result.job_id.startswith("custom-")
    assert result.total_score > 0
    assert "Python" in result.parsed_resume.skills


def test_screening_is_persisted_and_reloadable(service, read_resume):
    result = service.screen(
        ScreenRequest(resume_text=read_resume("zhangwei.txt"), job_id="java-senior")
    )

    loaded = service.get_screening(result.id)
    assert loaded is not None
    assert loaded.candidate_name == "张伟"
    assert loaded.total_score == result.total_score
    assert loaded.trace[-1].node == "save_results"

    recent = service.list_recent(limit=5)
    assert recent[0].id == result.id
    assert recent[0].candidate_name == "张伟"
