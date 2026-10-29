from datetime import date, datetime
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Task(Base):
    __tablename__ = 'tasks'
    __table_args__ = (CheckConstraint("status IN ('todo', 'in_progress', 'blocked', 'done')", name='ck_tasks_status'), CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='ck_tasks_priority'))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='todo', server_default='todo', index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default='medium', server_default='medium', index=True)
    due_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    project = relationship('Project', back_populates='tasks')
