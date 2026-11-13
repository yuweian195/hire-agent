"""Batch screen a directory of resumes and export a ranked CSV.

Usage:
    python scripts/batch_screen.py --job java-senior --input data/resumes \
        --output reports/batch_results.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas import BatchScreenRequest  # noqa: E402
from app.services.screening import get_service  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch screen resumes against one job.")
    parser.add_argument("--job", required=True, help="Job id, e.g. java-senior")
    parser.add_argument("--input", default=str(ROOT / "data" / "resumes"))
    parser.add_argument("--output", default=str(ROOT / "reports" / "batch_results.csv"))
    parser.add_argument("--pattern", default="*.txt")
    args = parser.parse_args()

    input_dir = Path(args.input)
    files = sorted(input_dir.glob(args.pattern))
    if not files:
        raise SystemExit(f"No resumes found in {input_dir} with pattern {args.pattern}")

    service = get_service()
    payload = BatchScreenRequest(
        job_id=args.job,
        resume_texts=[path.read_text(encoding="utf-8") for path in files],
    )
    result = service.screen_batch(payload)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["排名", "候选人", "综合评分", "结论", "匹配度", "缺失技能", "筛选编号"])
        for item in result.items:
            screening = item.screening
            writer.writerow(
                [
                    item.rank,
                    screening.candidate_name,
                    f"{screening.total_score:.2f}",
                    screening.recommendation.value,
                    f"{screening.job_match.overall_rate:.0%}",
                    "、".join(screening.skill_match.missing),
                    screening.id,
                ]
            )

    print(f"岗位：{result.job_title}｜共 {result.total} 份简历")
    for item in result.items:
        screening = item.screening
        print(
            f"{item.rank:>2}. {screening.candidate_name:<6} "
            f"{screening.total_score:5.2f}  {screening.recommendation.value:<9} "
            f"匹配 {screening.job_match.overall_rate:.0%}"
        )
    print(f"\nCSV written to {output}")


if __name__ == "__main__":
    main()
