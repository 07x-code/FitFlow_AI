from fastapi import FastAPI

from app.api.coach import router as coach_router
from app.api.errors import register_application_error_handlers
from app.api.memories import router as memories_router
from app.api.profiles import router as profiles_router
from app.api.proposals import router as proposals_router
from app.api.reports import router as reports_router
from app.api.training_plans import router as training_plans_router
from app.api.workouts import router as workouts_router


app = FastAPI(title="fitflow-api")
register_application_error_handlers(app)
app.include_router(coach_router)
app.include_router(memories_router)
app.include_router(profiles_router)
app.include_router(proposals_router)
app.include_router(reports_router)
app.include_router(training_plans_router)
app.include_router(workouts_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "service": "fitflow-api",
        "status": "ok",
    }
