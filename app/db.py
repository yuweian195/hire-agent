"""SQLite persistence for screening and interview records."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from app.config import get_settings


class ScreeningRepository:
    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = Path(database_path or get_settings().database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _init_schema(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS screenings (
                    id TEXT PRIMARY KEY,
                    candidate_name TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    total_score REAL NOT NULL,
                    recommendation TEXT NOT NULL,
                    match_rate REAL NOT NULL,
                    stage TEXT NOT NULL DEFAULT 'screening',
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(screenings)")
            }
            if "stage" not in columns:
                connection.execute(
                    "ALTER TABLE screenings ADD COLUMN stage TEXT NOT NULL DEFAULT 'screening'"
                )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_screenings_created_at "
                "ON screenings(created_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_screenings_stage "
                "ON screenings(stage)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS interview_reports (
                    id TEXT PRIMARY KEY,
                    candidate_name TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    recommendation TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_interviews_created_at "
                "ON interview_reports(created_at DESC)"
            )

    def save(self, record: dict[str, Any]) -> None:
        payload = record.get("payload", record)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO screenings
                (id, candidate_name, job_id, job_title, total_score,
                 recommendation, match_rate, stage, created_at, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    record["candidate_name"],
                    record["job_id"],
                    record["job_title"],
                    float(record["total_score"]),
                    record["recommendation"],
                    float(record["match_rate"]),
                    record.get("stage", "screening"),
                    record["created_at"],
                    json.dumps(payload, ensure_ascii=False, default=str),
                ),
            )

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                """
                SELECT id, candidate_name, job_id, job_title, total_score,
                       recommendation, match_rate, stage, created_at
                FROM screenings ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, screening_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                "SELECT payload FROM screenings WHERE id = ?", (screening_id,)
            ).fetchone()
        if not row:
            return None
        return json.loads(row["payload"])

    def update_stage(self, screening_id: str, stage: str) -> bool:
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                "SELECT payload FROM screenings WHERE id = ?", (screening_id,)
            ).fetchone()
            if not row:
                return False
            payload = json.loads(row["payload"])
            payload["stage"] = stage
            connection.execute(
                "UPDATE screenings SET stage = ?, payload = ? WHERE id = ?",
                (stage, json.dumps(payload, ensure_ascii=False, default=str), screening_id),
            )
        return True

    def count(self) -> int:
        with closing(self._connect()) as connection, connection:
            row = connection.execute("SELECT COUNT(*) AS n FROM screenings").fetchone()
        return int(row["n"])

    def save_interview(self, record: dict[str, Any]) -> None:
        payload = record.get("payload", record)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO interview_reports
                (id, candidate_name, job_id, job_title, overall_score,
                 recommendation, created_at, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    record["candidate_name"],
                    record["job_id"],
                    record["job_title"],
                    float(record["overall_score"]),
                    record["recommendation"],
                    record["created_at"],
                    json.dumps(payload, ensure_ascii=False, default=str),
                ),
            )

    def list_interviews(self, limit: int = 20) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                """
                SELECT id, candidate_name, job_id, job_title, overall_score,
                       recommendation, created_at
                FROM interview_reports ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_interview(self, report_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                "SELECT payload FROM interview_reports WHERE id = ?", (report_id,)
            ).fetchone()
        if not row:
            return None
        return json.loads(row["payload"])


_repository: ScreeningRepository | None = None


def get_repository() -> ScreeningRepository:
    global _repository
    if _repository is None:
        _repository = ScreeningRepository()
    return _repository
