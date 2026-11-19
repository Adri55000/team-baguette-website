from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database.database import SessionLocal
from app.modules.auth.models import UserSession
from app.modules.auth.service import get_valid_session


def get_db():
    with SessionLocal() as db:
        yield db


def get_current_session(
    db: Annotated[Session, Depends(get_db)],
    session_token: Annotated[str | None, Cookie()] = None,
) -> UserSession | None:
    if session_token is None:
        return None

    return get_valid_session(db, session_token)
