from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class Task:
    id: int
    user_id: int
    title: str
    due_at_utc: datetime
    timezone: str
    status: str
    created_at: datetime
    reminded_at: datetime | None


class TaskStorage:
    def __init__(self, db_path: str = "tasks.db") -> None:
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    due_at_utc TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'scheduled',
                    created_at TEXT NOT NULL,
                    reminded_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_user_due
                ON tasks (user_id, due_at_utc);

                CREATE INDEX IF NOT EXISTS idx_tasks_status_due
                ON tasks (status, due_at_utc);
                """
            )

    def add_task(self, user_id: int, title: str, due_at_utc: datetime, timezone: str) -> int:
        now = datetime.utcnow().replace(microsecond=0)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (user_id, title, due_at_utc, timezone, status, created_at)
                VALUES (?, ?, ?, ?, 'scheduled', ?)
                """,
                (
                    user_id,
                    title.strip(),
                    due_at_utc.replace(microsecond=0).isoformat(),
                    timezone,
                    now.isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def get_task(self, task_id: int, user_id: int) -> Task | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, user_id),
            ).fetchone()
        return self._row_to_task(row) if row else None

    def list_tasks(self, user_id: int, limit: int = 10) -> list[Task]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE user_id = ? AND status = 'scheduled'
                ORDER BY due_at_utc ASC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def set_done(self, task_id: int, user_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE tasks
                SET status = 'done'
                WHERE id = ? AND user_id = ? AND status = 'scheduled'
                """,
                (task_id, user_id),
            )
            return cursor.rowcount > 0

    def delete_task(self, task_id: int, user_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, user_id),
            )
            return cursor.rowcount > 0

    def pending_due_tasks(self, now_utc: datetime) -> Iterable[Task]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE status = 'scheduled' AND due_at_utc <= ? AND reminded_at IS NULL
                ORDER BY due_at_utc ASC
                """,
                (now_utc.replace(microsecond=0).isoformat(),),
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def mark_reminded(self, task_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE tasks SET reminded_at = ? WHERE id = ?",
                (datetime.utcnow().replace(microsecond=0).isoformat(), task_id),
            )

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            due_at_utc=datetime.fromisoformat(row["due_at_utc"]),
            timezone=row["timezone"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            reminded_at=datetime.fromisoformat(row["reminded_at"]) if row["reminded_at"] else None,
        )
