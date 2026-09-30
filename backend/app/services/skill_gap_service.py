import re
from typing import Any, Dict, List, Optional
from app.ai.skill_normalizer import skill_normalizer
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.job_requirement import JobRequirement


class SkillGapAnalysisResult:
    def __init__(
        self,
        matched_skills: List[Dict[str, Any]],
        missing_required: List[Dict[str, Any]],
        missing_optional: List[Dict[str, Any]],
        weak_skills: List[Dict[str, Any]],
        coverage_percentage: float,
    ):
        self.matched_skills = matched_skills
        self.missing_required = missing_required
        self.missing_optional = missing_optional
        self.weak_skills = weak_skills
        self.coverage_percentage = coverage_percentage

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched_skills": self.matched_skills,
            "missing_required": self.missing_required,
            "missing_optional": self.missing_optional,
            "weak_skills": self.weak_skills,
            "coverage_percentage": self.coverage_percentage,
        }


class SkillGapService:
    """
    Skill-Gap Analysis Engine powered by the Skill Graph.
    Identifies missing mandatory competencies, unsupported resume claims (weak skills),
    and categorized upskilling recommendations.
    """

    @classmethod
    def analyze(
        cls,
        job: Job,
        candidate: Candidate,
        requirement_evidence_map: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> SkillGapAnalysisResult:
        req_map = requirement_evidence_map or {}

        # Candidate skills
        candidate_skills_raw = candidate.skills or ""
        candidate_skills_list = [
            s.strip() for s in re.split(r"[,|\n/]+", candidate_skills_raw) if s.strip()
        ]

        exp_text = (candidate.experience or "").lower()
        proj_text = (candidate.projects or "").lower()
        combined_body = f"{exp_text} {proj_text}"

        matched_skills: List[Dict[str, Any]] = []
        missing_required: List[Dict[str, Any]] = []
        missing_optional: List[Dict[str, Any]] = []
        weak_skills: List[Dict[str, Any]] = []

        total_required_count = 0
        matched_required_count = 0

        for req in job.requirements:
            skill_name = req.skill_name
            is_req = req.is_required
            importance = req.importance or "medium"
            norm_skill = skill_normalizer.normalize(skill_name)
            canonical = norm_skill["canonical"]
            category = norm_skill["category"]

            if is_req:
                total_required_count += 1

            evidence_list = req_map.get(skill_name, [])
            best_evidence = evidence_list[0] if evidence_list else None
            evidence_strength = best_evidence.get("evidence_strength", 0.0) if best_evidence else 0.0

            # Check if skill matches any candidate listed skill via SkillGraph
            skill_declared = any(
                skill_normalizer.match_skills(skill_name, c_skill)
                for c_skill in candidate_skills_list
            )

            # Check if mentioned in experience / project text
            aliases = [a.lower() for a in norm_skill.get("aliases", [])]
            terms_to_search = [skill_name.lower(), canonical.lower()] + aliases
            practical_mention = any(term in combined_body for term in terms_to_search)

            is_strong_vector_match = evidence_strength >= 0.40

            if is_strong_vector_match or practical_mention:
                match_entry = {
                    "skill": skill_name,
                    "canonical": canonical,
                    "category": category,
                    "is_required": is_req,
                    "importance": importance,
                    "evidence_strength": round(evidence_strength, 2),
                    "section": best_evidence.get("section", "experience") if best_evidence else "text",
                    "citation": best_evidence.get("citation_quote", "Verified in profile") if best_evidence else "Practical experience found",
                }
                matched_skills.append(match_entry)
                if is_req:
                    matched_required_count += 1

            elif skill_declared and not practical_mention and evidence_strength < 0.40:
                # Declared but unverified (weak skill)
                weak_skills.append(
                    {
                        "skill": skill_name,
                        "canonical": canonical,
                        "category": category,
                        "is_required": is_req,
                        "importance": importance,
                        "reason": f"Listed in skills section but lacking demonstrable project or work experience",
                        "severity": "medium" if is_req else "low",
                    }
                )

            else:
                # Missing completely
                missing_entry = {
                    "skill": skill_name,
                    "canonical": canonical,
                    "category": category,
                    "is_required": is_req,
                    "importance": importance,
                    "severity": "critical" if (is_req and importance == "high") else ("high" if is_req else "low"),
                    "reason": f"Required competency not demonstrated in candidate profile or experience history",
                    "recommendation": f"Acquire experience or certification in {canonical}",
                    "related_skills": norm_skill.get("related", [])[:3],
                }
                if is_req:
                    missing_required.append(missing_entry)
                else:
                    missing_optional.append(missing_entry)

        coverage = (
            round((matched_required_count / total_required_count) * 100.0, 1)
            if total_required_count > 0
            else 100.0
        )

        return SkillGapAnalysisResult(
            matched_skills=matched_skills,
            missing_required=missing_required,
            missing_optional=missing_optional,
            weak_skills=weak_skills,
            coverage_percentage=coverage,
        )


skill_gap_service = SkillGapService()
