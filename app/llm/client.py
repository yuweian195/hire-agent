"""Optional LLM enrichment over any OpenAI-compatible chat endpoint.

The screening numbers never depend on the LLM.  When no API key is configured,
or the remote call fails, every method returns None and the caller falls back to
deterministic templates.
"""

from __future__ import annotations

import json
import logging
import re

from app.config import Settings, get_settings
from app.llm import prompts
from app.schemas import DimensionScore, InterviewQuestion, JobMatch, JobRequirements, ParsedResume

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = None
        if self.settings.llm_enabled:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self.settings.llm_api_key,
                base_url=self.settings.llm_base_url,
                timeout=self.settings.llm_timeout,
            )

    @property
    def enabled(self) -> bool:
        return self._client is not None

    @property
    def mode(self) -> str:
        return f"online:{self.settings.llm_model}" if self.enabled else "offline"

    def _chat(self, system: str, user: str, json_mode: bool = False) -> str | None:
        if not self._client:
            return None
        kwargs = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        try:
            if json_mode:
                try:
                    response = self._client.chat.completions.create(
                        **kwargs, response_format={"type": "json_object"}
                    )
                except Exception:
                    response = self._client.chat.completions.create(**kwargs)
            else:
                response = self._client.chat.completions.create(**kwargs)
            return (response.choices[0].message.content or "").strip() or None
        except Exception as exc:  # network / quota / provider incompatibility
            logger.warning("LLM call failed, falling back to rules: %s", exc)
            return None

    def summarize(
        self,
        parsed: ParsedResume,
        job: JobRequirements,
        dimensions: list[DimensionScore],
        job_match: JobMatch,
        total_score: float,
    ) -> str | None:
        dimension_text = "；".join(
            f"{item.label} {item.score}/10" for item in dimensions
        )
        user = prompts.SUMMARY_USER.format(
            job_title=job.title,
            job_requirements="、".join(job.required_skills),
            candidate_name="候选人" if self.settings.redact_pii else (parsed.name or "候选人"),
            education=parsed.education_level or "学历未识别",
            years=f"{parsed.years_experience:g}",
            skills="、".join(parsed.skills[:10]) or "未识别",
            dimensions=dimension_text,
            total_score=f"{total_score:.1f}",
            skill_analysis=job_match.analysis,
        )
        return self._chat(prompts.SUMMARY_SYSTEM, user)

    def generate_questions(
        self,
        parsed: ParsedResume,
        job: JobRequirements,
        missing_skills: list[str],
    ) -> list[InterviewQuestion] | None:
        user = prompts.QUESTIONS_USER.format(
            job_title=job.title,
            required_skills="、".join(job.required_skills),
            candidate_skills="、".join(parsed.skills[:12]) or "未识别",
            missing_skills="、".join(missing_skills) or "无",
            projects="；".join(parsed.projects[:3]) or "未识别",
        )
        content = self._chat(prompts.QUESTIONS_SYSTEM, user, json_mode=True)
        if not content:
            return None
        data = _parse_json(content)
        if not isinstance(data, list):
            return None
        questions: list[InterviewQuestion] = []
        for item in data[:6]:
            if not isinstance(item, dict) or not item.get("question"):
                continue
            try:
                questions.append(
                    InterviewQuestion(
                        category=str(item.get("category", "面试题")),
                        question=str(item["question"]),
                        intent=str(item.get("intent", "")),
                        difficulty=str(item.get("difficulty", "medium")),
                    )
                )
            except Exception:
                continue
        return questions or None

    def review_answer(
        self,
        question: str,
        answer: str,
        job: JobRequirements,
        dimensions: dict[str, float],
    ) -> dict | None:
        user = prompts.ANSWER_REVIEW_USER.format(
            job_title=job.title,
            required_skills="、".join(job.required_skills),
            question=question,
            answer=answer,
            dimensions="；".join(f"{key} {value}" for key, value in dimensions.items()),
        )
        content = self._chat(prompts.ANSWER_REVIEW_SYSTEM, user, json_mode=True)
        if not content:
            return None
        data = _parse_json(content)
        if not isinstance(data, dict):
            return None
        strengths = [str(item) for item in data.get("strengths", []) if str(item).strip()][:4]
        weaknesses = [str(item) for item in data.get("weaknesses", []) if str(item).strip()][:4]
        follow_up = str(data.get("follow_up", "")).strip()
        if not strengths and not weaknesses and not follow_up:
            return None
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "follow_up": follow_up,
        }

    def summarize_interview(
        self,
        candidate_name: str,
        job: JobRequirements,
        scores: list[float],
        overall: float,
        recommendation: str,
        strengths: list[str],
        weaknesses: list[str],
    ) -> str | None:
        safe_name = "候选人" if self.settings.redact_pii else candidate_name
        user = prompts.INTERVIEW_SUMMARY_USER.format(
            job_title=job.title,
            candidate_name=safe_name,
            scores="、".join(f"{score:.1f}" for score in scores),
            overall_score=f"{overall:.1f}",
            recommendation=recommendation,
            strengths="；".join(strengths[:3]) or "无明显优势",
            weaknesses="；".join(weaknesses[:3]) or "暂无明显风险",
        )
        return self._chat(prompts.INTERVIEW_SUMMARY_SYSTEM, user)


def _parse_json(content: str):
    content = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"(\[.*\]|\{.*\})", content, flags=re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
