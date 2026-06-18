import sqlite3
from pathlib import Path

from app.domain.models import FitnessProfileCreate


DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "fitflow.db"


class ProfileRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def save(self, user_id: str, profile: FitnessProfileCreate) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO fitness_profiles (user_id, profile_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    profile_json = excluded.profile_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, profile.model_dump_json()),
            )

    def get(self, user_id: str) -> FitnessProfileCreate | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT profile_json FROM fitness_profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        if row is None:
            return None

        return FitnessProfileCreate.model_validate_json(row[0])

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS fitness_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
