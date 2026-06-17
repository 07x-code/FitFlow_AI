from fastapi import FastAPI

from app.api.profiles import router as profiles_router


app = FastAPI(title="fitflow-api")
app.include_router(profiles_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "service": "fitflow-api",
        "status": "ok",
    }
