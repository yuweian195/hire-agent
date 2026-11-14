"""Seed demo screenings so the TypeScript pipeline board is not empty.

Usage:
    python scripts/seed_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas import ScreeningStage, ScreenRequest  # noqa: E402
from app.services.screening import get_service  # noqa: E402

SAMPLES = [
    ("zhangwei.txt", "java-senior", ScreeningStage.INTERVIEW),
    ("zhaomin.txt", "java-senior", ScreeningStage.SCREENING),
    ("wangqiang.txt", "java-senior", ScreeningStage.REJECTED),
    ("chenchen.txt", "llm-app", ScreeningStage.OFFER),
]


def main() -> None:
    service = get_service()
    for filename, job_id, stage in SAMPLES:
        text = (ROOT / "data" / "resumes" / filename).read_text(encoding="utf-8")
        result = service.screen(ScreenRequest(resume_text=text, job_id=job_id))
        service.update_stage(result.id, stage)
        print(
            f"{result.candidate_name:<6} {result.total_score:5.2f} "
            f"{result.recommendation.value:<9} {stage.value}"
        )
    print(f"\n已写入 {service.repository.count()} 条筛选记录")


if __name__ == "__main__":
    main()
