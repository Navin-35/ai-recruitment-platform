from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Job, JobRequirement
from app.schemas import (
    JobRequirementCreate,
    JobRequirementResponse,
    JobRequirementUpdate,
)

router = APIRouter(
    prefix="/jobs/{job_id}/requirements",
    tags=["Job Requirements"],
)


@router.post(
    "/",
    response_model=JobRequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_job_requirement(
    job_id: int,
    req_data: JobRequirementCreate,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    requirement = JobRequirement(
        job_id=job_id,
        skill_name=req_data.skill_name.strip(),
        is_required=req_data.is_required,
        importance=req_data.importance,
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


@router.get(
    "/",
    response_model=list[JobRequirementResponse],
)
def get_job_requirements(
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
        db.query(JobRequirement)
        .filter(JobRequirement.job_id == job_id)
        .all()
    )


@router.put(
    "/{requirement_id}",
    response_model=JobRequirementResponse,
)
def update_job_requirement(
    job_id: int,
    requirement_id: int,
    req_data: JobRequirementUpdate,
    db: Session = Depends(get_db),
):
    requirement = (
        db.query(JobRequirement)
        .filter(
            JobRequirement.id == requirement_id,
            JobRequirement.job_id == job_id,
        )
        .first()
    )
    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job requirement not found.",
        )

    update_data = req_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(requirement, field, value)

    db.commit()
    db.refresh(requirement)
    return requirement


@router.delete(
    "/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_job_requirement(
    job_id: int,
    requirement_id: int,
    db: Session = Depends(get_db),
):
    requirement = (
        db.query(JobRequirement)
        .filter(
            JobRequirement.id == requirement_id,
            JobRequirement.job_id == job_id,
        )
        .first()
    )
    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job requirement not found.",
        )

    db.delete(requirement)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
