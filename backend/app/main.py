from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    candidates_router,
    job_requirements_router,
    jobs_router,
    matches_router,
    resumes_router,
    skills_router,
)
from app.core.init_db import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_database()
    yield


app = FastAPI(
    title="AI Recruitment & Candidate Matching Platform",
    description=(
        "AI-powered recruitment platform for job description analysis, "
        "resume processing, semantic candidate matching, scoring and ranking."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(job_requirements_router)
app.include_router(candidates_router)
app.include_router(resumes_router)
app.include_router(skills_router)
app.include_router(matches_router)


@app.get("/")
async def root():
    return {
        "message": "AI Recruitment Platform API is running",
        "version": "1.0.0",
        "status": "healthy",
    }


from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

class DirectMatchRequest(BaseModel):
    job_id: int
    candidate_id: int

@app.post("/match", tags=["Matches"])
def match_candidate_direct(req: DirectMatchRequest, db: Session = Depends(get_db)):
    """Direct alias for candidate matching matching assignment specification."""
    from app.workflows.matching_pipeline import matching_pipeline
    return matching_pipeline.match_candidate_to_job(job_id=req.job_id, candidate_id=req.candidate_id, db=db)

@app.get("/ranking", tags=["Matches"])
def get_ranking_direct(job_id: int, db: Session = Depends(get_db)):
    """Direct alias for candidate ranking leaderboard matching assignment specification."""
    from app.api.matches import get_job_ranking
    return get_job_ranking(job_id=job_id, db=db)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "backend",
    }


@app.get("/api/system/status")
async def system_status():
    from app.ai.embedding_client import embedding_client
    from app.core.config import settings
    from app.core.observability import tracer
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "embedding": embedding_client.get_status(),
        "observability": {
            "langfuse_enabled": tracer.is_enabled,
        },
        "background_queue": {
            "redis_enabled": settings.enable_redis_queue,
            "engine": "redis" if settings.enable_redis_queue else "in-memory-threadpool",
        },
        "auth_enforced": settings.enable_auth_enforcement,
    }


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    from fastapi import HTTPException
    from app.workflows.worker import async_worker
    task = async_worker.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task