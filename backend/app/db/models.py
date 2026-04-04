from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

user_interests = Table(
    "user_interests",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("interest_id", ForeignKey("interests.id"), primary_key=True),
)


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    users = relationship(
        "User",
        secondary=user_interests,
        back_populates="interests",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    otp_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    about: Mapped[str | None] = mapped_column(Text, nullable=True)
    telegram: Mapped[str | None] = mapped_column(String(320), nullable=True)

    interests = relationship(
        "Interest",
        secondary=user_interests,
        back_populates="users",
    )
