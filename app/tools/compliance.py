"""JD compliance checks.

Recruiting JDs often contain requirements that are unrelated to the job and
carry legal risk (gender, age, marital status, household registration...).
The pipeline flags them and strips them before any matching happens.
"""

from __future__ import annotations

import re

from app.schemas import ComplianceResult

_PATTERNS: list[tuple[str, str]] = [
    (r"(限|仅限|要求)(男性|女性)", "性别限制"),
    (r"(男性优先|女性优先|男士优先|女士优先)", "性别偏好"),
    (r"(年龄\s*)?(不超过|低于|小于)\s*\d{2}\s*岁", "年龄限制"),
    (r"\d{2}\s*岁(以下|以内)", "年龄限制"),
    (r"第一学历.*(985|211|双一流|统招)", "第一学历限制"),
    (r"(已婚已育|未婚|婚姻状况|生育状况|婚育)", "婚育状况询问"),
    (r"(本地户口|户籍限|限.*户籍)", "户籍限制"),
]


def check_jd_compliance(jd_text: str) -> ComplianceResult:
    issues: list[str] = []
    for pattern, label in _PATTERNS:
        if re.search(pattern, jd_text):
            if label not in issues:
                issues.append(label)

    if not issues:
        return ComplianceResult(passed=True, issues=[], sanitized_text=jd_text)

    # Remove sentences containing a flagged pattern.
    sentences = re.split(r"(?<=[。；;\n])", jd_text)
    kept: list[str] = []
    for sentence in sentences:
        if any(re.search(pattern, sentence) for pattern, _ in _PATTERNS):
            continue
        kept.append(sentence)

    return ComplianceResult(
        passed=False,
        issues=issues,
        sanitized_text="".join(kept).strip(),
    )
