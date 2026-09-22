from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models import Candidate
from app.schemas import (
    CandidateCreate,
    CandidateDetailResponse,
    CandidateResponse,
    CandidateUpdate,
)

router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"],
)


@router.post(
    "/",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_candidate(
    candidate_data: CandidateCreate,
    db: Session = Depends(get_db),
):
    candidate = Candidate(
        name=candidate_data.name,
        email=candidate_data.email,
        phone=candidate_data.phone,
        education=candidate_data.education,
        experience=candidate_data.experience,
        skills=candidate_data.skills,
        projects=candidate_data.projects,
        certifications=candidate_data.certifications,
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return candidate


@router.get(
    "/",
    response_model=list[CandidateResponse],
)
def get_candidates(
    search: str | None = Query(default=None, description="Search name, email, or skills"),
    db: Session = Depends(get_db),
):
    query = db.query(Candidate)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Candidate.name.ilike(search_filter))
            | (Candidate.email.ilike(search_filter))
            | (Candidate.skills.ilike(search_filter))
        )
    return query.order_by(Candidate.created_at.desc()).all()


@router.get(
    "/{candidate_id}",
    response_model=CandidateDetailResponse,
)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
):
    candidate = (
        db.query(Candidate)
        .options(joinedload(Candidate.resumes))
        .filter(Candidate.id == candidate_id)
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    return candidate


@router.put(
    "/{candidate_id}",
    response_model=CandidateResponse,
)
def update_candidate(
    candidate_id: int,
    candidate_data: CandidateUpdate,
    db: Session = Depends(get_db),
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    update_data = candidate_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(candidate, field, value)

    db.commit()
    db.refresh(candidate)
    return candidate


@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    db.delete(candidate)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)