from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.job import Job


class VectorType(TypeDecorator):
    """
    Multi-dialect vector type:
    - On PostgreSQL: utilizes pgvector's native `VECTOR(768)`
    - On SQLite (testing/local): transparently stores vectors as JSON arrays
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int = 768, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        return list(value)

    def process_result_value(self, value: Any, dialect) -> Any:
        if value is None:
            return None
        return list(value)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # 'resume' or 'job_description'

    document_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    job_id: Mapped[int | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    section: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="general",
        index=True,
    )  # 'experience', 'skills', 'education', 'projects', 'requirements'

    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )  # For page-level citations

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    embedding: Mapped[List[float] | None] = mapped_column(
        VectorType(768),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    candidate: Mapped["Candidate | None"] = relationship("Candidate", back_populates="chunks")
    job: Mapped["Job | None"] = relationship("Job", back_populates="chunks")
