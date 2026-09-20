from app.api.candidates import router as candidates_router
from app.api.jobs import router as jobs_router
from app.api.resumes import router as resumes_router


__all__ = [
    "candidates_router",
    "jobs_router",
    "resumes_router",
]