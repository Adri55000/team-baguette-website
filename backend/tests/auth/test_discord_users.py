import secrets

import pytest

from app.infrastructure.database.database import SessionLocal
from app.modules.players.models import Player
from app.modules.users.models import User
from app.modules.users.service import get_or_create_discord_user


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_first_discord_login_creates_user_and_player(db):
    discord_id = "test_" + secrets.token_hex(12)

    user = get_or_create_discord_user(
        db,
        discord_id=discord_id,
        username="BaguetteTest",
        avatar="avatar_initial",
    )

    assert user.id is not None
    assert user.discord_id == discord_id
    assert user.discord_username == "BaguetteTest"

    player = db.get(Player, user.player_id)

    assert player is not None
    assert player.primary_name == "BaguetteTest"


def test_discord_reconnection_keeps_same_account(db):
    discord_id = "test_" + secrets.token_hex(12)

    user = get_or_create_discord_user(
        db,
        discord_id=discord_id,
        username="PseudoInitial",
        avatar="ancien_avatar",
    )

    user_id = user.id
    player_id = user.player_id

    reconnected_user = get_or_create_discord_user(
        db,
        discord_id=discord_id,
        username="NouveauPseudo",
        avatar="nouvel_avatar",
    )

    assert reconnected_user.id == user_id
    assert reconnected_user.player_id == player_id
    assert reconnected_user.discord_username == "NouveauPseudo"
    assert reconnected_user.discord_avatar == "nouvel_avatar"


def test_discord_reconnection_preserves_player_name(db):
    discord_id = "test_" + secrets.token_hex(12)

    user = get_or_create_discord_user(
        db,
        discord_id=discord_id,
        username="PseudoDiscord",
        avatar=None,
    )

    player = db.get(Player, user.player_id)
    assert player is not None

    player.primary_name = "Nom Sportif Personnalise"
    db.flush()

    get_or_create_discord_user(
        db,
        discord_id=discord_id,
        username="DiscordRenomme",
        avatar=None,
    )

    db.refresh(player)

    assert player.primary_name == "Nom Sportif Personnalise"


def test_discord_reconnection_does_not_duplicate_users(db):
    discord_id = "test_" + secrets.token_hex(12)

    first = get_or_create_discord_user(
        db, discord_id, "Pseudo1", None
    )
    second = get_or_create_discord_user(
        db, discord_id, "Pseudo2", None
    )

    assert first.id == second.id
    assert first.player_id == second.player_id
