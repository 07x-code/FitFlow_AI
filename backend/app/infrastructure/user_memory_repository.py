import sqlite3
from pathlib import Path

from app.domain.models import UserMemoryCreate, UserMemoryResponse
from app.infrastructure.profile_repository import DEFAULT_DB_PATH


class UserMemoryRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def create(self, user_id: str, memory: UserMemoryCreate) -> UserMemoryResponse:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO user_memories (user_id, memory_type, content, source, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, memory.type, memory.content, memory.source),
            )
            row = connection.execute(
                """
                SELECT id, memory_type, content, source, created_at
                FROM user_memories
                WHERE id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()

        return self._row_to_response(row)

    def list_by_user(self, user_id: str) -> list[UserMemoryResponse]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, memory_type, content, source, created_at
                FROM user_memories
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (user_id,),
            ).fetchall()

        return [self._row_to_response(row) for row in rows]

    def delete_by_id_for_user(self, user_id: str, memory_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM user_memories
                WHERE user_id = ? AND id = ?
                """,
                (user_id, memory_id),
            )

        return cursor.rowcount > 0

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_memories_user_id_id
                ON user_memories (user_id, id)
                """
            )

    def _row_to_response(self, row: tuple[int, str, str, str, str]) -> UserMemoryResponse:
        return UserMemoryResponse(
            id=row[0],
            type=row[1],
            content=row[2],
            source=row[3],
            created_at=row[4],
        )