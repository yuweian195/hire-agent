"""Resume text extraction and rule-based structured parsing."""

from __future__ import annotations

import io
import re
from pathlib import Path

from app.schemas import ParsedResume, WorkExperience
from app.tools.skill_matcher import extract_skills

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(?<!\d)(1[3-9]\d[\d -]{8,11})(?!\d)")
_NAME_RE = re.compile(r"姓\s*名\s*[:：]\s*([^\s|｜，,]+)")
_YEARS_RE = re.compile(r"(?:工作年限|工作经验|从业年限)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*年")
_YEARS_ALT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*年(?:以上)?(?:工作)?经验")
_SCHOOL_RE = re.compile(r"([\u4e00-\u9fa5]{2,20}(?:大学|学院|学校))")

_EDUCATION_ORDER = ["博士", "硕士", "本科", "大专", "高中"]
_KEY_UNIVERSITIES_985 = [
    "清华大学",
    "北京大学",
    "浙江大学",
    "复旦大学",
    "上海交通大学",
    "南京大学",
    "中国科学技术大学",
    "华中科技大学",
    "武汉大学",
    "西安交通大学",
    "哈尔滨工业大学",
    "中山大学",
    "四川大学",
    "同济大学",
    "东南大学",
    "厦门大学",
]
_KEY_UNIVERSITIES_211 = [
    "北京邮电大学",
    "南京邮电大学",
    "西安电子科技大学",
    "北京交通大学",
    "上海大学",
    "苏州大学",
    "郑州大学",
    "暨南大学",
]

_WORK_RE = re.compile(
    r"^\s*(\d{4})[.\-/年](\d{1,2})?\s*[-–—至~]\s*"
    r"(\d{4}|至今)[.\-/年]?(\d{1,2})?\s+(.+)$"
)


def decode_text(filename: str, content: bytes) -> str:
    """Extract plain text from txt/md/pdf/docx uploads."""
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".pdf":
        return _read_pdf(content)
    if suffix == ".docx":
        return _read_docx(content)
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _read_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _read_docx(content: bytes) -> str:
    from docx import Document

    document = Document(io.BytesIO(content))
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.append("  ".join(cell.text.strip() for cell in row.cells))
    return "\n".join(parts)


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    return "\n".join(line.rstrip() for line in text.splitlines())


def _extract_name(text: str) -> str:
    match = _NAME_RE.search(text)
    if match:
        return match.group(1).strip()
    for line in text.splitlines()[:5]:
        candidate = line.strip()
        if (
            2 <= len(candidate) <= 4
            and not any(word in candidate for word in ("简历", "求职", "电话", "邮箱", "@"))
            and re.fullmatch(r"[\u4e00-\u9fa5·]{2,4}", candidate)
        ):
            return candidate
    return ""


def _extract_education(text: str) -> str:
    for level in _EDUCATION_ORDER:
        if level in text:
            return level
    return ""


def _extract_years(text: str) -> float:
    match = _YEARS_RE.search(text) or _YEARS_ALT_RE.search(text)
    if match:
        return float(match.group(1))

    # Fall back to summing reverse-chronological work ranges.
    total_months = 0
    for line in text.splitlines():
        match = _WORK_RE.match(line)
        if not match:
            continue
        start_year, start_month, end_year, end_month = match.groups()[:4]
        end_y = 2026 if end_year == "至今" else int(end_year)
        end_m = int(end_month) if end_month else 12
        total_months += max(0, (end_y - int(start_year)) * 12 + end_m - int(start_month or 1))
    return round(total_months / 12, 1) if total_months else 0.0


def _extract_work_history(text: str) -> list[WorkExperience]:
    lines = text.splitlines()
    start = -1
    for index, line in enumerate(lines):
        if re.search(r"工作经历|工作经验|职业经历", line):
            start = index + 1
            break

    candidates = lines[start:] if start >= 0 else lines
    history: list[WorkExperience] = []
    for line in candidates:
        stripped = line.strip()
        if start >= 0 and re.match(r"(项目经历|项目经验|教育背景|技能|自我评价|证书)", stripped):
            break
        if any(word in stripped for word in ("大学", "学院", "学校")):
            continue
        match = _WORK_RE.match(line)
        if not match:
            continue
        start_year, start_month, end_year, end_month, rest = match.groups()
        start_date = f"{start_year}-{int(start_month or 1):02d}"
        end = "至今" if end_year == "至今" else f"{end_year}-{int(end_month or 1):02d}"
        parts = [p.strip() for p in re.split(r"\s{2,}|\t|\|", rest) if p.strip()]
        company = parts[0] if parts else rest.strip()
        title = parts[1] if len(parts) > 1 else ""
        history.append(WorkExperience(company=company, title=title, start=start_date, end=end))
    return history


def _extract_projects(text: str) -> list[str]:
    lines = text.splitlines()
    start = -1
    for index, line in enumerate(lines):
        if re.search(r"项目(经历|经验)", line):
            start = index + 1
            break
    if start < 0:
        return []

    projects: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if re.match(r"(技能|工作经历|教育背景|自我评价|证书)", stripped):
            break
        match = re.match(r"^\d+[.、]\s*(.+)$", stripped)
        if match:
            projects.append(match.group(1).strip())
    return projects[:8]


def _extract_school(text: str) -> tuple[str, str]:
    match = _SCHOOL_RE.search(text)
    school = match.group(1) if match else ""
    tier = ""
    if any(name in text for name in _KEY_UNIVERSITIES_985) or "985" in text:
        tier = "985"
    elif any(name in text for name in _KEY_UNIVERSITIES_211) or "211" in text:
        tier = "211"
    return school, tier


def _extract_current_title(history: list[WorkExperience]) -> str:
    if not history:
        return ""
    for item in history:
        if item.end == "至今":
            return item.title
    return history[0].title


def parse_resume(text: str) -> ParsedResume:
    text = _normalize(text)
    history = _extract_work_history(text)
    school, school_tier = _extract_school(text)
    return ParsedResume(
        name=_extract_name(text),
        email=(_EMAIL_RE.search(text).group(0) if _EMAIL_RE.search(text) else ""),
        phone=(re.sub(r"[^\d]", "", _PHONE_RE.search(text).group(1)) if _PHONE_RE.search(text) else ""),
        education_level=_extract_education(text),
        school=school,
        school_tier=school_tier,
        years_experience=_extract_years(text),
        current_title=_extract_current_title(history),
        skills=extract_skills(text),
        projects=_extract_projects(text),
        work_history=history,
    )
