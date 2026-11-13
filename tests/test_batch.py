from app.schemas import BatchScreenRequest, ScreeningStage, ScreenRequest
from app.services.reporting import screening_markdown


def test_batch_screening_is_ranked(service, read_resume):
    result = service.screen_batch(
        BatchScreenRequest(
            job_id="java-senior",
            resume_texts=[
                read_resume("zhaomin.txt"),
                read_resume("zhangwei.txt"),
                read_resume("wangqiang.txt"),
            ],
        )
    )

    assert result.total == 3
    assert [item.rank for item in result.items] == [1, 2, 3]
    scores = [item.screening.total_score for item in result.items]
    assert scores == sorted(scores, reverse=True)
    assert result.items[0].screening.candidate_name == "张伟"


def test_stage_can_be_updated(service, read_resume):
    result = service.screen(
        ScreenRequest(resume_text=read_resume("zhangwei.txt"), job_id="java-senior")
    )

    updated = service.update_stage(result.id, ScreeningStage.INTERVIEW)
    assert updated is not None
    assert updated.stage == ScreeningStage.INTERVIEW

    loaded = service.get_screening(result.id)
    assert loaded is not None
    assert loaded.stage == ScreeningStage.INTERVIEW


def test_markdown_report_contains_key_sections(service, read_resume):
    result = service.screen(
        ScreenRequest(resume_text=read_resume("zhangwei.txt"), job_id="java-senior")
    )

    markdown = screening_markdown(result)
    assert "# 候选人筛选报告：张伟" in markdown
    assert "## 六维评分" in markdown
    assert "## 技能覆盖" in markdown
    assert "## 建议面试题" in markdown
