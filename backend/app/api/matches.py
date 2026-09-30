from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Candidate, CandidateMatch, Job
from app.schemas import CandidateMatchCreate, CandidateMatchResponse

router = APIRouter(
    prefix="/matches",
    tags=["Matches"],
)


@router.post(
    "/",
    response_model=CandidateMatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_candidate_match(
    match_data: CandidateMatchCreate,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == match_data.job_id).first()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    candidate = db.query(Candidate).filter(Candidate.id == match_data.candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    # If match already exists for this job and candidate, update it; otherwise create new
    existing_match = (
        db.query(CandidateMatch)
        .filter(
            CandidateMatch.job_id == match_data.job_id,
            CandidateMatch.candidate_id == match_data.candidate_id,
        )
        .first()
    )

    if existing_match:
        for field, value in match_data.model_dump().items():
            setattr(existing_match, field, value)
        db.commit()
        db.refresh(existing_match)
        return existing_match

    match = CandidateMatch(**match_data.model_dump())
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.get(
    "/job/{job_id}",
    response_model=list[CandidateMatchResponse],
)
def get_matches_for_job(
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
        db.query(CandidateMatch)
        .filter(CandidateMatch.job_id == job_id)
        .order_by(CandidateMatch.final_score.desc())
        .all()
    )


@router.get(
    "/{match_id}",
    response_model=CandidateMatchResponse,
)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
):
    match = db.query(CandidateMatch).filter(CandidateMatch.id == match_id).first()
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match result not found.",
        )
    return match


@router.delete(
    "/{match_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_match(
    match_id: int,
    db: Session = Depends(get_db),
):
    match = db.query(CandidateMatch).filter(CandidateMatch.id == match_id).first()
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match result not found.",
        )

    db.delete(match)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/job/{job_id}/candidate/{candidate_id}",
    status_code=status.HTTP_200_OK,
)
def match_single_candidate(
    job_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
):
    """
    Executes full AI matching pipeline:
    - Hybrid retrieval (semantic + lexical + RRF)
    - Precision reranking of evidence
    - Deterministic scoring engine (40% skills, 25% exp, 20% proj, 10% edu, 5% add)
    - Skill-gap analysis
    - Grounded explanation generation citing evidence chunks
    """
    from app.workflows.matching_pipeline import matching_pipeline

    try:
        result = matching_pipeline.match_candidate_to_job(
            job_id=job_id,
            candidate_id=candidate_id,
            db=db,
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching pipeline failed: {str(e)}",
        )


@router.post(
    "/job/{job_id}/run-all",
    status_code=status.HTTP_200_OK,
)
def match_and_rank_all_candidates(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Runs the matching pipeline for all candidates against a job,
    generates grounded scores, and creates a ranked leaderboard.
    """
    from app.workflows.matching_pipeline import matching_pipeline

    try:
        ranked_results = matching_pipeline.rank_candidates_for_job(job_id=job_id, db=db)
        return {
            "job_id": job_id,
            "total_candidates_evaluated": len(ranked_results),
            "leaderboard": ranked_results,
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ranking pipeline failed: {str(e)}",
        )


@router.get(
    "/job/{job_id}/ranking",
    status_code=status.HTTP_200_OK,
)
def get_job_ranking(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieves the current ranked candidate leaderboard for a job,
    sorted by final_score descending, with category score breakdowns.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    matches = (
        db.query(CandidateMatch)
        .filter(CandidateMatch.job_id == job_id)
        .order_by(CandidateMatch.final_score.desc())
        .all()
    )

    leaderboard = []
    for rank, m in enumerate(matches, start=1):
        candidate = db.query(Candidate).filter(Candidate.id == m.candidate_id).first()
        leaderboard.append(
            {
                "rank": rank,
                "match_id": m.id,
                "candidate_id": m.candidate_id,
                "candidate_name": candidate.name if candidate else "Unknown",
                "candidate_email": candidate.email if candidate else None,
                "final_score": m.final_score,
                "score_breakdown": {
                    "skills": m.skill_score,
                    "experience": m.experience_score,
                    "projects": m.project_score,
                    "education": m.education_score,
                    "semantic": m.semantic_score,
                },
                "matching_skills": m.matching_skills,
                "missing_skills": m.missing_skills,
                "explanation_summary": m.explanation,
                "evaluated_at": m.created_at,
            }
        )

    return {
        "job_id": job.id,
        "job_title": job.title,
        "candidate_count": len(leaderboard),
        "leaderboard": leaderboard,
    }


@router.get(
    "/job/{job_id}/candidate/{candidate_id}/report",
    status_code=status.HTTP_200_OK,
)
def get_candidate_match_report(
    job_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns full explainability and skill-gap report for a specific candidate and job.
    """
    from app.workflows.matching_pipeline import matching_pipeline

    try:
        report = matching_pipeline.match_candidate_to_job(
            job_id=job_id,
            candidate_id=candidate_id,
            db=db,
        )
        return report
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )

