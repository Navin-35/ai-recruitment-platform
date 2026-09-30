import numpy as np
from app.ai.embedding_client import embedding_client
from app.ai.structured_outputs import (
    ExtractedCandidateProfile,
    ExtractedExperience,
    ExtractedJobData,
    ExtractedProject,
    ExtractedRequirement,
)
from app.models.candidate import Candidate
from app.models.chunk import DocumentChunk
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.retrieval.chunking import SectionAwareChunker
from app.retrieval.hybrid_search import cosine_similarity, hybrid_retrieval_engine
from app.retrieval.reranker import evidence_reranker
from app.services.scoring_service import ScoringWeights, scoring_engine
from app.services.skill_gap_service import skill_gap_service
from app.workflows.matching_pipeline import matching_pipeline


def test_embedding_client():
    text = "FastAPI backend microservices and PostgreSQL"
    vec = embedding_client.embed_text(text)
    assert len(vec) == 768
    norm = np.linalg.norm(vec)
    assert 0.99 <= norm <= 1.01  # Normalized unit vector


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    assert cosine_similarity(v1, v2) == 1.0
    assert cosine_similarity(v1, v3) == 0.0


def test_section_aware_chunking():
    job_data = ExtractedJobData(
        title="Backend Engineer",
        company_name="TechCorp",
        summary="Leading backend development.",
        requirements=[
            ExtractedRequirement(
                skill_name="Python",
                is_required=True,
                importance="high",
                category="language",
            ),
            ExtractedRequirement(
                skill_name="Docker",
                is_required=False,
                importance="medium",
                category="tool",
            ),
        ],
    )
    chunks = SectionAwareChunker.chunk_job_description(job_data, "raw text")
    assert len(chunks) >= 3
    sections = [c.section for c in chunks]
    assert "summary" in sections
    assert "requirements" in sections


def test_deterministic_scoring_formula():
    reqs = [
        JobRequirement(id=1, job_id=1, skill_name="Python", is_required=True, importance="high"),
        JobRequirement(id=2, job_id=1, skill_name="PostgreSQL", is_required=True, importance="high"),
        JobRequirement(id=3, job_id=1, skill_name="Docker", is_required=False, importance="low"),
    ]

    mock_evidence = {
        "Python": [
            {
                "chunk_id": 1,
                "section": "experience",
                "evidence_strength": 0.95,
                "semantic_score": 0.9,
            }
        ],
        "PostgreSQL": [
            {
                "chunk_id": 2,
                "section": "experience",
                "evidence_strength": 0.85,
                "semantic_score": 0.85,
            }
        ],
        "Docker": [
            {
                "chunk_id": 3,
                "section": "projects",
                "evidence_strength": 0.70,
                "semantic_score": 0.75,
            }
        ],
    }

    score = scoring_engine.compute_score(
        job_requirements=reqs,
        candidate_skills="Python, PostgreSQL, Docker",
        candidate_experience="3 years backend engineering at TechCorp",
        candidate_projects="Built scalable APIs",
        candidate_education="B.S. Computer Science",
        candidate_certifications="AWS Certified",
        requirement_evidence_map=mock_evidence,
    )

    assert 0.0 <= score.final_score <= 100.0
    assert score.required_skill_score >= 80.0
    assert score.weights_used["required_skills"] == 0.40
    assert score.weights_used["experience"] == 0.25
    assert score.weights_used["projects"] == 0.20
    assert score.weights_used["education"] == 0.10
    assert score.weights_used["additional_skills"] == 0.05


def test_skill_gap_analysis():
    job = Job(
        id=1,
        title="Senior Python Lead",
        description="Looking for senior Python and Kubernetes engineer.",
    )
    job.requirements = [
        JobRequirement(id=1, job_id=1, skill_name="Python", is_required=True, importance="high"),
        JobRequirement(id=2, job_id=1, skill_name="Kubernetes", is_required=True, importance="high"),
        JobRequirement(id=3, job_id=1, skill_name="Terraform", is_required=False, importance="low"),
        JobRequirement(id=4, job_id=1, skill_name="React", is_required=False, importance="low"),
    ]

    # Candidate has Python in experience, React in skills list only (weak skill), but lacks Kubernetes
    candidate = Candidate(
        id=1,
        name="Alice Candidate",
        skills="Python, React",
        experience="Built backend services with Python for 4 years.",
        projects="Python microservices",
    )

    mock_ev = {
        "Python": [{"evidence_strength": 0.9, "citation_quote": "Built backend services with Python"}],
        "React": [{"evidence_strength": 0.2, "citation_quote": "React"}],
    }

    result = skill_gap_service.analyze(job=job, candidate=candidate, requirement_evidence_map=mock_ev)

    matched = [m["skill"] for m in result.matched_skills]
    missing_req = [m["skill"] for m in result.missing_required]
    weak = [w["skill"] for w in result.weak_skills]

    assert "Python" in matched
    assert "Kubernetes" in missing_req
    assert "React" in weak  # Listed in skills but 0 experience
    assert result.coverage_percentage == 50.0  # 1 of 2 required matched


def test_evidence_reranker():
    chunks = [
        {
            "chunk_id": 1,
            "section": "summary",
            "semantic_score": 0.8,
            "lexical_score": 0.5,
            "chunk": type("C", (), {"content": "FastAPI is my favorite framework for APIs."})(),
        },
        {
            "chunk_id": 2,
            "section": "experience",
            "semantic_score": 0.85,
            "lexical_score": 0.9,
            "chunk": type("C", (), {"content": "Architected FastAPI microservices handling 50k requests."})(),
        },
    ]

    reranked = evidence_reranker.rerank_evidence(requirement="FastAPI", retrieved_chunks=chunks)
    assert len(reranked) == 2
    # Experience chunk should rank higher than summary due to section weighting and keywords
    assert reranked[0]["chunk_id"] == 2
    assert "FastAPI" in reranked[0]["citation_quote"]


def test_end_to_end_matching_in_db(db_session):
    # 1. Create Job with requirements
    job = Job(
        title="AI Engineer",
        description="Seeking an AI Engineer with Python, PyTorch, and FastAPI experience.",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # Index job requirements
    matching_pipeline.process_and_index_job(job.id, db_session)
    assert len(job.requirements) >= 1

    # 2. Create Candidate with chunks
    candidate = Candidate(
        name="Jordan AI",
        email="jordan@example.com",
        skills="Python, PyTorch, FastAPI, Docker",
        experience="Built deep learning models in PyTorch and deployed FastAPI inference endpoints for 3 years.",
        projects="Computer vision defect detection using PyTorch",
        education="M.S. in Artificial Intelligence",
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    # Add candidate chunks
    emb = embedding_client.embed_text("PyTorch and FastAPI deep learning")
    chunk = DocumentChunk(
        document_type="resume",
        document_id=1,
        candidate_id=candidate.id,
        section="experience",
        content="Built deep learning models in PyTorch and deployed FastAPI inference endpoints for 3 years.",
        embedding=emb,
    )
    db_session.add(chunk)
    db_session.commit()

    # 3. Match Candidate to Job
    match_result = matching_pipeline.match_candidate_to_job(
        job_id=job.id, candidate_id=candidate.id, db=db_session
    )

    assert match_result["final_score"] > 50.0
    assert "score_breakdown" in match_result
    assert "grounded_explanation" in match_result
    assert match_result["grounded_explanation"]["summary"] is not None
    assert len(match_result["top_evidence_citations"]) >= 1

    # 4. Rank Candidates for Job
    ranked = matching_pipeline.rank_candidates_for_job(job_id=job.id, db=db_session)
    assert len(ranked) >= 1
    assert ranked[0]["rank"] == 1
    assert ranked[0]["candidate_id"] == candidate.id
