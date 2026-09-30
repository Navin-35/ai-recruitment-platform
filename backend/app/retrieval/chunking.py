import re
from typing import Any, Dict, List, Optional
from app.ai.structured_outputs import ExtractedCandidateProfile, ExtractedJobData
from app.services.document_service import DocumentService, document_service


class ChunkItem:
    def __init__(
        self,
        section: str,
        content: str,
        page_number: Optional[int] = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.section = section
        self.content = content.strip()
        self.page_number = page_number or 1
        self.metadata = metadata or {}
        self.content_hash = DocumentService.compute_content_hash(self.content)


class SectionAwareChunker:
    """
    Decomposes documents into logical, semantic, section-aware chunks
    preserving accurate physical page numbers and section boundaries.
    """

    @classmethod
    def chunk_job_description(
        cls,
        jd_data: ExtractedJobData,
        raw_text: str,
        pages_data: Optional[List[Dict[str, Any]]] = None,
    ) -> List[ChunkItem]:
        chunks: List[ChunkItem] = []

        # 1. Job Summary chunk
        if jd_data.summary:
            summary_content = f"Job Title: {jd_data.title}\nCompany: {jd_data.company_name or 'N/A'}\nSummary: {jd_data.summary}"
            page_num = document_service.find_page_number_for_snippet(jd_data.summary, pages_data)
            chunks.append(
                ChunkItem(
                    section="summary",
                    content=summary_content,
                    page_number=page_num,
                    metadata={"title": jd_data.title, "company": jd_data.company_name},
                )
            )

        # 2. Per-requirement atomic chunks
        for req in jd_data.requirements:
            status = "Required" if req.is_required else "Preferred"
            years = (
                f" (Min {req.min_years_experience} years)"
                if req.min_years_experience
                else ""
            )
            req_content = (
                f"Requirement: {req.skill_name} | Status: {status} | "
                f"Importance: {req.importance} | Category: {req.category}{years}"
            )
            page_num = document_service.find_page_number_for_snippet(req.skill_name, pages_data)
            chunks.append(
                ChunkItem(
                    section="requirements",
                    content=req_content,
                    page_number=page_num,
                    metadata={
                        "skill_name": req.skill_name,
                        "is_required": req.is_required,
                        "importance": req.importance,
                        "category": req.category,
                    },
                )
            )

        # 3. Overall full text chunk if no atomic chunks created
        if not chunks:
            chunks.append(
                ChunkItem(
                    section="general",
                    content=raw_text[:2000],
                    page_number=1,
                )
            )

        return chunks

    @classmethod
    def chunk_candidate_profile(
        cls,
        profile: ExtractedCandidateProfile,
        raw_text: str,
        pages_data: Optional[List[Dict[str, Any]]] = None,
    ) -> List[ChunkItem]:
        chunks: List[ChunkItem] = []

        # 1. Professional Summary chunk
        if profile.summary:
            page_num = document_service.find_page_number_for_snippet(profile.summary, pages_data)
            chunks.append(
                ChunkItem(
                    section="summary",
                    content=f"Candidate Summary: {profile.summary}",
                    page_number=page_num,
                    metadata={"candidate_name": profile.name},
                )
            )

        # 2. Skills chunk
        if profile.skills:
            skills_text = ", ".join(profile.skills)
            page_num = document_service.find_page_number_for_snippet(skills_text, pages_data)
            chunks.append(
                ChunkItem(
                    section="skills",
                    content=f"Technical & Professional Skills: {skills_text}",
                    page_number=page_num,
                    metadata={"skills": profile.skills},
                )
            )

        # 3. Experience chunks (one chunk per experience entry with role and highlights)
        for exp in profile.experience:
            bullets = "\n- ".join(exp.highlights) if exp.highlights else "General responsibilities"
            techs = ", ".join(exp.skills_used) if exp.skills_used else "N/A"
            exp_text = (
                f"Experience at {exp.company} as {exp.role} ({exp.duration or 'Dates not specified'}):\n"
                f"Technologies Used: {techs}\n"
                f"- {bullets}"
            )
            page_num = document_service.find_page_number_for_snippet(f"{exp.role} {exp.company}", pages_data)
            chunks.append(
                ChunkItem(
                    section="experience",
                    content=exp_text,
                    page_number=page_num,
                    metadata={
                        "company": exp.company,
                        "role": exp.role,
                        "duration": exp.duration,
                        "skills_used": exp.skills_used,
                    },
                )
            )

        # 4. Projects chunks
        for proj in profile.projects:
            techs = ", ".join(proj.technologies) if proj.technologies else "N/A"
            proj_text = (
                f"Project: {proj.name}\n"
                f"Technologies: {techs}\n"
                f"Description: {proj.description}"
            )
            page_num = document_service.find_page_number_for_snippet(proj.name, pages_data)
            chunks.append(
                ChunkItem(
                    section="projects",
                    content=proj_text,
                    page_number=page_num,
                    metadata={"project_name": proj.name, "technologies": proj.technologies},
                )
            )

        # 5. Education chunk
        if profile.education:
            edu_lines = [
                f"{ed.degree} at {ed.institution} ({ed.year or 'Year not specified'})"
                for ed in profile.education
            ]
            edu_content = "Education:\n" + "\n".join(edu_lines)
            page_num = document_service.find_page_number_for_snippet(edu_lines[0], pages_data)
            chunks.append(
                ChunkItem(
                    section="education",
                    content=edu_content,
                    page_number=page_num,
                    metadata={"education_count": len(profile.education)},
                )
            )

        # 6. Certifications chunk
        if profile.certifications:
            cert_content = "Certifications & Credentials:\n- " + "\n- ".join(profile.certifications)
            page_num = document_service.find_page_number_for_snippet(profile.certifications[0], pages_data)
            chunks.append(
                ChunkItem(
                    section="certifications",
                    content=cert_content,
                    page_number=page_num,
                    metadata={"certifications": profile.certifications},
                )
            )

        # Fallback if no structured sections were extracted
        if not chunks:
            sections = DocumentService.detect_sections(raw_text)
            for sec_name, content in sections.items():
                if content.strip():
                    page_num = document_service.find_page_number_for_snippet(content[:100], pages_data)
                    chunks.append(
                        ChunkItem(
                            section=sec_name,
                            content=content,
                            page_number=page_num,
                        )
                    )

        return chunks
