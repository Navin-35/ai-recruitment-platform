from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CandidateCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    education: str | None = None
    experience: str | None = None
    skills: str | None = None
    projects: str | None = None
    certifications: str | None = None


class CandidateResponse(CandidateCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )