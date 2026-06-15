from fastapi import FastAPI


app = FastAPI(title="fitflow-api")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "service": "fitflow-api",
        "status": "ok",
    }