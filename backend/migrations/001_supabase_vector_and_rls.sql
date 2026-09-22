-- =========================================================================
-- AI RECRUITMENT & CANDIDATE INTELLIGENCE PLATFORM
-- Phase 2: Supabase pgvector Extension, Storage Buckets, and RLS Policies
-- =========================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. DOCUMENT CHUNKS TABLE (RAG & Hybrid Retrieval Engine)
CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_type VARCHAR(50) NOT NULL, -- 'resume' or 'job_description'
    document_id BIGINT NOT NULL,
    candidate_id BIGINT REFERENCES candidates(id) ON DELETE CASCADE,
    job_id BIGINT REFERENCES jobs(id) ON DELETE CASCADE,
    section VARCHAR(100) NOT NULL DEFAULT 'general', -- 'experience', 'skills', 'projects', 'education', 'requirements'
    page_number INT,
    content TEXT NOT NULL,
    content_hash VARCHAR(64),
    embedding VECTOR(768), -- Optimized for Gemini text-embedding-004 (768-dim)
    search_tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. INDEXES FOR HIGH-PERFORMANCE HYBRID RETRIEVAL
-- HNSW index for fast approximate nearest neighbor (ANN) cosine similarity search
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw 
ON document_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- GIN index for Lexical / Full-Text Search (tsvector)
CREATE INDEX IF NOT EXISTS idx_document_chunks_search_tsv 
ON document_chunks 
USING gin (search_tsv);

-- Relational indexes for candidate and job filtering
CREATE INDEX IF NOT EXISTS idx_document_chunks_candidate_id ON document_chunks(candidate_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_job_id ON document_chunks(job_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_section ON document_chunks(section);

-- 4. PRIVATE SUPABASE STORAGE BUCKETS
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
    ('resumes', 'resumes', false, 10485760, ARRAY['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']),
    ('job-descriptions', 'job-descriptions', false, 5242880, ARRAY['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']),
    ('exports', 'exports', false, 20971520, ARRAY['application/pdf', 'application/json', 'text/csv'])
ON CONFLICT (id) DO NOTHING;

-- 5. ROW LEVEL SECURITY (RLS) POLICIES
-- Enable RLS across core tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Policy: Allow authenticated recruiters full access to recruitment data
CREATE POLICY "Authenticated users can manage jobs"
ON jobs FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can manage candidates"
ON candidates FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can manage resumes"
ON resumes FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can manage matches"
ON candidate_matches FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authenticated users can manage document chunks"
ON document_chunks FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Storage bucket access policies
CREATE POLICY "Allow authenticated users to read resumes"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'resumes');

CREATE POLICY "Allow authenticated users to upload resumes"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'resumes');

CREATE POLICY "Allow authenticated users to delete resumes"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'resumes');
