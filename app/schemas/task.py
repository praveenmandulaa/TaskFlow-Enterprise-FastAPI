from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class TaskStatus(str, Enum):
    todo = 'todo'
    in_progress = 'in_progress'
    blocked = 'blocked'
    done = 'done'

class TaskPriority(str, Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    urgent = 'urgent'

class TaskCreate(BaseModel):
    project_id: int = Field(gt=0)
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    assignee_id: int | None = Field(default=None, gt=0)
    due_date: date | None = None

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: int | None = Field(default=None, gt=0)
    due_date: date | None = None

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    created_by: int
    assignee_id: int | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    created_at: datetime
    updated_at: datetime

class TaskPage(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
    pages: int
