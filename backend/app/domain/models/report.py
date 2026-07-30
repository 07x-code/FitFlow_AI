from pydantic import BaseModel

from app.domain.models.proposal import TrainingPlanProposalResponse


class WeeklyReportMetrics(BaseModel):
    """训练周报指标。"""

    session_count: int
    completed_sessions: int
    completion_rate: float
    average_rpe: float | None = None
    average_fatigue: float | None = None
    max_pain: int | None = None


class WeeklyReportResponse(BaseModel):
    """训练周报响应。"""

    metrics: WeeklyReportMetrics
    recommendation: str
    adjustment_proposal: TrainingPlanProposalResponse | None = None
