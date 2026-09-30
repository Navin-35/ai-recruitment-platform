from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractedRequirement(BaseModel):
    skill_name: str = Field(..., description="Canonical or standard name of the skill or requirement")
    is_required: bool = Field(default=True, description="True if mandatory requirement, False if preferred/nice-to-have")
    importance: str = Field(default="high", description="'high', 'medium', or 'low'")
    category: str = Field(
        default="general",
        description="Category: 'language', 'framework', 'database', 'cloud', 'devops', 'tool', or 'concept'",
    )
    min_years_experience: Optional[float] = Field(
        default=None, description="Minimum years of experience required, if mentioned"
    )


class ExtractedJobData(BaseModel):
    title: str = Field(..., description="Official job title")
    company_name: Optional[str] = Field(default=None, description="Company name if mentioned")
    summary: str = Field(..., description="Executive summary of the role and responsibilities")
    requirements: List[ExtractedRequirement] = Field(
        default_factory=list, description="Decomposed atomic requirements"
    )


class ExtractedExperience(BaseModel):
    company: str = Field(..., description="Company or organization name")
    role: str = Field(..., description="Job title or role held")
    duration: Optional[str] = Field(default=None, description="Dates or duration, e.g., '2021 - 2023' or '2 years'")
    skills_used: List[str] = Field(default_factory=list, description="Technologies and skills used in this role")
    highlights: List[str] = Field(
        default_factory=list, description="Key accomplishments, metrics, or responsibilities"
    )


class ExtractedProject(BaseModel):
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Description of the project and outcome")
    technologies: List[str] = Field(default_factory=list, description="Technologies and tools used")


class ExtractedEducation(BaseModel):
    degree: str = Field(..., description="Degree or program, e.g., 'B.S. Computer Science'")
    institution: str = Field(..., description="University or school name")
    year: Optional[str] = Field(default=None, description="Graduation year or dates")


class ExtractedCandidateProfile(BaseModel):
    name: Optional[str] = Field(default=None, description="Candidate's full name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    summary: Optional[str] = Field(default=None, description="Professional summary or bio")
    skills: List[str] = Field(default_factory=list, description="List of all technical and professional skills")
    experience: List[ExtractedExperience] = Field(default_factory=list, description="Work experience history")
    projects: List[ExtractedProject] = Field(default_factory=list, description="Notable projects")
    education: List[ExtractedEducation] = Field(default_factory=list, description="Educational background")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications or licenses")


class StrengthEvidence(BaseModel):
    skill_or_area: str = Field(..., description="Strength or matching requirement")
    reason: str = Field(..., description="Why candidate meets or exceeds this requirement")
    evidence_quote: str = Field(..., description="Direct citation or quote from candidate evidence")
    chunk_id: Optional[int] = Field(default=None, description="Referenced evidence chunk ID")


class GapEvidence(BaseModel):
    skill_or_requirement: str = Field(..., description="Missing or insufficient requirement")
    severity: str = Field(default="medium", description="'high' for mandatory missing, 'medium' for partial, 'low' for nice-to-have")
    reason: str = Field(..., description="Explanation of the gap or lack of evidence in resume")


class GroundedExplanation(BaseModel):
    summary: str = Field(..., description="Comprehensive recruiter-facing synthesis explaining the match score")
    overall_fit: str = Field(default="moderate", description="'strong', 'moderate', or 'weak'")
    strengths: List[StrengthEvidence] = Field(default_factory=list, description="Verified strengths with evidence citations")
    gaps: List[GapEvidence] = Field(default_factory=list, description="Detected skill or experience gaps")
    experience_analysis: str = Field(..., description="Evaluation of seniority, role relevance, and project impact")
    recruiter_recommendation: str = Field(..., description="Actionable recommendation: whether to interview, technical screen, or pass")
