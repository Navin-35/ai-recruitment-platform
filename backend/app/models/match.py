from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.job import Job


class CandidateMatch(Base):
    __tablename__ = "candidate_matches"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id"),
        nullable=False,
    )

    semantic_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    skill_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    experience_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    project_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    education_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    final_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    matching_skills: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    missing_skills: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="matches",
    )

    candidate: Mapped["Candidate"] = relationship(
        "Candidate",
        back_populates="matches",
    )