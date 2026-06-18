from fastapi import FastAPI

from app.api.profiles import router as profiles_router
from app.api.training_plans import router as training_plans_router


app = FastAPI(title="fitflow-api")
app.include_router(profiles_router)
app.include_router(training_plans_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "service": "fitflow-api",
        "status": "ok",
    }
