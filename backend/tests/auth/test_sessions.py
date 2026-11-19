from datetime import timedelta
import secrets

import pytest

from app.infrastructure.database.database import SessionLocal
from app.modules.players.models import Player
from app.modules.users.models import User
from app.modules.auth.service import (
    create_session,
    get_valid_session,
    revoke_session,
    cleanup_expired_sessions,
)


@pytest.fixture
def test_user():
    db = SessionLocal()

    try:
        player = Player(primary_name="Test Session Pytest")
        db.add(player)
        db.flush()

        user = User(
            player_id=player.id,
            discord_id="test_" + secrets.token_hex(12),
            discord_username="test_pytest",
        )
        db.add(user)
        db.flush()

        yield db, user.id

    finally:
        db.rollback()
        db.close()


def test_create_and_read_session(test_user):
    db, user_id = test_user

    token = create_session(
        db,
        user_id=user_id,
        duration=timedelta(minutes=5),
    )

    session = get_valid_session(db, token)

    assert session is not None
    assert session.user_id == user_id


def test_unknown_token_is_rejected(test_user):
    db, _ = test_user

    assert get_valid_session(db, "unknown_token") is None


def test_expired_session_is_rejected(test_user):
    db, user_id = test_user

    token = create_session(
        db,
        user_id=user_id,
        duration=timedelta(seconds=-1),
    )

    assert get_valid_session(db, token) is None


def test_revoke_session(test_user):
    db, user_id = test_user

    token = create_session(
        db,
        user_id=user_id,
        duration=timedelta(minutes=5),
    )

    assert get_valid_session(db, token) is not None

    assert revoke_session(db, token) is True
    assert get_valid_session(db, token) is None
    assert revoke_session(db, token) is False

def test_cleanup_expired_sessions(test_user):
    db, user_id = test_user

    # Une session expirée
    expired_token = create_session(
        db,
        user_id=user_id,
        duration=timedelta(seconds=-60),
    )

    # Une session encore valide
    valid_token = create_session(
        db,
        user_id=user_id,
        duration=timedelta(hours=1),
    )

    deleted = cleanup_expired_sessions(db)

    assert deleted >= 1

    assert get_valid_session(db, expired_token) is None
    assert get_valid_session(db, valid_token) is not None