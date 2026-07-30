from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.api.dependencies import get_report_use_cases
from app.application.use_cases.reports import ReportUseCases
from app.domain.models import WeeklyReportResponse


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/weekly", response_model=WeeklyReportResponse)
def create_weekly_report(
    user_id: Annotated[str, Header(alias="X-User-ID")],
    use_cases: Annotated[ReportUseCases, Depends(get_report_use_cases)],
) -> WeeklyReportResponse:
    return use_cases.create_weekly(user_id)
