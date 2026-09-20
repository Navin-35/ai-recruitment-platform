from app.core.database import Base, engine

from app.models import (
    Candidate,
    CandidateMatch,
    Job,
    JobRequirement,
    Resume,
    Skill,
)


def init_database():
    Base.metadata.create_all(bind=engine)