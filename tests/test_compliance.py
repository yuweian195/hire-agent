from app.tools.compliance import check_jd_compliance


def test_clean_jd_passes():
    jd = "招聘高级后端工程师，要求 5 年以上 Java 经验，熟悉 Spring Cloud 与 MySQL。"
    result = check_jd_compliance(jd)

    assert result.passed is True
    assert result.issues == []


def test_discriminatory_jd_is_flagged_and_sanitized():
    jd = (
        "招聘后端工程师。限男性，35岁以下。第一学历需为985。"
        "岗位职责：负责交易系统研发。"
    )
    result = check_jd_compliance(jd)

    assert result.passed is False
    assert "性别限制" in result.issues
    assert "年龄限制" in result.issues
    assert "第一学历限制" in result.issues
    assert "限男性" not in result.sanitized_text
    assert "交易系统研发" in result.sanitized_text
