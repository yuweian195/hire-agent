"""Skill extraction and matching.

The skill library is intentionally explicit: it keeps extraction deterministic and
easy to audit, which matters more than recall for a screening pipeline.
"""

from __future__ import annotations

import re

from app.schemas import SkillMatch

SKILL_LIBRARY: dict[str, list[str]] = {
    "Java": ["java"],
    "Spring Boot": ["spring boot", "springboot", "spring-boot"],
    "Spring Cloud": ["spring cloud", "springcloud", "spring-cloud"],
    "MySQL": ["mysql"],
    "Redis": ["redis"],
    "Kafka": ["kafka"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "微服务": ["微服务", "microservice", "microservices"],
    "高并发": ["高并发", "高吞吐", "高性能"],
    "分布式事务": ["分布式事务"],
    "Python": ["python"],
    "FastAPI": ["fastapi"],
    "LangGraph": ["langgraph"],
    "LangChain": ["langchain"],
    "RAG": ["rag", "检索增强", "retrieval-augmented"],
    "向量数据库": ["向量数据库", "milvus", "faiss", "chroma", "pgvector", "qdrant"],
    "Prompt Engineering": ["prompt engineering", "提示词工程", "prompt 工程"],
    "LLM": ["llm", "大模型", "大语言模型"],
    "评测": ["评测", "离线评估", "evaluation", "evals"],
    "React": ["react"],
    "TypeScript": ["typescript"],
    "Node.js": ["node.js", "nodejs"],
    "Vue": ["vue"],
    "Go": ["golang", "go 语言"],
    "C++": ["c++"],
    "数据分析": ["数据分析", "pandas"],
    "项目管理": ["项目管理", "团队管理"],
    "开源": ["开源", "open source"],
    "论文": ["论文", "paper"],
    "专利": ["专利"],
}


def _contains(text: str, alias: str) -> bool:
    """ASCII aliases must match as whole tokens to avoid 'go' inside 'good'."""
    if re.search(r"[a-zA-Z]", alias):
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(alias) + r"(?![a-zA-Z0-9])"
        return bool(re.search(pattern, text, flags=re.IGNORECASE))
    return alias.lower() in text.lower()


def extract_skills(text: str) -> list[str]:
    found: list[str] = []
    for canonical, aliases in SKILL_LIBRARY.items():
        if any(_contains(text, alias) for alias in aliases):
            found.append(canonical)
    return found


def match_skills(
    candidate_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
) -> SkillMatch:
    candidate = set(candidate_skills)
    required = [s for s in required_skills if s]
    preferred = [s for s in preferred_skills if s]

    matched = [s for s in required if s in candidate]
    missing = [s for s in required if s not in candidate]
    preferred_matched = [s for s in preferred if s in candidate]

    required_rate = len(matched) / len(required) if required else 1.0
    preferred_rate = len(preferred_matched) / len(preferred) if preferred else 1.0
    overall = 0.75 * required_rate + 0.25 * preferred_rate

    return SkillMatch(
        overall_rate=round(overall, 4),
        required_rate=round(required_rate, 4),
        preferred_rate=round(preferred_rate, 4),
        matched=matched,
        missing=missing,
        preferred_matched=preferred_matched,
    )
