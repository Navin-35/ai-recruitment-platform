from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.job_requirement import JobRequirementResponse


class JobBase(BaseModel):
    title: str
    company_name: str | None = None
    description: str
    location: str | None = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: str | None = None
    company_name: str | None = None
    description: str | None = None
    location: str | None = None
    status: str | None = None


class JobResponse(JobBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDetailResponse(JobResponse):
    requirements: list[JobRequirementResponse] = []