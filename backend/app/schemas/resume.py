from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    id: int
    candidate_id: int
    filename: str
    file_path: str | None
    file_type: str | None
    processing_status: str
    extracted_text: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )