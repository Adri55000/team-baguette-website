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


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    storage_key: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
    )

    original_filename: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    mime_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    uploaded_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
