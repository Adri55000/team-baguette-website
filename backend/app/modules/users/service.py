from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.modules.players.models import Player
from app.modules.users.models import User


def get_or_create_discord_user(
    db: Session,
    discord_id: str,
    username: str,
    avatar: str | None,
) -> User:
    statement = select(User).where(
        User.discord_id == discord_id
    )

    user = db.scalar(statement)

    if user is not None:
        # Actualiser uniquement les données Discord
        user.discord_username = username
        user.discord_avatar = avatar
        db.flush()
        return user


    # Première connexion : tenter de créer le compte
    try:
        with db.begin_nested():
            player = Player(primary_name=username)
            db.add(player)
            db.flush()

            user = User(
                player_id=player.id,
                discord_id=discord_id,
                discord_username=username,
                discord_avatar=avatar,
            )
            db.add(user)
            db.flush()

    except IntegrityError as exc:
        # Ne traiter que le conflit sur l'identifiant Discord
        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None,
        )

        if constraint_name != "users_discord_id_key":
            raise

        # Une autre connexion vient de créer le compte
        user = db.scalar(
            select(User).where(User.discord_id == discord_id)
        )

        if user is None:
            raise

        user.discord_username = username
        user.discord_avatar = avatar
        db.flush()

    return user

