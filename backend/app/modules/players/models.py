from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    primary_name: Mapped[str] = mapped_column(Text, nullable=False)

    racetime_name: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    racetime_user_id: Mapped[str | None] = mapped_column(
        Text,
        unique=True,
        nullable=True,
    )

    merged_into_player_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("players.id"),
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



class PlayerAlias(Base):
    __tablename__ = "player_aliases"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("players.id"),
        nullable=False,
        index=True,
    )

    alias: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
