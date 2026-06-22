import sqlite3
from pathlib import Path

from app.domain.models import (
    ProposalStatus,
    ProposalType,
    SafetyCheckResult,
    TrainingPlanDraft,
    TrainingPlanProposalResponse,
)
from app.infrastructure.profile_repository import DEFAULT_DB_PATH


class TrainingPlanProposalRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def create(
        self,
        user_id: str,
        plan: TrainingPlanDraft,
        safety_check: SafetyCheckResult,
    ) -> TrainingPlanProposalResponse:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO training_plan_proposals (
                    user_id,
                    proposal_type,
                    status,
                    plan_json,
                    safety_check_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    user_id,
                    ProposalType.TRAINING_PLAN.value,
                    ProposalStatus.PENDING.value,
                    plan.model_dump_json(),
                    safety_check.model_dump_json(),
                ),
            )
            row = self._fetch_by_id(connection, cursor.lastrowid)

        return self._row_to_proposal(row)

    def list_by_user(self, user_id: str) -> list[TrainingPlanProposalResponse]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    proposal_type,
                    status,
                    plan_json,
                    safety_check_json,
                    approved_plan_id,
                    decision_note,
                    created_at,
                    decided_at
                FROM training_plan_proposals
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (user_id,),
            ).fetchall()

        return [self._row_to_proposal(row) for row in rows]

    def get_by_id_for_user(
        self,
        user_id: str,
        proposal_id: int,
    ) -> TrainingPlanProposalResponse | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    proposal_type,
                    status,
                    plan_json,
                    safety_check_json,
                    approved_plan_id,
                    decision_note,
                    created_at,
                    decided_at
                FROM training_plan_proposals
                WHERE user_id = ? AND id = ?
                """,
                (user_id, proposal_id),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_proposal(row)

    def approve(
        self,
        user_id: str,
        proposal_id: int,
        approved_plan_id: int,
        decision_note: str | None,
    ) -> TrainingPlanProposalResponse | None:
        return self._update_decision(
            user_id=user_id,
            proposal_id=proposal_id,
            status=ProposalStatus.APPROVED,
            approved_plan_id=approved_plan_id,
            decision_note=decision_note,
        )

    def reject(
        self,
        user_id: str,
        proposal_id: int,
        decision_note: str | None,
    ) -> TrainingPlanProposalResponse | None:
        return self._update_decision(
            user_id=user_id,
            proposal_id=proposal_id,
            status=ProposalStatus.REJECTED,
            approved_plan_id=None,
            decision_note=decision_note,
        )

    def _update_decision(
        self,
        *,
        user_id: str,
        proposal_id: int,
        status: ProposalStatus,
        approved_plan_id: int | None,
        decision_note: str | None,
    ) -> TrainingPlanProposalResponse | None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE training_plan_proposals
                SET
                    status = ?,
                    approved_plan_id = ?,
                    decision_note = ?,
                    decided_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND id = ?
                """,
                (
                    status.value,
                    approved_plan_id,
                    decision_note,
                    user_id,
                    proposal_id,
                ),
            )
            if cursor.rowcount == 0:
                return None

            row = self._fetch_by_id(connection, proposal_id)

        if row is None:
            return None

        return self._row_to_proposal(row)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS training_plan_proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    proposal_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    safety_check_json TEXT NOT NULL,
                    approved_plan_id INTEGER,
                    decision_note TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    decided_at TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_training_plan_proposals_user_id_id
                ON training_plan_proposals (user_id, id)
                """
            )

    def _fetch_by_id(
        self,
        connection: sqlite3.Connection,
        proposal_id: int,
    ) -> tuple[int, str, str, str, str, int | None, str | None, str, str | None] | None:
        return connection.execute(
            """
            SELECT
                id,
                proposal_type,
                status,
                plan_json,
                safety_check_json,
                approved_plan_id,
                decision_note,
                created_at,
                decided_at
            FROM training_plan_proposals
            WHERE id = ?
            """,
            (proposal_id,),
        ).fetchone()

    def _row_to_proposal(
        self,
        row: tuple[int, str, str, str, str, int | None, str | None, str, str | None],
    ) -> TrainingPlanProposalResponse:
        return TrainingPlanProposalResponse(
            id=row[0],
            type=ProposalType(row[1]),
            status=ProposalStatus(row[2]),
            plan=TrainingPlanDraft.model_validate_json(row[3]),
            safety_check=SafetyCheckResult.model_validate_json(row[4]),
            approved_plan_id=row[5],
            decision_note=row[6],
            created_at=row[7],
            decided_at=row[8],
        )
