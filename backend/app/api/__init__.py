from app.api.candidates import router as candidates_router
from app.api.job_requirements import router as job_requirements_router
from app.api.jobs import router as jobs_router
from app.api.matches import router as matches_router
from app.api.resumes import router as resumes_router
from app.api.skills import router as skills_router

__all__ = [
    "candidates_router",
    "jobs_router",
    "job_requirements_router",
    "matches_router",
    "resumes_router",
    "skills_router",
]