from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user_id, get_report_use_cases
from app.application.use_cases.reports import ReportUseCases
from app.domain.models import WeeklyReportResponse


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/weekly", response_model=WeeklyReportResponse)
async def create_weekly_report(
    user_id: Annotated[str, Depends(get_current_user_id)],
    use_cases: Annotated[ReportUseCases, Depends(get_report_use_cases)],
) -> WeeklyReportResponse:
    return await use_cases.create_weekly(user_id)
