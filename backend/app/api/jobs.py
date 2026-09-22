from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models import Job
from app.schemas import JobCreate, JobDetailResponse, JobResponse, JobUpdate

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
):
    job = Job(
        title=job_data.title,
        company_name=job_data.company_name,
        description=job_data.description,
        location=job_data.location,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@router.get(
    "/",
    response_model=list[JobResponse],
)
def get_jobs(
    status: str | None = Query(default=None, description="Filter jobs by status"),
    search: str | None = Query(default=None, description="Search title or company"),
    db: Session = Depends(get_db),
):
    query = db.query(Job)
    if status:
        query = query.filter(Job.status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Job.title.ilike(search_filter)) | (Job.company_name.ilike(search_filter))
        )
    return query.order_by(Job.created_at.desc()).all()


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = (
        db.query(Job)
        .options(joinedload(Job.requirements))
        .filter(Job.id == job_id)
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    return job


@router.put(
    "/{job_id}",
    response_model=JobResponse,
)
def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    db.delete(job)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)