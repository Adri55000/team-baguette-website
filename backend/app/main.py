from fastapi import FastAPI

from app.core.config import settings
from app.modules.system.router import router as system_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(system_router, prefix="/api")
