from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.modules.auth.models import UserSession
from app.modules.auth.security import (
    generate_session_token,
    hash_session_token,
)


def create_session(
    db: Session,
    user_id: int,
    duration: timedelta,
) -> str:
    token = generate_session_token()

    session = UserSession(
        user_id=user_id,
        token_hash=hash_session_token(token),
        expires_at=datetime.now(timezone.utc) + duration,
    )

    db.add(session)
    db.flush()

    return token


def get_valid_session(
    db: Session,
    token: str,
) -> UserSession | None:
    if not token:
        return None

    token_hash = hash_session_token(token)

    statement = select(UserSession).where(
        UserSession.token_hash == token_hash,
        UserSession.expires_at > datetime.now(timezone.utc),
    )

    return db.scalar(statement)


def revoke_session(
    db: Session,
    token: str,
) -> bool:
    if not token:
        return False

    statement = select(UserSession).where(
        UserSession.token_hash == hash_session_token(token)
    )

    session = db.scalar(statement)

    if session is None:
        return False

    db.delete(session)
    db.flush()

    return True


def cleanup_expired_sessions(db: Session) -> int:
    statement = delete(UserSession).where(
        UserSession.expires_at <= datetime.now(timezone.utc)
    )

    result = db.execute(statement)

    return result.rowcount
