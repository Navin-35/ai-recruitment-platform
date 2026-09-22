from pydantic import BaseModel, ConfigDict


class JobRequirementBase(BaseModel):
    skill_name: str
    is_required: bool = True
    importance: str | None = None


class JobRequirementCreate(JobRequirementBase):
    pass


class JobRequirementUpdate(BaseModel):
    skill_name: str | None = None
    is_required: bool | None = None
    importance: str | None = None


class JobRequirementResponse(JobRequirementBase):
    id: int
    job_id: int

    model_config = ConfigDict(from_attributes=True)
