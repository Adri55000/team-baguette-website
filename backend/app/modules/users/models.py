from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("players.id"),
        unique=True,
        nullable=False,
    )

    # Identité Discord
    discord_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
    )

    discord_username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    discord_avatar: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Profil public
    avatar_upload_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("uploads.id", use_alter=True, name="fk_users_avatar_upload_id"),
        nullable=True,
    )

    pronouns: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    nationality: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
    )

    # Préférences
    language: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    timezone: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
