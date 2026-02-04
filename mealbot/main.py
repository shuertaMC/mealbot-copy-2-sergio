from fastapi import FastAPI

app = FastAPI(
    title="Mealbot API",
    version="1.0.0",
    description="REST API for meal pairing service",
)


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}
