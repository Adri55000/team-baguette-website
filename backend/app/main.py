
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine


app = FastAPI(
    title="Team Baguette API",
    version="0.1.0",
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "team-baguette-backend",
    }


@app.get("/api/health/db")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )
