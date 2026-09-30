from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
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


@router.post(
    "/upload",
    response_model=JobDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_job_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    company_name: Optional[str] = Form(default=None),
    location: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    """
    Uploads a Job Description as PDF, DOCX, or TXT, extracts full text,
    decomposes atomic requirements via Gemini, and vector indexes section chunks.
    """
    from app.services.document_service import document_service
    from app.workflows.matching_pipeline import matching_pipeline

    file_bytes = await file.read()
    raw_text, _ = document_service.extract_text(file_bytes, file.filename)
    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract readable text from uploaded file.",
        )

    job = Job(
        title=title or file.filename.rsplit(".", 1)[0].replace("_", " ").title(),
        company_name=company_name,
        location=location,
        description=raw_text,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Process and index requirements via LangGraph pipeline
    try:
        updated_job = matching_pipeline.process_and_index_job(job_id=job.id, db=db)
        return updated_job
    except Exception as e:
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


@router.post(
    "/{job_id}/extract-requirements",
    response_model=JobDetailResponse,
)
def extract_job_requirements(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Triggers AI extraction and decomposition of job requirements using LLM,
    creates atomic requirement records, and generates 768-dim embeddings for retrieval.
    """
    from app.workflows.matching_pipeline import matching_pipeline

    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    try:
        updated_job = matching_pipeline.process_and_index_job(job_id=job.id, db=db)
        return updated_job
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract requirements: {str(e)}",
        )