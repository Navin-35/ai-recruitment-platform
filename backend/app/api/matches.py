from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Candidate, CandidateMatch, Job
from app.schemas import CandidateMatchCreate, CandidateMatchResponse

router = APIRouter(
    prefix="/matches",
    tags=["Matches"],
)


@router.post(
    "/",
    response_model=CandidateMatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_candidate_match(
    match_data: CandidateMatchCreate,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == match_data.job_id).first()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    candidate = db.query(Candidate).filter(Candidate.id == match_data.candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    # If match already exists for this job and candidate, update it; otherwise create new
    existing_match = (
        db.query(CandidateMatch)
        .filter(
            CandidateMatch.job_id == match_data.job_id,
            CandidateMatch.candidate_id == match_data.candidate_id,
        )
        .first()
    )

    if existing_match:
        for field, value in match_data.model_dump().items():
            setattr(existing_match, field, value)
        db.commit()
        db.refresh(existing_match)
        return existing_match

    match = CandidateMatch(**match_data.model_dump())
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.get(
    "/job/{job_id}",
    response_model=list[CandidateMatchResponse],
)
def get_matches_for_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    return (
        db.query(CandidateMatch)
        .filter(CandidateMatch.job_id == job_id)
        .order_by(CandidateMatch.final_score.desc())
        .all()
    )


@router.get(
    "/{match_id}",
    response_model=CandidateMatchResponse,
)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
):
    match = db.query(CandidateMatch).filter(CandidateMatch.id == match_id).first()
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match result not found.",
        )
    return match


@router.delete(
    "/{match_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_match(
    match_id: int,
    db: Session = Depends(get_db),
):
    match = db.query(CandidateMatch).filter(CandidateMatch.id == match_id).first()
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match result not found.",
        )

    db.delete(match)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
