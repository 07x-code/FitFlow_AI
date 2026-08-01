import json
import sqlite3
from pathlib import Path

from pydantic import TypeAdapter

from app.domain.models import (
    WorkoutSafetyAlert,
    WorkoutSessionCreate,
    WorkoutSessionResponse,
    WorkoutSetLog,
)
from app.infrastructure.persistence.sqlite.profile_repository import DEFAULT_DB_PATH


class WorkoutSessionRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def save(
        self,
        user_id: str,
        plan_id: int,
        plan_day_name: str,
        session: WorkoutSessionCreate,
        safety_alert: WorkoutSafetyAlert | None,
    ) -> WorkoutSessionResponse:
        sets_json = json.dumps(
            [workout_set.model_dump() for workout_set in session.sets],
            ensure_ascii=False,
        )
        safety_alert_json = (
            safety_alert.model_dump_json() if safety_alert is not None else None
        )

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO workout_sessions (
                    user_id,
                    plan_id,
                    plan_day_index,
                    plan_day_name,
                    completed,
                    fatigue_level,
                    pain_level,
                    notes,
                    sets_json,
                    safety_alert_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    user_id,
                    plan_id,
                    session.plan_day_index,
                    plan_day_name,
                    int(session.completed),
                    session.fatigue_level,
                    session.pain_level,
                    session.notes,
                    sets_json,
                    safety_alert_json,
                ),
            )
            row = self._fetch_by_id(connection, cursor.lastrowid)

        return self._row_to_session(row)

    def list_by_user(
        self,
        user_id: str,
        plan_id: int | None = None,
    ) -> list[WorkoutSessionResponse]:
        query = """
            SELECT
                id,
                plan_id,
                plan_day_index,
                plan_day_name,
                completed,
                fatigue_level,
                pain_level,
                notes,
                sets_json,
                safety_alert_json,
                created_at
            FROM workout_sessions
            WHERE user_id = ?
        """
        parameters: tuple[str] | tuple[str, int] = (user_id,)
        if plan_id is not None:
            query += " AND plan_id = ?"
            parameters = (user_id, plan_id)

        query += " ORDER BY id DESC"

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [self._row_to_session(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workout_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    plan_id INTEGER NOT NULL,
                    plan_day_index INTEGER NOT NULL DEFAULT 1,
                    plan_day_name TEXT NOT NULL DEFAULT 'Day 1',
                    completed INTEGER NOT NULL,
                    fatigue_level INTEGER NOT NULL,
                    pain_level INTEGER NOT NULL,
                    notes TEXT,
                    sets_json TEXT NOT NULL,
                    safety_alert_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._ensure_column(
                connection,
                column_name="plan_day_index",
                definition="INTEGER NOT NULL DEFAULT 1",
            )
            self._ensure_column(
                connection,
                column_name="plan_day_name",
                definition="TEXT NOT NULL DEFAULT 'Day 1'",
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_id_id
                ON workout_sessions (user_id, id)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_plan_id
                ON workout_sessions (user_id, plan_id, id)
                """
            )

    @staticmethod
    def _ensure_column(
        connection: sqlite3.Connection,
        *,
        column_name: str,
        definition: str,
    ) -> None:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(workout_sessions)"
            ).fetchall()
        }
        if column_name not in columns:
            connection.execute(
                f"ALTER TABLE workout_sessions ADD COLUMN {column_name} {definition}"
            )

    def _fetch_by_id(
        self,
        connection: sqlite3.Connection,
        session_id: int,
    ) -> tuple:
        return connection.execute(
            """
            SELECT
                id,
                plan_id,
                plan_day_index,
                plan_day_name,
                completed,
                fatigue_level,
                pain_level,
                notes,
                sets_json,
                safety_alert_json,
                created_at
            FROM workout_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()

    def _row_to_session(
        self,
        row: tuple,
    ) -> WorkoutSessionResponse:
        sets = TypeAdapter(list[WorkoutSetLog]).validate_json(row[8])
        safety_alert = (
            WorkoutSafetyAlert.model_validate_json(row[9])
            if row[9] is not None
            else None
        )

        return WorkoutSessionResponse(
            id=row[0],
            plan_id=row[1],
            plan_day_index=row[2],
            plan_day_name=row[3],
            completed=bool(row[4]),
            fatigue_level=row[5],
            pain_level=row[6],
            notes=row[7],
            sets=sets,
            safety_alert=safety_alert,
            created_at=row[10],
        )
