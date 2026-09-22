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
        "version": "0.1.0",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "backend",
    }