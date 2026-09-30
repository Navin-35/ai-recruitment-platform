import math
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.ai.skill_normalizer import skill_normalizer


class ScoringWeights(BaseModel):
    required_skills: float = Field(default=0.40, ge=0.0, le=1.0)
    experience: float = Field(default=0.25, ge=0.0, le=1.0)
    projects: float = Field(default=0.20, ge=0.0, le=1.0)
    education: float = Field(default=0.10, ge=0.0, le=1.0)
    additional_skills: float = Field(default=0.05, ge=0.0, le=1.0)


class ScoreBreakdown(BaseModel):
    final_score: float
    required_skill_score: float
    experience_score: float
    project_score: float
    education_score: float
    additional_skill_score: float
    semantic_score: float
    confidence: float = 0.85
    evidence_coverage: float = 0.80
    weights_used: Dict[str, float]
    requirement_match_details: List[Dict[str, Any]] = []


class ScoringEngine:
    """
    Deterministic calibrated scoring engine implementing:
    FinalScore = (0.40 * RequiredSkillScore) +
                 (0.25 * ExperienceScore) +
                 (0.20 * ProjectScore) +
                 (0.10 * EducationScore) +
                 (0.05 * AdditionalSkillScore)
    Includes evidence coverage, confidence estimation, and seniority/duration calibration.
    """

    def __init__(self, default_weights: Optional[ScoringWeights] = None):
        self.default_weights = default_weights or ScoringWeights()

    @staticmethod
    def _extract_years_of_experience(text: str) -> float:
        """Extracts numerical years of experience mentioned in experience text."""
        if not text:
            return 0.0

        year_patterns = [
            r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience)?",
            r"(?:experience\s*:\s*)(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        ]
        years = []
        for p in year_patterns:
            matches = re.findall(p, text, re.IGNORECASE)
            for m in matches:
                try:
                    years.append(float(m))
                except ValueError:
                    continue

        if years:
            return max(years)

        # Estimate based on date ranges (e.g., 2020 - 2024 or 2019 - Present)
        ranges = re.findall(r"(20\d\d)\s*(?:-|–|to)\s*(20\d\d|present|current)", text, re.IGNORECASE)
        total_years = 0.0
        for start_str, end_str in ranges:
            start_yr = int(start_str)
            end_yr = 2026 if end_str.lower() in ("present", "current") else int(end_str)
            span = max(end_yr - start_yr, 1)
            total_years += min(span, 10)

        if total_years > 0:
            return min(total_years, 20.0)

        # If no explicit numbers, check entry count
        entries = re.split(r"(?:^|\n)\s*(?:role|at|experience|company)", text, re.IGNORECASE)
        return min(max(len(entries) * 1.5, 1.0), 10.0)

    @staticmethod
    def _text_match_score(
        skill_name: str,
        candidate_skills: str | None,
        candidate_experience: str | None,
        candidate_projects: str | None,
    ) -> float:
        """
        Skill Graph canonical text matching fallback.
        """
        norm = skill_normalizer.normalize(skill_name)
        canonical = norm["canonical"].lower()
        aliases = [a.lower() for a in norm.get("aliases", [])]

        skills_text = (candidate_skills or "").lower()
        exp_text = (candidate_experience or "").lower()
        proj_text = (candidate_projects or "").lower()

        for term in [canonical] + aliases:
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            if pattern.search(exp_text) or pattern.search(proj_text):
                return 80.0  # Proven practical implementation
            if pattern.search(skills_text):
                return 65.0  # Declared skill

        return 0.0

    def compute_score(
        self,
        job_requirements: List[Any],
        candidate_skills: str | None,
        candidate_experience: str | None,
        candidate_projects: str | None,
        candidate_education: str | None,
        candidate_certifications: str | None,
        requirement_evidence_map: Dict[str, List[Dict[str, Any]]],
        weights: Optional[ScoringWeights] = None,
    ) -> ScoreBreakdown:
        w = weights or self.default_weights

        total_w = (
            w.required_skills
            + w.experience
            + w.projects
            + w.education
            + w.additional_skills
        )
        norm_w = {
            "required_skills": w.required_skills / total_w,
            "experience": w.experience / total_w,
            "projects": w.projects / total_w,
            "education": w.education / total_w,
            "additional_skills": w.additional_skills / total_w,
        }

        # 1. Required & Additional Skill Score
        required_reqs = [r for r in job_requirements if getattr(r, "is_required", True)]
        optional_reqs = [r for r in job_requirements if not getattr(r, "is_required", True)]
        importance_multipliers = {"high": 1.2, "medium": 1.0, "low": 0.8}

        req_details = []
        semantic_scores_list = []
        covered_requirements_count = 0

        # Required skills calculation
        if required_reqs:
            weighted_req_points = 0.0
            max_req_points = 0.0

            for req in required_reqs:
                skill_name = getattr(req, "skill_name", str(req))
                imp = getattr(req, "importance", "medium") or "medium"
                imp_weight = importance_multipliers.get(imp.lower(), 1.0)
                max_req_points += imp_weight

                ev_list = requirement_evidence_map.get(skill_name, [])
                best_ev = ev_list[0] if ev_list else None

                if best_ev:
                    strength = best_ev.get("evidence_strength", 0.0)
                    sem = best_ev.get("semantic_score", 0.0)
                    semantic_scores_list.append(sem)
                    req_score = min(max(strength * 100.0, 0.0), 100.0)
                    if strength >= 0.5:
                        covered_requirements_count += 1
                else:
                    req_score = self._text_match_score(
                        skill_name, candidate_skills, candidate_experience, candidate_projects
                    )
                    if req_score >= 60.0:
                        covered_requirements_count += 1

                weighted_req_points += req_score * imp_weight
                req_details.append(
                    {
                        "skill": skill_name,
                        "is_required": True,
                        "importance": imp,
                        "score": round(req_score, 1),
                        "evidence_count": len(ev_list),
                        "scored_by": "vector_cross_encoder" if best_ev else "canonical_fallback",
                    }
                )

            required_skill_score = (
                (weighted_req_points / max_req_points) if max_req_points > 0 else 50.0
            )
        else:
            required_skill_score = 75.0

        # Additional / preferred skills calculation
        if optional_reqs:
            opt_points = 0.0
            for req in optional_reqs:
                skill_name = getattr(req, "skill_name", str(req))
                ev_list = requirement_evidence_map.get(skill_name, [])
                best_ev = ev_list[0] if ev_list else None
                if best_ev:
                    score = best_ev.get("evidence_strength", 0.0) * 100.0
                else:
                    score = self._text_match_score(
                        skill_name, candidate_skills, candidate_experience, candidate_projects
                    )
                opt_points += score
                req_details.append(
                    {
                        "skill": skill_name,
                        "is_required": False,
                        "importance": getattr(req, "importance", "low"),
                        "score": round(score, 1),
                        "evidence_count": len(ev_list),
                        "scored_by": "vector_cross_encoder" if best_ev else "canonical_fallback",
                    }
                )
            additional_skill_score = opt_points / len(optional_reqs)
        else:
            additional_skill_score = 50.0

        # 2. Experience Score (Calibrated by years and seniority)
        exp_evidence_chunks = [
            item
            for sublist in requirement_evidence_map.values()
            for item in sublist
            if item.get("section") == "experience"
        ]

        extracted_years = self._extract_years_of_experience(candidate_experience or "")
        seniority_bonus = 0.0
        exp_lower = (candidate_experience or "").lower()
        if any(w in exp_lower for w in ["lead", "staff", "principal", "architect", "senior"]):
            seniority_bonus = 10.0

        if exp_evidence_chunks:
            avg_strength = sum(c.get("evidence_strength", 0.0) for c in exp_evidence_chunks) / len(
                exp_evidence_chunks
            )
            # Duration factor (up to 30 pts) + Evidence strength (up to 60 pts) + Seniority
            duration_pts = min(extracted_years * 6.0, 30.0)
            exp_score = min((avg_strength * 60.0) + duration_pts + seniority_bonus, 100.0)
        elif candidate_experience and len(candidate_experience.strip()) > 30:
            duration_pts = min(extracted_years * 8.0, 45.0)
            exp_score = min(35.0 + duration_pts + seniority_bonus, 85.0)
        else:
            exp_score = 25.0

        # 3. Project Score
        proj_evidence_chunks = [
            item
            for sublist in requirement_evidence_map.values()
            for item in sublist
            if item.get("section") == "projects"
        ]
        if proj_evidence_chunks:
            avg_proj_strength = sum(
                c.get("evidence_strength", 0.0) for c in proj_evidence_chunks
            ) / len(proj_evidence_chunks)
            proj_score = min((avg_proj_strength * 80.0) + 20.0, 100.0)
        elif candidate_projects and len(candidate_projects.strip()) > 20:
            proj_score = 65.0
        else:
            proj_score = 30.0

        # 4. Education & Certification Score
        edu_score = 50.0
        edu_text = (candidate_education or "").lower()
        cert_text = (candidate_certifications or "").lower()

        if any(deg in edu_text for deg in ["ph.d", "phd", "doctorate"]):
            edu_score = 100.0
        elif any(deg in edu_text for deg in ["master", "m.s", "ms", "m.tech", "mba"]):
            edu_score = 90.0
        elif any(deg in edu_text for deg in ["bachelor", "b.s", "bs", "b.tech", "b.e"]):
            edu_score = 80.0
        elif any(deg in edu_text for deg in ["associate", "diploma"]):
            edu_score = 65.0

        if cert_text and len(cert_text.strip()) > 10:
            edu_score = min(edu_score + 10.0, 100.0)

        # 5. Deterministic Weighted Formula
        raw_final = (
            (norm_w["required_skills"] * required_skill_score)
            + (norm_w["experience"] * exp_score)
            + (norm_w["projects"] * proj_score)
            + (norm_w["education"] * edu_score)
            + (norm_w["additional_skills"] * additional_skill_score)
        )
        final_score = round(min(max(raw_final, 0.0), 100.0), 1)

        # 6. Confidence & Evidence Coverage Calibration
        total_reqs_count = len(job_requirements) if job_requirements else 1
        evidence_coverage = round(covered_requirements_count / total_reqs_count, 2)
        has_vector_evidence = len(semantic_scores_list) > 0
        confidence = round(0.70 + (0.25 * evidence_coverage) if has_vector_evidence else 0.65, 2)

        avg_semantic = (
            sum(semantic_scores_list) / len(semantic_scores_list) if semantic_scores_list else 0.5
        )

        return ScoreBreakdown(
            final_score=final_score,
            required_skill_score=round(required_skill_score, 1),
            experience_score=round(exp_score, 1),
            project_score=round(proj_score, 1),
            education_score=round(edu_score, 1),
            additional_skill_score=round(additional_skill_score, 1),
            semantic_score=round(avg_semantic, 3),
            confidence=confidence,
            evidence_coverage=evidence_coverage,
            weights_used={k: round(v, 3) for k, v in norm_w.items()},
            requirement_match_details=req_details,
        )


scoring_engine = ScoringEngine()
