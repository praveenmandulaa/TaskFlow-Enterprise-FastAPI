
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TeamMemberAdd(BaseModel):
    user_id: int = Field(gt=0)


class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    user_id: int
    role: str
    joined_at: datetime
