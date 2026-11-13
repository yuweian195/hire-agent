"""Run the labelled evaluation set and write reports/evaluation.md.

Usage:
    python scripts/evaluate.py
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.db import ScreeningRepository  # noqa: E402
from app.llm.client import LLMClient  # noqa: E402
from app.schemas import ScreenRequest  # noqa: E402
from app.services.screening import ScreeningService  # noqa: E402


def main() -> None:
    labels = json.loads(
        (ROOT / "data" / "fixtures" / "eval_labels.json").read_text(encoding="utf-8")
    )

    with tempfile.TemporaryDirectory() as tmp:
        settings = Settings(llm_api_key="", database_path=Path(tmp) / "eval.db")
        service = ScreeningService(
            repository=ScreeningRepository(settings.database_path),
            llm=LLMClient(settings),
            jobs_dir=ROOT / "data" / "jobs",
        )

        rows: list[dict] = []
        for item in labels:
            text = (ROOT / "data" / "resumes" / item["resume"]).read_text(encoding="utf-8")
            started = time.perf_counter()
            result = service.screen(ScreenRequest(resume_text=text, job_id=item["job_id"]))
            latency_ms = (time.perf_counter() - started) * 1000
            in_range = item["score_min"] <= result.total_score <= item["score_max"]
            rows.append(
                {
                    "resume": item["resume"],
                    "job": result.job_title,
                    "expected": item["expected"],
                    "actual": result.recommendation.value,
                    "score": result.total_score,
                    "range": f"{item['score_min']}-{item['score_max']}",
                    "match": result.job_match.overall_rate,
                    "latency_ms": latency_ms,
                    "decision_ok": result.recommendation.value == item["expected"],
                    "score_ok": in_range,
                }
            )

    decision_hits = sum(row["decision_ok"] for row in rows)
    score_hits = sum(row["score_ok"] for row in rows)
    latencies = [row["latency_ms"] for row in rows]

    lines = [
        "# 离线评估报告",
        "",
        f"生成日期：{date.today().isoformat()}  ",
        "运行模式：离线规则（不调用外部 LLM）  ",
        f"样本数：{len(rows)}",
        "",
        "| 简历 | 岗位 | 期望结论 | 实际结论 | 分数 | 分数区间 | 匹配度 | 耗时 |",
        "|---|---|---|---|---:|---|---:|---:|",
    ]
    for row in rows:
        decision = "✅" if row["decision_ok"] else "❌"
        score = "✅" if row["score_ok"] else "❌"
        lines.append(
            f"| {row['resume']} | {row['job']} | {row['expected']} | "
            f"{row['actual']} {decision} | {row['score']:.2f} {score} | "
            f"{row['range']} | {row['match']:.0%} | {row['latency_ms']:.0f} ms |"
        )

    lines += [
        "",
        "## 汇总",
        "",
        f"- 决策准确率：**{decision_hits}/{len(rows)}（{decision_hits / len(rows):.0%}）**",
        f"- 分数区间命中：**{score_hits}/{len(rows)}（{score_hits / len(rows):.0%}）**",
        f"- 平均单份耗时：**{statistics.mean(latencies):.0f} ms**",
        f"- P95 耗时：**{sorted(latencies)[min(len(latencies) - 1, math.ceil(len(latencies) * 0.95) - 1)]:.0f} ms**",
        "",
        "> 评估集为合成简历，标签由人工按岗位要求标注；分数区间用于检查评分量级是否合理。",
    ]

    report = "\n".join(lines) + "\n"
    output = ROOT / "reports" / "evaluation.md"
    output.parent.mkdir(exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)
    print(f"written to {output}")


if __name__ == "__main__":
    main()
