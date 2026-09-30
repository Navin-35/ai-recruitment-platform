import json
from typing import Any, Dict, List
from app.ai.llm_client import llm_client
from app.ai.structured_outputs import GroundedExplanation
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.scoring_service import ScoreBreakdown
from app.services.skill_gap_service import SkillGapAnalysisResult


class ExplanationService:
    """
    Grounded Explanation Engine: generates transparent, evidence-backed
    explanations for recruiter decision-making, strictly citing candidate evidence chunks.
    """

    @classmethod
    def generate_explanation(
        cls,
        job: Job,
        candidate: Candidate,
        score_breakdown: ScoreBreakdown,
        gap_analysis: SkillGapAnalysisResult,
        top_evidence_chunks: List[Dict[str, Any]],
    ) -> GroundedExplanation:
        """
        Synthesizes candidate evidence into an explainability report.
        """
        # Format requirements summary
        req_lines = [
            f"- {r.skill_name} ({'Required' if r.is_required else 'Preferred'}, Importance: {r.importance})"
            for r in job.requirements
        ]
        requirements_summary = "\n".join(req_lines) if req_lines else "General requirements"

        # Format evidence chunks
        evidence_text_list = []
        for i, item in enumerate(top_evidence_chunks[:8]):
            chunk_id = item.get("chunk_id", i + 1)
            sec = item.get("section", "general")
            strength = item.get("evidence_strength", 0.0)
            quote = item.get("citation_quote") or item.get("content", "")[:200]
            evidence_text_list.append(
                f"[Chunk #{chunk_id} | Section: {sec} | Strength: {strength}]: \"{quote}\""
            )
        evidence_chunks_text = "\n".join(evidence_text_list) if evidence_text_list else "No direct chunks"

        # Format skill gaps
        gap_lines = []
        for g in gap_analysis.missing_required:
            r = g.get("reason") or g.get("recommendation") or "Mandatory requirement not demonstrated"
            gap_lines.append(f"- [HIGH SEVERITY - MANDATORY MISSING]: {g.get('skill', 'Unknown')} - {r}")
        for w in gap_analysis.weak_skills:
            r = w.get("reason") or "Skill declared without practical evidence"
            gap_lines.append(f"- [MEDIUM SEVERITY - WEAK EVIDENCE]: {w.get('skill', 'Unknown')} - {r}")
        for o in gap_analysis.missing_optional:
            r = o.get("reason") or o.get("recommendation") or "Optional skill not found"
            gap_lines.append(f"- [LOW SEVERITY - OPTIONAL]: {o.get('skill', 'Unknown')} - {r}")
        skill_gaps_text = "\n".join(gap_lines) if gap_lines else "None identified"

        return llm_client.generate_grounded_explanation(
            job_title=job.title,
            job_description=job.description,
            requirements_summary=requirements_summary,
            candidate_name=candidate.name or "Candidate",
            candidate_skills=candidate.skills or "N/A",
            experience_summary=candidate.experience or "N/A",
            evidence_chunks_text=evidence_chunks_text,
            skill_gaps_text=skill_gaps_text,
            final_score=score_breakdown.final_score,
            skill_score=score_breakdown.required_skill_score,
            experience_score=score_breakdown.experience_score,
            project_score=score_breakdown.project_score,
            education_score=score_breakdown.education_score,
        )


explanation_service = ExplanationService()
