
import secrets
import threading
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import event, select

from app.infrastructure.database.database import SessionLocal
from app.modules.players.models import Player
from app.modules.users.models import User
from app.modules.users.service import get_or_create_discord_user


def test_simultaneous_discord_registrations():
    discord_id = "test_" + secrets.token_hex(12)

    second_ready = threading.Event()
    allow_second_insert = threading.Event()

    def second_connection():
        with SessionLocal() as db:

            @event.listens_for(db, "before_flush")
            def pause_before_insert(session, context, instances):
                if any(isinstance(obj, User) for obj in session.new):
                    second_ready.set()

                    if not allow_second_insert.wait(timeout=15):
                        raise TimeoutError("Timeout waiting for first transaction")

            user = get_or_create_discord_user(
                db,
                discord_id=discord_id,
                username="SecondConnection",
                avatar=None,
            )

            result = (user.id, user.player_id)
            db.commit()
            return result

    try:
        with SessionLocal() as db:
            first_user = get_or_create_discord_user(
                db,
                discord_id=discord_id,
                username="FirstConnection",
                avatar=None,
            )

            first_ids = (first_user.id, first_user.player_id)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(second_connection)

                try:
                    assert second_ready.wait(timeout=15)
                    db.commit()
                finally:
                    allow_second_insert.set()

                second_ids = future.result(timeout=15)

        assert first_ids == second_ids

        with SessionLocal() as db:
            users = db.scalars(
                select(User).where(User.discord_id == discord_id)
            ).all()

            assert len(users) == 1
            assert users[0].id == first_ids[0]

    finally:
        allow_second_insert.set()

        # Supprimer uniquement le compte fictif du test
        with SessionLocal() as db:
            user = db.scalar(
                select(User).where(User.discord_id == discord_id)
            )

            if user is not None:
                player_id = user.player_id

                db.delete(user)
                db.flush()

                player = db.get(Player, player_id)
                if player is not None:
                    db.delete(player)

                db.commit()
