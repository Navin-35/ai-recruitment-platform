# System Workflows, Architecture & Engineering Roadmap

> **Visual architectural diagrams, workflow specifications, and phased implementation milestones for the AI Recruitment & Candidate Intelligence Platform.**  
> *Raw Mermaid Source File: [`docs/project_workflow_and_phases.mmd`](project_workflow_and_phases.mmd)*

---

## 📑 Table of Contents
1. [Master System Architecture & Pipelines](#1-master-system-architecture--pipelines)
2. [Pipeline A — Job Intelligence Workflow](#2-pipeline-a--job-intelligence-workflow)
3. [Pipeline B — Candidate Intelligence Workflow](#3-pipeline-b--candidate-intelligence-workflow)
4. [Pipeline C — Matching & Grounded Explanation Workflow](#4-pipeline-c--matching--grounded-explanation-workflow)
5. [LangGraph Execution State Machine](#5-langgraph-execution-state-machine)
6. [Data Model & Entity-Relationship Diagram](#6-data-model--entity-relationship-diagram)
7. [9-Phase Implementation Roadmap](#7-9-phase-implementation-roadmap)

---

## 1. Master System Architecture & Pipelines

This diagram represents the end-to-end topology: from user interaction in the React dashboard, through FastAPI and LangGraph orchestration, to Supabase Storage, pgvector, deterministic scoring, and Langfuse observability.

```mermaid
flowchart TB
    subgraph UI_LAYER ["1. User Interaction & Access Layer"]
        RECRUITER["Recruiter / Hiring Manager"]
        WEB_APP["React + Vite + TypeScript Frontend\n(Job Workspace & Candidate Leaderboard)"]
        AUTH_SVC["Supabase Auth Service\n(JWT Tokens, RBAC, Multi-Tenant RLS)"]
        
        RECRUITER -->|"Interacts via UI"| WEB_APP
        WEB_APP -->|"Authenticates"| AUTH_SVC
    end

    subgraph BACKEND_LAYER ["2. API Gateway & Orchestration Core"]
        FASTAPI["FastAPI REST Backend\n(/api/v1/jobs, /candidates, /matches)"]
        LANGGRAPH["LangGraph Workflow Orchestrator\n(Deterministic Multi-Step State Machine)"]
        REDIS_Q["Redis Task Queue\n(Celery / Arq Async Worker)"]
        
        WEB_APP -->|"REST API Calls + JWT"| FASTAPI
        FASTAPI -->|"Dispatches Sync Tasks"| LANGGRAPH
        FASTAPI -->|"Enqueues Batch Jobs"| REDIS_Q
        REDIS_Q -->|"Pulls Background Jobs"| LANGGRAPH
    end

    subgraph DOC_INTELLIGENCE ["3. Document Processing & Structured Extraction"]
        DOC_STORAGE["Supabase Storage\n(Encrypted Private S3 Buckets)"]
        PARSER["Document Parsing Engine\n(PyMuPDF / pdfplumber / python-docx)"]
        OCR_FALLBACK["OCR Fallback Engine\n(Tesseract / Visual Extraction)"]
        GEMINI_EXTRACT["Gemini 1.5/2.0 Flash Extraction\n(Pydantic Structured JSON Schema)"]
        SKILL_ONTOLOGY["Skill Graph & Ontology\n(Canonical Normalization & Aliases)"]

        FASTAPI -->|"Stores Raw PDF/DOCX"| DOC_STORAGE
        LANGGRAPH -->|"Fetches Document"| DOC_STORAGE
        DOC_STORAGE -->|"Raw Stream"| PARSER
        PARSER -->|"Scanned / Image Fallback"| OCR_FALLBACK
        PARSER -->|"Clean Raw Text"| GEMINI_EXTRACT
        OCR_FALLBACK -->|"Recovered Text"| GEMINI_EXTRACT
        GEMINI_EXTRACT -->|"Extracted Skills"| SKILL_ONTOLOGY
    end

    subgraph RETRIEVAL_LAYER ["4. Hybrid Retrieval & Vector Database (Supabase)"]
        CHUNKER["Section-Aware Chunker\n(Experience, Projects, Education, Skills)"]
        EMBED_SVC["Gemini Embeddings Service\n(text-embedding-004 / 768-dim)"]
        PG_VECTOR[("PostgreSQL + pgvector\n(HNSW Cosine Vector Index)")]
        PG_FTS[("PostgreSQL FTS\n(tsvector Lexical / Keyword Index)")]
        RRF_FUSION["Reciprocal Rank Fusion (RRF)\n(Combines Vector & Lexical Ranks)"]
        RERANKER["Cross-Encoder Reranker\n(Deep Precision Context Filtering)"]

        GEMINI_EXTRACT -->|"Candidate Sections"| CHUNKER
        CHUNKER -->|"Text Chunks"| EMBED_SVC
        EMBED_SVC -->|"Dense Vectors"| PG_VECTOR
        CHUNKER -->|"Exact Keywords & Terms"| PG_FTS

        PG_VECTOR -->|"Top-K Semantic Matches"| RRF_FUSION
        PG_FTS -->|"Top-K Keyword Matches"| RRF_FUSION
        RRF_FUSION -->|"Fused Candidates"| RERANKER
    end

    subgraph MATCH_ENGINE ["5. Deterministic Matching & Grounded Explanations"]
        DECOMPOSE["JD Requirement Decomposition\n(Atomic Criteria: Skills, Exp, Education)"]
        EVIDENCE_STORE["Auditable Evidence Collector\n(Page Numbers, Bullet Points, Snippets)"]
        SCORE_ENGINE["Deterministic Scoring Engine\n(40% Skills + 25% Exp + 20% Proj + 10% Edu + 5% Add)"]
        SKILL_GAP["Skill-Gap Analyzer\n(Missing vs Met Qualifications Matrix)"]
        EXPLAINER["Grounded LLM Explainer (Gemini)\n(Strictly Generates Explanations with Citations)"]
        
        LANGGRAPH -->|"Inputs JD Requirements"| DECOMPOSE
        DECOMPOSE -->|"Executes Per-Requirement Search"| PG_VECTOR
        DECOMPOSE -->|"Executes Per-Requirement Search"| PG_FTS
        RERANKER -->|"Verified Snippets"| EVIDENCE_STORE
        EVIDENCE_STORE -->|"Evidence Metrics"| SCORE_ENGINE
        SCORE_ENGINE -->|"Evaluates Deficits"| SKILL_GAP
        SCORE_ENGINE -->|"Mathematical Scores"| EXPLAINER
        EVIDENCE_STORE -->|"Verified Snippets"| EXPLAINER
        SKILL_GAP -->|"Gaps Data"| EXPLAINER
    end

    subgraph OUTPUT_OBSERVABILITY ["6. Output Persistence & Observability"]
        PG_RELATIONAL[("PostgreSQL Relational DB\n(Jobs, Candidates, MatchRuns, Scores)")]
        LANGFUSE["Langfuse Observability & Tracing\n(Latency, Token Costs, Recall@K, Evals)"]
        LEADERBOARD["Recruiter Dashboard View\n(Rankings, Fit Breakdown & Evidence Drawer)"]

        SCORE_ENGINE -->|"Persists Final Scores"| PG_RELATIONAL
        EXPLAINER -->|"Persists Grounded Summary"| PG_RELATIONAL
        LANGGRAPH -->|"Emits Traces & Spans"| LANGFUSE
        FASTAPI -->|"Monitors API Latency"| LANGFUSE
        PG_RELATIONAL -->|"Queries Match Results"| FASTAPI
        FASTAPI -->|"Streams Results"| LEADERBOARD
    end
```

---

## 2. Pipeline A — Job Intelligence Workflow

Transforms raw job posts into structured, queryable atomic requirements with embeddings and canonical skill mappings.

```mermaid
flowchart TD
    A[Recruiter Uploads JD] --> B{Input Format}
    B -->|PDF / DOCX File| C[Document Validator & Magic Byte Check]
    B -->|Direct Text| D[Text Sanitizer & Normalizer]
    C --> E[PyMuPDF / pdfplumber Text Extraction]
    E --> D
    D --> F[Gemini 1.5/2.0 Flash Extraction]
    F --> G[Pydantic Structured Validation]
    G --> H[Requirement Decomposition: Atomic Criteria]
    H --> I[Canonical Skill Graph Normalization]
    I --> J[Gemini Text Embeddings: 768-dim]
    J --> K[(Store in Postgres: jobs, job_requirements, vectors)]
    K --> L[Job State: READY_FOR_MATCHING]
```

---

## 3. Pipeline B — Candidate Intelligence Workflow

Processes unstructured resumes into section-aware chunks, structured entities, embeddings, and full-text indexes.

```mermaid
flowchart TD
    A[Resume Upload via API] --> B[Store File in Supabase Private Bucket]
    B --> C[Publish Task to Redis Queue]
    C --> D[Async Worker Picks Up Job]
    D --> E[Validate File Format & Scan Corrupted Files]
    E --> F[Document Parser: PyMuPDF / docx]
    F --> G{Text Density Check}
    G -->|Dense Text| H[Section Detection Engine]
    G -->|Scanned / Image| I[OCR Engine: Tesseract Fallback]
    I --> H
    H --> J[Gemini Profile Extraction into Structured JSON]
    J --> K[Pydantic Schema Validation]
    K --> L[Extract Skills, Experience, Education, Projects]
    L --> M[Section-Aware Chunking with Metadata]
    M --> N[Generate Gemini Embeddings]
    N --> O[(Postgres: candidates, chunks, pgvector, tsvector)]
    O --> P[Candidate Status: INDEXED & READY]
```

---

## 4. Pipeline C — Matching & Grounded Explanation Workflow

Executes requirement-level hybrid RAG, applies deterministic mathematical scoring, performs skill-gap analysis, and generates cited justifications.

```mermaid
flowchart TD
    A[Trigger Match Run: Job ID vs Candidate IDs] --> B[Fetch Atomic Job Requirements]
    B --> C[Loop Over Each Requirement]
    
    subgraph HYBRID_RAG ["Requirement-Level Hybrid Retrieval"]
        C --> D1[Vector Search: pgvector Cosine Sim]
        C --> D2[Keyword Search: PostgreSQL FTS]
        D1 --> E[Reciprocal Rank Fusion - RRF]
        D2 --> E
        E --> F[Cross-Encoder Reranker]
        F --> G[Extract Top-K Evidence Snippets]
    end
    
    G --> H[Aggregate Evidence across all Requirements]
    H --> I[Evaluate Category Fulfillment]
    
    subgraph DETERMINISTIC_SCORING ["Deterministic Scoring Engine"]
        I --> J1[Required Skills Score: 40%]
        I --> J2[Relevant Experience Score: 25%]
        I --> J3[Projects Score: 20%]
        I --> J4[Education / Certs Score: 10%]
        I --> J5[Additional Skills Score: 5%]
        J1 & J2 & J3 & J4 & J5 --> K[Weighted Mathematical Sum]
    end

    K --> L[Skill-Gap Engine: Met vs Missing Skills]
    K --> M[Grounded LLM Explainer: Gemini]
    L --> M
    H --> M
    M --> N[Synthesize Justification with Page & Section Citations]
    N --> O[(Save match_results, requirement_matches, explanations)]
    O --> P[Render Candidate Leaderboard & Evidence Panel]
```

---

## 5. LangGraph Execution State Machine

Illustrates the fault-tolerant state transitions executed by the LangGraph orchestrator.

```mermaid
stateDiagram-v2
    [*] --> ValidateJob
    ValidateJob --> LoadCandidate: Valid JD
    ValidateJob --> JobError: Invalid / Empty JD

    LoadCandidate --> DecomposeRequirements: Candidate Exists
    LoadCandidate --> CandidateError: Not Found

    DecomposeRequirements --> RetrieveEvidence: Requirements Generated
    RetrieveEvidence --> RerankEvidence: Chunks Retrieved
    RerankEvidence --> EvaluateRequirements: Evidence Filtered

    EvaluateRequirements --> ComputeScores: Fulfillment Calculated
    ComputeScores --> AnalyzeSkillGaps: Numerical Score Ready
    AnalyzeSkillGaps --> GenerateGroundedExplanation: Gaps Identified

    GenerateGroundedExplanation --> PersistResults: Citations Formed
    PersistResults --> EmitLangfuseTelemetry: Saved to Postgres
    EmitLangfuseTelemetry --> [*]: Complete

    JobError --> [*]
    CandidateError --> [*]
```

---

## 6. Data Model & Entity-Relationship Diagram

Core relational schema showing how jobs, candidates, chunks, vectors, and match scores interconnect.

```mermaid
erDiagram
    ORGANIZATION ||--o{ RECRUITER : employs
    ORGANIZATION ||--o{ JOB : owns
    ORGANIZATION ||--o{ CANDIDATE : manages

    JOB ||--o{ JOB_REQUIREMENT : defines
    JOB ||--o{ MATCH_RUN : initiates

    CANDIDATE ||--o{ CANDIDATE_DOCUMENT : uploads
    CANDIDATE_DOCUMENT ||--o{ CHUNK : splits_into
    CHUNK ||--o{ CHUNK_EMBEDDING : indexed_as

    CANDIDATE ||--o{ CANDIDATE_SKILL : possesses
    CANDIDATE_SKILL }o--|| SKILL : references
    JOB_REQUIREMENT }o--|| SKILL : requires

    MATCH_RUN ||--o{ MATCH_RESULT : evaluates
    CANDIDATE ||--o{ MATCH_RESULT : receives

    MATCH_RESULT ||--o{ REQUIREMENT_MATCH : itemizes
    REQUIREMENT_MATCH }o--|| JOB_REQUIREMENT : against
    REQUIREMENT_MATCH ||--o{ EVIDENCE_CITATION : proven_by
```

---

## 7. 9-Phase Implementation Roadmap

The progressive milestone roadmap from database foundation to full enterprise observability.

```mermaid
flowchart TD
    subgraph PHASE1 ["Phase 1: Foundation (Current)"]
        M1["• SQLite / Postgres Core Tables\n• SQLAlchemy / SQLModel Setup\n• Initial FastAPI CRUD Endpoints"]
    end

    subgraph PHASE2 ["Phase 2: Supabase & Vector Storage"]
        M2["• Supabase Project & Auth Setup\n• pgvector Extension & HNSW Index\n• Private S3 Storage Buckets & RLS"]
    end

    subgraph PHASE3 ["Phase 3: Document Processing Engine"]
        M3["• PyMuPDF & pdfplumber PDF Extraction\n• python-docx Parser\n• Tesseract OCR Fallback for Scans"]
    end

    subgraph PHASE4 ["Phase 4: Structured Intelligence"]
        M4["• Gemini 1.5/2.0 Flash Extraction\n• Pydantic Profile & JD Validation\n• Relational Skill Graph & Normalization"]
    end

    subgraph PHASE5 ["Phase 5: Hybrid RAG & Reranking"]
        M5["• Gemini Embeddings (text-embedding-004)\n• Section-aware Chunking with Page Tags\n• pgvector Cosine + Postgres FTS\n• Reciprocal Rank Fusion & Cross-Encoder"]
    end

    subgraph PHASE6 ["Phase 6: Matching & Deterministic Scoring"]
        M6["• Atomic Requirement-Level Matching\n• Deterministic Weighted Scoring Algorithm\n• Automated Skill-Gap Identification"]
    end

    subgraph PHASE7 ["Phase 7: Grounded Explanations"]
        M7["• Citation Generation (Page & Snippet Link)\n• Grounded Justification Prompts\n• Anti-Hallucination Guardrails"]
    end

    subgraph PHASE8 ["Phase 8: LangGraph & Async Workers"]
        M8["• LangGraph State Machine Graph\n• Redis Queue & Background Workers\n• Non-blocking Batch Resume Processing"]
    end

    subgraph PHASE9 ["Phase 9: Observability & Production"]
        M9["• Langfuse Tracing & Latency Telemetry\n• Retrieval Recall@K & Evals Suite\n• Dockerization & CI/CD Pipeline"]
    end

    PHASE1 ==> PHASE2 ==> PHASE3 ==> PHASE4 ==> PHASE5 ==> PHASE6 ==> PHASE7 ==> PHASE8 ==> PHASE9
```

---

## 🔗 Related Resources
- **Full Architecture Blueprint**: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)
- **Standalone Mermaid Flowchart**: [`docs/project_workflow_and_phases.mmd`](project_workflow_and_phases.mmd)
- **Project Overview & Tech Stack**: [`README.md`](../README.md)
