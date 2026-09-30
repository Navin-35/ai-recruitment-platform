JOB_EXTRACTION_PROMPT = """You are an expert technical talent acquisition and recruitment AI.
Analyze the following Job Description and extract structured information, decomposing the job into atomic requirements.

Strict Guidelines:
1. Identify all core required skills vs preferred / optional skills.
2. For each requirement, determine its importance (high, medium, low) and category (language, framework, database, cloud, devops, tool, concept).
3. Do not combine multiple unrelated skills into one requirement (e.g., separate "Python and Kubernetes" into "Python" and "Kubernetes").
4. If years of experience is stated, capture min_years_experience.
5. Provide a crisp summary of the role.

Return ONLY valid JSON matching this schema:
{
  "title": "string",
  "company_name": "string or null",
  "summary": "string",
  "requirements": [
    {
      "skill_name": "string",
      "is_required": true/false,
      "importance": "high|medium|low",
      "category": "language|framework|database|cloud|devops|tool|concept",
      "min_years_experience": number or null
    }
  ]
}

Job Description Text:
\"\"\"
{text}
\"\"\"
"""


RESUME_EXTRACTION_PROMPT = """You are an expert resume parsing AI.
Analyze the following resume text and extract complete, structured candidate information.

Strict Guidelines:
1. Extract candidate name, contact email, and phone if present.
2. Extract all distinct technical and domain skills into a clean list of canonical names.
3. For each past experience: extract company, role title, duration, technologies/skills used, and key responsibility bullets or accomplishments.
4. For projects: extract project name, description, and technologies.
5. For education: extract degree, institution, and graduation year.
6. For certifications: extract list of certifications.
7. If any field is missing or ambiguous in the resume, leave it null or empty array. DO NOT hallucinate.

Return ONLY valid JSON matching this schema:
{
  "name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "summary": "string or null",
  "skills": ["string"],
  "experience": [
    {
      "company": "string",
      "role": "string",
      "duration": "string or null",
      "skills_used": ["string"],
      "highlights": ["string"]
    }
  ],
  "projects": [
    {
      "name": "string",
      "description": "string",
      "technologies": ["string"]
    }
  ],
  "education": [
    {
      "degree": "string",
      "institution": "string",
      "year": "string or null"
    }
  ],
  "certifications": ["string"]
}

Resume Text:
\"\"\"
{text}
\"\"\"
"""


EXPLANATION_PROMPT = """You are an AI Recruitment Explainability Engine.
Your task is to generate an objective, grounded evaluation explaining why a candidate received their match score for a job.

CRITICAL INSTRUCTIONS:
1. Grounding: You MUST only cite facts present in the Candidate Evidence Chunks and Profile provided. Never invent experiences, metrics, or technologies not present in the evidence.
2. Strengths: For each strength, cite the specific evidence chunk ID (e.g. Chunk #12) and quote the supporting evidence snippet.
3. Skill Gaps: For missing or weak requirements, state the gap clearly and explain the severity (high for missing mandatory requirements, medium for partial, low for optional).
4. Deterministic Score Alignment: The candidate has received the following deterministic scores:
   - Final Score: {final_score}/100
   - Required Skill Score: {skill_score}/100
   - Experience Score: {experience_score}/100
   - Project Score: {project_score}/100
   - Education/Certifications Score: {education_score}/100
   Your qualitative synthesis MUST align with these mathematical scores.
5. Recruiter Recommendation: Provide a clear, actionable hiring recommendation (e.g., "Advance to Technical Interview", "Schedule Phone Screen focused on [Topic]", or "Do Not Advance").

Job Title: {job_title}
Job Description:
{job_description}

Job Requirements:
{requirements_summary}

Candidate Profile:
Name: {candidate_name}
Skills: {candidate_skills}
Experience Summary: {experience_summary}

Candidate Evidence Chunks:
{evidence_chunks_text}

Detected Skill Gaps:
{skill_gaps_text}

Return ONLY valid JSON matching this schema:
{
  "summary": "string",
  "overall_fit": "strong|moderate|weak",
  "strengths": [
    {
      "skill_or_area": "string",
      "reason": "string",
      "evidence_quote": "string",
      "chunk_id": number or null
    }
  ],
  "gaps": [
    {
      "skill_or_requirement": "string",
      "severity": "high|medium|low",
      "reason": "string"
    }
  ],
  "experience_analysis": "string",
  "recruiter_recommendation": "string"
}
"""


QUERY_EXPANSION_PROMPT = """You are an information retrieval query expansion model for recruitment RAG.
Given the following job requirement, output a JSON list of 3 to 6 synonym keywords, related technical terms, frameworks, and equivalent expressions to expand semantic and lexical retrieval.

Requirement: "{requirement}"

Return ONLY a JSON array of strings, for example: ["Python", "FastAPI", "Django", "REST APIs", "backend development"]
"""
