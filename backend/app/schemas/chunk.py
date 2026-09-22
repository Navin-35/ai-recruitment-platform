from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentChunkBase(BaseModel):
    document_type: str = Field(..., description="Document type: 'resume' or 'job_description'")
    document_id: int
    candidate_id: Optional[int] = None
    job_id: Optional[int] = None
    section: str = Field(default="general", description="Section: 'experience', 'skills', 'education', 'projects', 'requirements'")
    page_number: Optional[int] = Field(default=None, description="Source page number for evidence citation")
    content: str = Field(..., description="Raw text snippet")
    content_hash: Optional[str] = None


class DocumentChunkCreate(DocumentChunkBase):
    embedding: Optional[List[float]] = Field(default=None, description="768-dimensional embedding vector")


class DocumentChunkResponse(DocumentChunkBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChunkSearchQuery(BaseModel):
    query_text: str
    top_k: int = Field(default=5, ge=1, le=50)
    candidate_id: Optional[int] = None
    job_id: Optional[int] = None
    section: Optional[str] = None


class ChunkSearchResult(BaseModel):
    chunk: DocumentChunkResponse
    similarity_score: float
