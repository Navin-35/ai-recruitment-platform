# Implementation Plan: Phase 1 — Database Foundation & Core REST API

Complete and harden **Phase 1: Foundation**, establishing a production-ready relational database foundation and a comprehensive FastAPI CRUD API covering all core entities of the recruitment platform (Jobs, Candidates, Resumes, Skills, Job Requirements, and Candidate Matches), backed by an automated integration test suite.

## Background & Current State

The repository has an initial prototype of the database models in [`backend/app/models`](../backend/app/models) and basic endpoints in [`backend/app/api`](../backend/app/api). However:
- **Incomplete CRUD Operations**: Jobs and Candidates only had `POST` and `GET`. Update (`PUT`) and Delete (`DELETE`) were missing.
- **Missing Routers & Schemas**: Models existed for `Skill`, `JobRequirement`, and `CandidateMatch`, but there were no Pydantic schemas or API routers for them.
- **Missing ORM Relationships**: SQLAlchemy models did not define `relationship(...)` mappings and foreign key cascades, which could lead to orphan records upon deletion.
- **Zero Test Coverage**: [`backend/tests/`](../backend/tests) only contained an empty `__init__.py`. No test suite validated API contract integrity or database constraints.

---

## User Review Required

> [!IMPORTANT]
> **Database Cascade Rules**: When a `Job` or `Candidate` is deleted, all dependent records (e.g. resumes, job requirements, and candidate matches) will be deleted via `cascade="all, delete-orphan"` to preserve data integrity.
> **Testing Environment**: Tests run against an in-memory or temporary SQLite database (`sqlite:///:memory:`) to ensure local `recruitment.db` data is never modified during test runs.

---

## Proposed Changes

### 1. Dependencies & Environment
- Install `pytest` and `httpx` in the local virtual environment (`backend/.venv`) for test execution.
- Update `backend/requirements.txt` to include `httpx` and `pytest`.

---

### 2. Relational Models & Schemas

#### [MODIFY] [`job.py`](../backend/app/models/job.py)
- Add `updated_at` column.
- Add bidirectional `relationship` to `JobRequirement` and `CandidateMatch` with cascade deletion.

#### [MODIFY] [`candidate.py`](../backend/app/models/candidate.py)
- Add `updated_at` column.
- Add bidirectional `relationship` to `Resume` and `CandidateMatch` with cascade deletion.

#### [MODIFY] [`resume.py`](../backend/app/models/resume.py)
- Add bidirectional `relationship` to `Candidate`.

#### [MODIFY] [`job_requirement.py`](../backend/app/models/job_requirement.py)
- Add bidirectional `relationship` to `Job`.

#### [MODIFY] [`match.py`](../backend/app/models/match.py)
- Add bidirectional `relationship` to `Job` and `Candidate`.

---

### 3. Pydantic Schemas

#### [MODIFY] [`backend/app/schemas/job.py`](../backend/app/schemas/job.py)
- Add `JobUpdate` schema (optional fields for partial updates).
- Add `JobDetailResponse` including nested requirements.

#### [MODIFY] [`backend/app/schemas/candidate.py`](../backend/app/schemas/candidate.py)
- Add `CandidateUpdate` schema.
- Add `CandidateDetailResponse` including nested resumes.

#### [NEW] [`backend/app/schemas/skill.py`](../backend/app/schemas/skill.py)
- Define `SkillCreate`, `SkillUpdate`, and `SkillResponse`.

#### [NEW] [`backend/app/schemas/job_requirement.py`](../backend/app/schemas/job_requirement.py)
- Define `JobRequirementCreate`, `JobRequirementUpdate`, and `JobRequirementResponse`.

#### [NEW] [`backend/app/schemas/match.py`](../backend/app/schemas/match.py)
- Define `CandidateMatchCreate`, `CandidateMatchResponse`.

#### [MODIFY] [`backend/app/schemas/__init__.py`](../backend/app/schemas/__init__.py)
- Re-export all schema classes.

---

### 4. API Endpoints

#### [MODIFY] [`backend/app/api/jobs.py`](../backend/app/api/jobs.py)
- Add `PUT /jobs/{job_id}` (update job metadata or status).
- Add `DELETE /jobs/{job_id}` (delete job and cascade).

#### [MODIFY] [`backend/app/api/candidates.py`](../backend/app/api/candidates.py)
- Add `PUT /candidates/{candidate_id}` (update candidate details).
- Add `DELETE /candidates/{candidate_id}` (delete candidate and cascade).

#### [MODIFY] [`backend/app/api/resumes.py`](../backend/app/api/resumes.py)
- Add `GET /resumes/{resume_id}` (get single resume details).
- Add `GET /resumes/candidate/{candidate_id}` (list all resumes for a candidate).
- Add `DELETE /resumes/{resume_id}` (delete record and remove physical file from disk).

#### [NEW] [`backend/app/api/skills.py`](../backend/app/api/skills.py)
- Add `POST /skills/` (create skill).
- Add `GET /skills/` (list skills with optional search filter).
- Add `GET /skills/{skill_id}` (get skill by id).
- Add `DELETE /skills/{skill_id}` (delete skill).

#### [NEW] [`backend/app/api/job_requirements.py`](../backend/app/api/job_requirements.py)
- Add `POST /jobs/{job_id}/requirements` (add requirement to a job).
- Add `GET /jobs/{job_id}/requirements` (list requirements for a job).
- Add `DELETE /jobs/{job_id}/requirements/{requirement_id}` (delete requirement).

#### [NEW] [`backend/app/api/matches.py`](../backend/app/api/matches.py)
- Add `POST /matches/` (record candidate match evaluation).
- Add `GET /matches/job/{job_id}` (list ranked matches for a job).
- Add `GET /matches/{match_id}` (get single match details with explanation).

#### [MODIFY] [`backend/app/api/__init__.py`](../backend/app/api/__init__.py) and [`backend/app/main.py`](../backend/app/main.py)
- Register all new routers under the FastAPI application.

---

### 5. Test Suite

#### [NEW] [`backend/tests/conftest.py`](../backend/tests/conftest.py)
- SQLite in-memory engine fixture overriding `get_db`.
- `TestClient` test fixture.

#### [NEW] [`backend/tests/test_jobs.py`](../backend/tests/test_jobs.py)
- Tests for creating, listing, retrieving, updating, and deleting jobs.

#### [NEW] [`backend/tests/test_candidates.py`](../backend/tests/test_candidates.py)
- Tests for creating, listing, retrieving, updating, and deleting candidates.

#### [NEW] [`backend/tests/test_resumes.py`](../backend/tests/test_resumes.py)
- Tests for resume upload validation, retrieval, candidate resume queries, and deletion.

#### [NEW] [`backend/tests/test_skills_and_requirements.py`](../backend/tests/test_skills_and_requirements.py)
- Tests for skills catalog management and job requirements attachment.

#### [NEW] [`backend/tests/test_matches.py`](../backend/tests/test_matches.py)
- Tests for match record creation, retrieval by job, and verification of score fields.

---

## Verification Plan

### Automated Tests
1. Execute pytest suite in the virtual environment:
   ```powershell
   & .\.venv\Scripts\python.exe -m pytest -v
   ```
2. Verify all test modules (`test_jobs`, `test_candidates`, `test_resumes`, `test_skills_and_requirements`, `test_matches`) pass with 100% success.

### Manual Verification
1. Start FastAPI server or query OpenAPI schema via Python:
   - Check `app.openapi()` contains all routes (`/jobs`, `/candidates`, `/resumes`, `/skills`, `/matches`).
2. Run database migration/initialization script:
   - Run `& .\.venv\Scripts\python.exe check_db.py` to confirm all tables and foreign keys are intact.
