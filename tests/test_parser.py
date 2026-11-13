from app.tools.resume_parser import decode_text, parse_resume


def test_parse_structured_resume(read_resume):
    parsed = parse_resume(read_resume("zhangwei.txt"))

    assert parsed.name == "张伟"
    assert parsed.email == "zhangwei@example.com"
    assert parsed.phone == "13800001234"
    assert parsed.education_level == "硕士"
    assert parsed.school == "浙江大学"
    assert parsed.school_tier == "985"
    assert parsed.years_experience == 6
    assert "Spring Cloud" in parsed.skills
    assert "Kubernetes" in parsed.skills
    assert len(parsed.projects) == 3
    assert len(parsed.work_history) == 2
    assert parsed.work_history[0].company == "某互联网公司"
    assert parsed.work_history[0].title == "高级 Java 工程师"


def test_work_history_does_not_include_education(read_resume):
    parsed = parse_resume(read_resume("chenchen.txt"))

    assert len(parsed.work_history) == 2
    assert all("大学" not in item.company for item in parsed.work_history)


def test_decode_plain_text():
    content = "测试简历".encode()
    assert decode_text("resume.txt", content) == "测试简历"
