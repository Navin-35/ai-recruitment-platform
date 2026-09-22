from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CandidateMatchBase(BaseModel):
    job_id: int
    candidate_id: int
    semantic_score: float = Field(default=0.0, ge=0.0, le=100.0)
    skill_score: float = Field(default=0.0, ge=0.0, le=100.0)
    experience_score: float = Field(default=0.0, ge=0.0, le=100.0)
    project_score: float = Field(default=0.0, ge=0.0, le=100.0)
    education_score: float = Field(default=0.0, ge=0.0, le=100.0)
    final_score: float = Field(default=0.0, ge=0.0, le=100.0)
    matching_skills: str | None = None
    missing_skills: str | None = None
    explanation: str | None = None


class CandidateMatchCreate(CandidateMatchBase):
    pass


class CandidateMatchResponse(CandidateMatchBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
