
from fastapi import FastAPI, HTTPException

import os
import psycopg

app = FastAPI(
    title="Team Baguette API",
    version="0.1.0"
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "team-baguette-backend",
        "reload": "active"
    }


@app.get("/api/health/db")
def database_health():
    try:
        with psycopg.connect(
            host=os.environ["POSTGRES_HOST"],
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            connect_timeout=3
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

        return {
            "status": "ok",
            "database": "connected"
        }

    except psycopg.OperationalError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )
