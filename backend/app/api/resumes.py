from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Candidate, Resume
from app.schemas import ResumeResponse

router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"],
)

UPLOAD_DIR = Path("data/resumes")
UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
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
    file_path = UPLOAD_DIR / unique_filename
    file_path.write_bytes(contents)

    resume = Resume(
        candidate_id=candidate_id,
        filename=filename,
        file_path=str(file_path),
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
        local_path = Path(resume.file_path)
        if local_path.exists():
            try:
                local_path.unlink()
            except OSError:
                pass

    db.delete(resume)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)