
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
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

    owner = relationship("User", foreign_keys=[owner_id])

    members = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
    )
