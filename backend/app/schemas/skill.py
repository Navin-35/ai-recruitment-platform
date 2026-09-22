from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SkillBase(BaseModel):
    name: str
    category: str | None = None


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None


class SkillResponse(SkillBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
