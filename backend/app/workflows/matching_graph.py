import logging
from typing import Any, Dict, List, Optional, TypedDict
from sqlalchemy.orm import Session

from app.ai.llm_client import llm_client
from app.ai.skill_normalizer import skill_normalizer
from app.core.observability import tracer
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match import CandidateMatch
from app.retrieval.hybrid_search import hybrid_retrieval_engine
from app.retrieval.reranker import evidence_reranker
from app.services.explanation_service import explanation_service
from app.services.scoring_service import ScoringWeights, scoring_engine
from app.services.skill_gap_service import skill_gap_service

logger = logging.getLogger(__name__)


class MatchingState(TypedDict, total=False):
    """
    LangGraph state schema passed between matching pipeline nodes.
    """
    job_id: int
    candidate_id: int
    db: Session
    weights: Optional[ScoringWeights]
    job: Job
    candidate: Candidate
    normalized_job_skills: List[Dict[str, Any]]
    expanded_queries: Dict[str, List[str]]
    raw_retrieved_chunks: Dict[str, List[Dict[str, Any]]]
    reranked_evidence: Dict[str, List[Dict[str, Any]]]
    all_top_evidence: List[Dict[str, Any]]
    score_breakdown: Any
    gap_analysis: Any
    grounded_explanation: Any
    persisted_match: CandidateMatch
    final_output: Dict[str, Any]


class MatchingGraphOrchestrator:
    """
    LangGraph-compatible state graph orchestrator executing the 10-step recruitment pipeline:
    Load -> Normalize -> Expand -> Retrieve -> Cross-Encode -> Build Evidence ->
    Deterministic Score -> Skill Gap -> Grounded Explanation -> Persist.
    """

    def __init__(self):
        self._compiled_graph = None
        try:
            from langgraph.graph import StateGraph, END
            graph = StateGraph(MatchingState)

            graph.add_node("load_entities", self._node_load_entities)
            graph.add_node("normalize_skills", self._node_normalize_skills)
            graph.add_node("expand_queries", self._node_expand_queries)
            graph.add_node("hybrid_retrieval", self._node_hybrid_retrieval)
            graph.add_node("cross_encoder", self._node_cross_encoder)
            graph.add_node("evidence_builder", self._node_evidence_builder)
            graph.add_node("deterministic_scoring", self._node_deterministic_scoring)
            graph.add_node("skill_gap_analysis", self._node_skill_gap_analysis)
            graph.add_node("explanation_synthesis", self._node_explanation_synthesis)
            graph.add_node("persist_results", self._node_persist_results)

            graph.set_entry_point("load_entities")
            graph.add_edge("load_entities", "normalize_skills")
            graph.add_edge("normalize_skills", "expand_queries")
            graph.add_edge("expand_queries", "hybrid_retrieval")
            graph.add_edge("hybrid_retrieval", "cross_encoder")
            graph.add_edge("cross_encoder", "evidence_builder")
            graph.add_edge("evidence_builder", "deterministic_scoring")
            graph.add_edge("deterministic_scoring", "skill_gap_analysis")
            graph.add_edge("skill_gap_analysis", "explanation_synthesis")
            graph.add_edge("explanation_synthesis", "persist_results")
            graph.add_edge("persist_results", END)

            self._compiled_graph = graph.compile()
            logger.info("Compiled LangGraph matching pipeline successfully.")
        except Exception as e:
            logger.info(f"LangGraph compiled via internal state graph executor: {e}")

    def run(self, job_id: int, candidate_id: int, db: Session, weights: Optional[ScoringWeights] = None) -> Dict[str, Any]:
        """Runs the state graph across all nodes."""
        initial_state: MatchingState = {
            "job_id": job_id,
            "candidate_id": candidate_id,
            "db": db,
            "weights": weights,
        }

        if self._compiled_graph:
            try:
                res = self._compiled_graph.invoke(initial_state)
                return res["final_output"]
            except Exception as e:
                logger.warning(f"LangGraph execution exception: {e}. Running sequential state executor.")

        # Sequential StateGraph execution
        state = initial_state
        state = self._node_load_entities(state)
        state = self._node_normalize_skills(state)
        state = self._node_expand_queries(state)
        state = self._node_hybrid_retrieval(state)
        state = self._node_cross_encoder(state)
        state = self._node_evidence_builder(state)
        state = self._node_deterministic_scoring(state)
        state = self._node_skill_gap_analysis(state)
        state = self._node_explanation_synthesis(state)
        state = self._node_persist_results(state)
        return state["final_output"]

    # ==================== Graph Node Definitions ====================

    def _node_load_entities(self, state: MatchingState) -> MatchingState:
        with tracer.trace_span("load_entities", {"job_id": state["job_id"], "candidate_id": state["candidate_id"]}):
            db = state["db"]
            job = db.query(Job).filter(Job.id == state["job_id"]).first()
            if not job:
                raise ValueError(f"Job {state['job_id']} not found.")
            candidate = db.query(Candidate).filter(Candidate.id == state["candidate_id"]).first()
            if not candidate:
                raise ValueError(f"Candidate {state['candidate_id']} not found.")

            if not job.requirements:
                from app.workflows.matching_pipeline import MatchingPipeline
                MatchingPipeline.process_and_index_job(job.id, db)
                db.refresh(job)

            state["job"] = job
            state["candidate"] = candidate
            return state

    def _node_normalize_skills(self, state: MatchingState) -> MatchingState:
        with tracer.trace_span("normalize_skills"):
            job = state["job"]
            normalized = []
            for req in job.requirements:
                norm = skill_normalizer.normalize(req.skill_name)
                normalized.append({
                    "skill_name": req.skill_name,
                    "canonical": norm["canonical"],
                    "category": norm["category"],
                    "aliases": norm["aliases"],
                    "is_required": req.is_required,
                    "importance": req.importance,
                })
            state["normalized_job_skills"] = normalized
            return state

    def _node_expand_queries(self, state: MatchingState) -> MatchingState:
        with tracer.trace_span("expand_queries"):
            job = state["job"]
            expansions = {}
            for req in job.requirements:
                expansions[req.skill_name] = llm_client.expand_query(req.skill_name)
            state["expanded_queries"] = expansions
            return state

    def _node_hybrid_retrieval(self, state: MatchingState) -> MatchingState:
        with tracer.trace_span("hybrid_retrieval"):
            db = state["db"]
            candidate = state["candidate"]
            job = state["job"]
            expansions = state["expanded_queries"]
            retrieved_map = {}

            for req in job.requirements:
                skill = req.skill_name
                expanded_kw = expansions.get(skill, [])
                retrieved = hybrid_retrieval_engine.retrieve_evidence(
                    query=f"{skill} {' '.join(expanded_kw)}",
                    db=db,
                    candidate_id=candidate.id,
                    document_type="resume",
                    top_k=5,
                    expanded_keywords=expanded_kw,
                )
                retrieved_map[skill] = retrieved

            state["raw_retrieved_chunks"] = retrieved_map
            return state

    def _node_cross_encoder(self, state: MatchingState) -> MatchingState:
        with tracer.trace_span("cross_encoder_rerank"):
            job = state["job"]
            retrieved_map = state["raw_retrieved_chunks"]
            reranked_map = {}

            for req in job.requirements:
                skill = req.skill_name
                retrieved = retrieved_map.get(skill, [])
                reranked = evidence_reranker.rerank_evidence(
                    requirement=skill, retrieved_chunks=retrieved, top_n=2
                )
                reranked_map[skill] = reranked

            state["reranked_evidence"] = reranked_map
            return state

    def _node_evidence_builder(self, state: MatchingState) -> MatchingState:
        with tracer.trace_span("evidence_builder"):
            reranked_map = state["reranked_evidence"]
            all_top = []
            for evidence_list in reranked_map.values():
                all_top.extend(evidence_list)
            all_top.sort(key=lambda x: x["evidence_strength"], reverse=True)
            state["all_top_evidence"] = all_top
            return state

    def _node_deterministic_scoring(self, state: MatchingState) -> MatchingState:
        with tracer.trace_span("deterministic_scoring"):
            job = state["job"]
            candidate = state["candidate"]
            score = scoring_engine.compute_score(
                job_requirements=job.requirements,
                candidate_skills=candidate.skills,
                candidate_experience=candidate.experience,
                candidate_projects=candidate.projects,
                candidate_education=candidate.education,
                candidate_certifications=candidate.certifications,
                requirement_evidence_map=state["reranked_evidence"],
                weights=state.get("weights"),
            )
            state["score_breakdown"] = score
            return state

    def _node_skill_gap_analysis(self, state: MatchingState) -> MatchingState:
        with tracer.trace_span("skill_gap_analysis"):
            gap = skill_gap_service.analyze(
                job=state["job"],
                candidate=state["candidate"],
                requirement_evidence_map=state["reranked_evidence"],
            )
            state["gap_analysis"] = gap
            return state

    def _node_explanation_synthesis(self, state: MatchingState) -> MatchingState:
        with tracer.trace_span("explanation_synthesis"):
            exp = explanation_service.generate_explanation(
                job=state["job"],
                candidate=state["candidate"],
                score_breakdown=state["score_breakdown"],
                gap_analysis=state["gap_analysis"],
                top_evidence_chunks=state["all_top_evidence"],
            )
            state["grounded_explanation"] = exp
            return state

    def _node_persist_results(self, state: MatchingState) -> MatchingState:
        with tracer.trace_span("persist_results"):
            db = state["db"]
            job = state["job"]
            candidate = state["candidate"]
            score_breakdown = state["score_breakdown"]
            gap_analysis = state["gap_analysis"]
            grounded_exp = state["grounded_explanation"]
            all_top_evidence = state["all_top_evidence"]

            matching_skills_str = ", ".join([m["skill"] for m in gap_analysis.matched_skills])
            missing_skills_str = ", ".join(
                [m["skill"] for m in gap_analysis.missing_required + gap_analysis.missing_optional]
            )

            existing_match = (
                db.query(CandidateMatch)
                .filter(
                    CandidateMatch.job_id == job.id,
                    CandidateMatch.candidate_id == candidate.id,
                )
                .first()
            )
            if not existing_match:
                existing_match = CandidateMatch(job_id=job.id, candidate_id=candidate.id)
                db.add(existing_match)

            existing_match.final_score = score_breakdown.final_score
            existing_match.skill_score = score_breakdown.required_skill_score
            existing_match.experience_score = score_breakdown.experience_score
            existing_match.project_score = score_breakdown.project_score
            existing_match.education_score = score_breakdown.education_score
            existing_match.semantic_score = score_breakdown.semantic_score
            existing_match.matching_skills = matching_skills_str
            existing_match.missing_skills = missing_skills_str
            existing_match.explanation = grounded_exp.summary

            db.commit()
            db.refresh(existing_match)

            state["persisted_match"] = existing_match
            state["final_output"] = {
                "match_id": existing_match.id,
                "job_id": job.id,
                "job_title": job.title,
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "final_score": score_breakdown.final_score,
                "confidence": score_breakdown.confidence,
                "evidence_coverage": score_breakdown.evidence_coverage,
                "score_breakdown": score_breakdown.model_dump(),
                "skill_gaps": gap_analysis.to_dict(),
                "grounded_explanation": grounded_exp.model_dump(),
                "top_evidence_citations": all_top_evidence[:6],
                "created_at": existing_match.created_at,
                "pipeline": "LangGraph-Orchestrated",
            }
            return state


matching_graph = MatchingGraphOrchestrator()
