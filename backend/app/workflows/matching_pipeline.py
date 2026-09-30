import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.ai.embedding_client import embedding_client
from app.ai.llm_client import llm_client
from app.models.candidate import Candidate
from app.models.chunk import DocumentChunk
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.match import CandidateMatch
from app.models.resume import Resume
from app.retrieval.chunking import SectionAwareChunker
from app.retrieval.hybrid_search import hybrid_retrieval_engine
from app.retrieval.reranker import evidence_reranker
from app.services.document_service import document_service
from app.services.explanation_service import explanation_service
from app.services.scoring_service import ScoringWeights, scoring_engine
from app.services.skill_gap_service import skill_gap_service
from app.services.storage import storage_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class MatchingPipeline:
    """
    End-to-end AI recruitment pipeline orchestrating:
    1. Document ingestion and section-aware chunking
    2. LLM structured extraction (Job requirements & Candidate profiles)
    3. 768-dimensional dense embedding generation and indexing
    4. Multi-query hybrid retrieval and precision reranking
    5. Deterministic scoring engine (40% skills, 25% exp, 20% proj, 10% edu, 5% add)
    6. Skill-gap detection with severity categorization
    7. Evidence-grounded explanation synthesis
    """

    @classmethod
    def process_and_index_job(cls, job_id: int, db: Session) -> Job:
        """
        Decomposes a job description into atomic requirements and vector chunks.
        """
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        # 1. AI decomposition of requirements
        extracted_data = llm_client.extract_job_data(job.description)

        # Update job fields if better info extracted
        if not job.title or job.title == "Untitled Job":
            job.title = extracted_data.title
        if not job.company_name and extracted_data.company_name:
            job.company_name = extracted_data.company_name

        # 2. Add or update atomic requirements in DB
        existing_req_names = {r.skill_name.lower() for r in job.requirements}
        for req in extracted_data.requirements:
            if req.skill_name.lower() not in existing_req_names:
                new_req = JobRequirement(
                    job_id=job.id,
                    skill_name=req.skill_name,
                    is_required=req.is_required,
                    importance=req.importance,
                )
                db.add(new_req)
                existing_req_names.add(req.skill_name.lower())

        # 3. Create section-aware chunks & 768-dim embeddings
        # Clear previous chunks for this job
        db.query(DocumentChunk).filter(
            DocumentChunk.job_id == job.id, DocumentChunk.document_type == "job_description"
        ).delete()

        chunks = SectionAwareChunker.chunk_job_description(extracted_data, job.description)
        for c in chunks:
            emb = embedding_client.embed_text(c.content)
            doc_chunk = DocumentChunk(
                document_type="job_description",
                document_id=job.id,
                job_id=job.id,
                section=c.section,
                page_number=c.page_number,
                content=c.content,
                content_hash=c.content_hash,
                embedding=emb,
            )
            db.add(doc_chunk)

        db.commit()
        db.refresh(job)
        return job

    @classmethod
    def process_and_index_resume(cls, resume_id: int, db: Session) -> Candidate:
        """
        Parses resume document, extracts structured profile, embeds section chunks,
        and links evidence to the Candidate record.
        """
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise ValueError(f"Resume {resume_id} not found.")

        candidate = db.query(Candidate).filter(Candidate.id == resume.candidate_id).first()
        if not candidate:
            raise ValueError(f"Candidate {resume.candidate_id} not found.")

        # Read file bytes
        file_bytes = None
        if resume.file_path:
            # Check local file
            p = Path(resume.file_path)
            if p.exists():
                file_bytes = p.read_bytes()
            else:
                # Check storage service
                try:
                    file_key = Path(resume.file_path).name
                    file_bytes = storage_service.download_file(
                        bucket=settings.storage_bucket_resumes,
                        file_path=file_key,
                    )
                except Exception as e:
                    logger.warning(f"Could not read from storage: {e}")

        pages_data = None
        # If we already have extracted_text stored
        if not file_bytes and resume.extracted_text:
            raw_text = resume.extracted_text
        elif file_bytes:
            raw_text, pages_data = document_service.extract_text(file_bytes, resume.filename)
            resume.extracted_text = raw_text
        else:
            raw_text = f"Resume for {candidate.name or 'Candidate'}\nSkills: {candidate.skills or ''}\nExperience: {candidate.experience or ''}"

        # 1. AI candidate profile extraction
        profile = llm_client.extract_candidate_profile(raw_text)

        # Update candidate attributes
        if profile.name and (not candidate.name or candidate.name == "Unnamed Candidate"):
            candidate.name = profile.name
        if profile.email and not candidate.email:
            candidate.email = profile.email
        if profile.phone and not candidate.phone:
            candidate.phone = profile.phone

        # Store skills as comma-separated
        if profile.skills:
            candidate.skills = ", ".join(profile.skills)

        # Store experience, projects, education, certifications
        exp_lines = []
        for e in profile.experience:
            techs = f" [Tech: {', '.join(e.skills_used)}]" if e.skills_used else ""
            bullets = " | ".join(e.highlights) if e.highlights else ""
            exp_lines.append(f"{e.role} at {e.company} ({e.duration or 'N/A'}){techs}: {bullets}")
        candidate.experience = "\n".join(exp_lines)

        proj_lines = [
            f"{p.name} ({', '.join(p.technologies)}): {p.description}" for p in profile.projects
        ]
        candidate.projects = "\n".join(proj_lines)

        edu_lines = [f"{ed.degree} - {ed.institution} ({ed.year or 'N/A'})" for ed in profile.education]
        candidate.education = "\n".join(edu_lines)

        if profile.certifications:
            candidate.certifications = ", ".join(profile.certifications)

        # 2. Section-aware chunking and vector indexing with accurate page citations
        db.query(DocumentChunk).filter(
            DocumentChunk.candidate_id == candidate.id, DocumentChunk.document_type == "resume"
        ).delete()

        chunks = SectionAwareChunker.chunk_candidate_profile(profile, raw_text, pages_data=pages_data)
        for c in chunks:
            emb = embedding_client.embed_text(c.content)
            doc_chunk = DocumentChunk(
                document_type="resume",
                document_id=resume.id,
                candidate_id=candidate.id,
                section=c.section,
                page_number=c.page_number,
                content=c.content,
                content_hash=c.content_hash,
                embedding=emb,
            )
            db.add(doc_chunk)

        resume.processing_status = "completed"
        db.commit()
        db.refresh(candidate)
        return candidate

    @classmethod
    def match_candidate_to_job(
        cls,
        job_id: int,
        candidate_id: int,
        db: Session,
        weights: Optional[ScoringWeights] = None,
    ) -> Dict[str, Any]:
        """
        Runs the full LangGraph matching pipeline between a candidate and a job:
        - Requirement decomposition & expansion
        - Hybrid retrieval & cross-encoder precision reranking
        - Calibrated deterministic scoring (with confidence & coverage)
        - Skill-gap analysis via SkillGraph
        - Grounded explanation synthesis
        - Persistence in CandidateMatch table
        """
        from app.workflows.matching_graph import matching_graph
        return matching_graph.run(job_id=job_id, candidate_id=candidate_id, db=db, weights=weights)

    @classmethod
    def rank_candidates_for_job(cls, job_id: int, db: Session) -> List[Dict[str, Any]]:
        """
        Evaluates and ranks all candidates for a job, generating a deterministic leaderboard.
        """
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        candidates = db.query(Candidate).all()
        if not candidates:
            return []

        # Pre-cache requirement expansions once for this job
        for req in job.requirements:
            llm_client.expand_query(req.skill_name)

        ranked_results = []
        for candidate in candidates:
            try:
                res = cls.match_candidate_to_job(job_id=job.id, candidate_id=candidate.id, db=db)
                ranked_results.append(res)
            except Exception as e:
                logger.error(f"Error matching candidate {candidate.id} to job {job.id}: {e}")

        # Sort by final score descending
        ranked_results.sort(key=lambda x: x["final_score"], reverse=True)

        for rank_idx, item in enumerate(ranked_results):
            item["rank"] = rank_idx + 1

        return ranked_results


matching_pipeline = MatchingPipeline()
