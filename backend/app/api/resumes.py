from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import Candidate, Resume
from app.schemas import ResumeResponse
from app.services.storage import storage_service

router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"],
)

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post(
    "/",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    candidate_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id)
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported file format. "
                "Only PDF and DOCX files are allowed."
            ),
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    unique_filename = f"{uuid4().hex}{extension}"
    content_type = ALLOWED_EXTENSIONS.get(extension, "application/octet-stream")

    stored_path = storage_service.upload_file(
        bucket=settings.storage_bucket_resumes,
        destination_path=unique_filename,
        file_bytes=contents,
        content_type=content_type,
    )

    resume = Resume(
        candidate_id=candidate_id,
        filename=filename,
        file_path=stored_path,
        file_type=extension.replace(".", ""),
        processing_status="pending",
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
)
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )
    return resume


@router.get(
    "/{resume_id}/signed-url",
)
def get_resume_signed_url(
    resume_id: int,
    expires_in: int = Query(default=3600, ge=60, le=86400, description="Signed URL expiry in seconds"),
    db: Session = Depends(get_db),
):
    """
    Generates a secure, time-limited signed URL for authorized download/preview
    of a candidate's resume from private Supabase Storage.
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    if not resume.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file stored for this resume.",
        )

    # Extract object key if stored as full path or filename
    file_key = Path(resume.file_path).name

    signed_url = storage_service.get_signed_url(
        bucket=settings.storage_bucket_resumes,
        file_path=file_key,
        expires_in=expires_in,
    )

    return {
        "resume_id": resume.id,
        "filename": resume.filename,
        "signed_url": signed_url,
        "expires_in_seconds": expires_in,
    }


@router.get(
    "/candidate/{candidate_id}",
    response_model=list[ResumeResponse],
)
def get_resumes_by_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    return (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate_id)
        .order_by(Resume.created_at.desc())
        .all()
    )


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    if resume.file_path:
        file_key = Path(resume.file_path).name
        storage_service.delete_file(
            bucket=settings.storage_bucket_resumes,
            file_path=file_key,
        )

    db.delete(resume)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)