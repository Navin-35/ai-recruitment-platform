from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    title: str
    company_name: str | None = None
    description: str
    location: str | None = None


class JobResponse(JobCreate):
    id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )