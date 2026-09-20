from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    candidates_router,
    jobs_router,
    resumes_router,
)

from app.core.init_db import init_database


app = FastAPI(
    title="AI Recruitment & Candidate Matching Platform",
    description=(
        "AI-powered recruitment platform for job description analysis, "
        "resume processing, semantic candidate matching, scoring and ranking."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(resumes_router)


@app.on_event("startup")
def startup_event():
    init_database()


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