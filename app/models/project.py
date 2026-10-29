from datetime import date, datetime
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Project(Base):
    __tablename__ = 'projects'
    __table_args__ = (CheckConstraint("status IN ('planned', 'active', 'on_hold', 'completed')", name='ck_projects_status'), CheckConstraint('due_date IS NULL OR start_date IS NULL OR due_date >= start_date', name='ck_projects_dates'))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id', ondelete='CASCADE'), index=True, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='planned', server_default='planned', index=True)
    start_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    tasks = relationship('Task', back_populates='project', cascade='all, delete-orphan', passive_deletes=True)
