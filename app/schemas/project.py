from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator

class ProjectStatus(str, Enum):
    planned = 'planned'
    active = 'active'
    on_hold = 'on_hold'
    completed = 'completed'

class ProjectCreate(BaseModel):
    team_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    status: ProjectStatus = ProjectStatus.planned
    start_date: date | None = None
    due_date: date | None = None

    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_date and self.due_date and self.due_date < self.start_date:
            raise ValueError('due_date must be on or after start_date')
        return self

class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    due_date: date | None = None

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    team_id: int
    created_by: int
    name: str
    description: str | None
    status: ProjectStatus
    start_date: date | None
    due_date: date | None
    created_at: datetime
    updated_at: datetime

class ProjectPage(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int
