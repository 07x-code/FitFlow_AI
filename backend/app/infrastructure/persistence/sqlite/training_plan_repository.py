import sqlite3
from pathlib import Path

from app.domain.models import SafetyCheckResult, TrainingPlanDraft, TrainingPlanHistoryItem
from app.infrastructure.persistence.sqlite.profile_repository import DEFAULT_DB_PATH


class TrainingPlanRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def save(
        self,
        user_id: str,
        plan: TrainingPlanDraft,
        safety_check: SafetyCheckResult,
    ) -> TrainingPlanHistoryItem:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO training_plans (user_id, plan_json, safety_check_json, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, plan.model_dump_json(), safety_check.model_dump_json()),
            )
            row = connection.execute(
                """
                SELECT id, plan_json, safety_check_json, created_at
                FROM training_plans
                WHERE id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()

        return self._row_to_history_item(row)

    def list_by_user(self, user_id: str) -> list[TrainingPlanHistoryItem]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, plan_json, safety_check_json, created_at
                FROM training_plans
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (user_id,),
            ).fetchall()

        return [self._row_to_history_item(row) for row in rows]

    def get_by_id_for_user(
        self,
        user_id: str,
        plan_id: int,
    ) -> TrainingPlanHistoryItem | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, plan_json, safety_check_json, created_at
                FROM training_plans
                WHERE user_id = ? AND id = ?
                """,
                (user_id, plan_id),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_history_item(row)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS training_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    safety_check_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_training_plans_user_id_id
                ON training_plans (user_id, id)
                """
            )

    def _row_to_history_item(self, row: tuple[int, str, str, str]) -> TrainingPlanHistoryItem:
        return TrainingPlanHistoryItem(
            id=row[0],
            plan=TrainingPlanDraft.model_validate_json(row[1]),
            safety_check=SafetyCheckResult.model_validate_json(row[2]),
            created_at=row[3],
        )
