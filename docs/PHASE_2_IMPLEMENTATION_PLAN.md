# Implementation Plan: Phase 2 — Supabase & Vector Storage

Establish the cloud foundation for **Phase 2**, integrating **Supabase** for Auth, private Storage buckets with signed URL access, PostgreSQL `pgvector` vector storage with HNSW cosine distance indexing, and Row Level Security (RLS) policies.

---

## User Review Required

> [!IMPORTANT]
> **Supabase Credentials & Dual-Mode Fallback**:
> The implementation supports **dual modes**:
> 1. **Live Supabase Mode**: When `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_KEY`) are present in `.env`, the backend connects directly to Supabase Auth, Supabase Storage buckets (`resumes`, `job-descriptions`), and PostgreSQL with `pgvector`.
> 2. **Local / Test Fallback Mode**: When credentials are not yet configured or when running automated CI tests, the system seamlessly falls back to local disk storage and mock authentication, ensuring tests run out-of-the-box without requiring an active Supabase cloud subscription.
>
> **Vector Dimensions**:
> Vectors are standardized to **768 dimensions** (native for Google Gemini `text-embedding-004`), indexed with `pgvector` using an **HNSW** (Hierarchical Navigable Small World) index with cosine distance (`vector_cosine_ops`).

---

## Proposed Changes

### 1. Dependencies & Configuration

#### [MODIFY] [`backend/requirements.txt`](../backend/requirements.txt)
- Add `supabase>=2.30.0`
- Add `pgvector>=0.5.0`
- Add `PyJWT>=2.8.0` and `cryptography>=42.0.0` (for JWT validation and token decoding)

#### [MODIFY] [`backend/app/core/config.py`](../backend/app/core/config.py)
- Add configuration settings:
  - `supabase_url: str = ""`
  - `supabase_key: str = ""` (Anon/Public key)
  - `supabase_service_role_key: str = ""` (Backend admin operations)
  - `supabase_jwt_secret: str = ""` (For offline JWT signature validation)
  - `storage_bucket_resumes: str = "resumes"`
  - `storage_bucket_jobs: str = "job-descriptions"`
  - `storage_signed_url_expiry: int = 3600` (1 hour)

---

### 2. Supabase Client & Storage Service

#### [NEW] [`backend/app/core/supabase.py`](../backend/app/core/supabase.py)
- Initialize Supabase client singleton using `supabase_url` and `supabase_service_role_key`.
- Provide client accessor with connection health check.

#### [NEW] [`backend/app/services/storage.py`](../backend/app/services/storage.py)
- Unified `StorageService` interface:
  - `upload_file(bucket: str, file_path: str, file_bytes: bytes, content_type: str) -> str`: Upload to private bucket.
  - `get_signed_url(bucket: str, file_path: str, expires_in: int = 3600) -> str`: Generate secure, time-limited signed URL for viewing/downloading.
  - `delete_file(bucket: str, file_path: str) -> bool`: Remove file from bucket.
  - Transparent fallback to local filesystem storage (`data/storage/...`) when running in local development or test mode.

#### [MODIFY] [`backend/app/api/resumes.py`](../backend/app/api/resumes.py)
- Route file uploads through `StorageService`.
- Add endpoint `GET /resumes/{resume_id}/signed-url` to generate signed access URLs for recruiters.

---

### 3. Supabase Auth & Role-Based Access Control (RBAC)

#### [NEW] [`backend/app/core/auth.py`](../backend/app/core/auth.py)
- FastAPI authentication dependencies:
  - `get_current_user(credentials: HTTPAuthorizationCredentials)`: Validates JWT token against Supabase Auth / secret, extracting `sub` (user ID), email, and `app_metadata.role`.
  - `require_role(allowed_roles: list[str])`: Enforces RBAC permissions (`recruiter`, `hiring_manager`, `admin`).
  - Permissive mock fallback during local testing when auth is disabled.

---

### 4. Vector Storage Schema & pgvector Setup

#### [NEW] [`backend/app/models/chunk.py`](../backend/app/models/chunk.py)
- Define `DocumentChunk` table for RAG embeddings:
  - `id`: Integer primary key
  - `document_type`: String (`resume`, `job_description`)
  - `document_id`: Integer (ref to `resumes.id` or `jobs.id`)
  - `candidate_id`: Integer (nullable, ref to `candidates.id`)
  - `job_id`: Integer (nullable, ref to `jobs.id`)
  - `section`: String (`experience`, `skills`, `education`, `requirements`, etc.)
  - `page_number`: Integer (page-level citation grounding)
  - `content`: Text (raw chunk text)
  - `embedding`: `VectorType(768)` (pgvector on Postgres, JSON array on SQLite)
  - `content_hash`: String (duplicate chunk prevention)
  - `created_at`: DateTime (UTC)

#### [MODIFY] [`backend/app/models/__init__.py`](../backend/app/models/__init__.py)
- Export `DocumentChunk`.

#### [NEW] [`backend/app/schemas/chunk.py`](../backend/app/schemas/chunk.py)
- Pydantic schemas for `DocumentChunkCreate`, `DocumentChunkResponse`, and `ChunkSearchQuery`.

---

### 5. Supabase SQL Migration & RLS Scripts

#### [NEW] [`backend/migrations/001_supabase_vector_and_rls.sql`](../backend/migrations/001_supabase_vector_and_rls.sql)
- Production PostgreSQL SQL script for Supabase SQL Editor:
  - Enable `vector` extension: `CREATE EXTENSION IF NOT EXISTS vector;`
  - Create HNSW cosine similarity index: `CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);`
  - Full-Text Search tsvector trigger on `content`.
  - Enable Row Level Security (RLS) on `jobs`, `candidates`, `resumes`, `document_chunks`.
  - Create RLS security policies restricting document access by recruiter tenant / organization.
  - Setup private storage buckets: `resumes`, `job-descriptions`, `exports`.

---

### 6. Automated Test Suite

#### [NEW] [`backend/tests/test_storage.py`](../backend/tests/test_storage.py)
- Test uploading to storage service, generating signed URLs, and file deletion.
- Test `GET /resumes/{resume_id}/signed-url` endpoint.

#### [NEW] [`backend/tests/test_auth.py`](../backend/tests/test_auth.py)
- Test JWT token validation, role extraction, unauthorized request handling (401/403).

#### [NEW] [`backend/tests/test_vector_chunk.py`](../backend/tests/test_vector_chunk.py)
- Test `DocumentChunk` model creation, metadata attributes, page number tracking, and cosine similarity query helpers.

---

## Verification Plan

### Automated Tests
1. Run complete test suite (Phase 1 + Phase 2 test modules):
   ```powershell
   & .\.venv\Scripts\python.exe -m pytest -v
   ```
   *Target: 28/28 tests passing with 100% success rate.*

### Manual Verification
1. Inspect OpenAPI endpoints:
   - Check `/resumes/{id}/signed-url` in OpenAPI spec.
2. Verify migration script:
   - Validate syntax of `001_supabase_vector_and_rls.sql`.
