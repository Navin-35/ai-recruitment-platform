from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.resume import ResumeResponse


class CandidateBase(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    education: str | None = None
    experience: str | None = None
    skills: str | None = None
    projects: str | None = None
    certifications: str | None = None


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    education: str | None = None
    experience: str | None = None
    skills: str | None = None
    projects: str | None = None
    certifications: str | None = None


class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateDetailResponse(CandidateResponse):
    resumes: list[ResumeResponse] = []