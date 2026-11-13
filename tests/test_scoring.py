import pytest

from app.schemas import Recommendation, ScreenRequest
from app.tools.scorer import WEIGHTS


def test_dimension_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_stronger_candidate_scores_higher(service, read_resume):
    strong = service.screen(
        ScreenRequest(resume_text=read_resume("zhangwei.txt"), job_id="java-senior")
    )
    medium = service.screen(
        ScreenRequest(resume_text=read_resume("zhaomin.txt"), job_id="java-senior")
    )
    weak = service.screen(
        ScreenRequest(resume_text=read_resume("wangqiang.txt"), job_id="java-senior")
    )

    assert strong.total_score > medium.total_score > weak.total_score
    assert strong.recommendation == Recommendation.RECOMMEND
    assert medium.recommendation == Recommendation.HOLD
    assert weak.recommendation == Recommendation.REJECT


def test_six_dimensions_and_score_bounds(service, read_resume):
    result = service.screen(
        ScreenRequest(resume_text=read_resume("zhangwei.txt"), job_id="java-senior")
    )

    assert len(result.dimension_scores) == 6
    assert {item.key for item in result.dimension_scores} == set(WEIGHTS)
    assert all(1 <= item.score <= 10 for item in result.dimension_scores)
    assert 1 <= result.total_score <= 10
