import math
from app.models.candidate import Candidate
from app.models.chunk import DocumentChunk
from app.models.job import Job


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def test_document_chunk_persistence_and_vector(db_session):
    # 1. Create candidate
    candidate = Candidate(name="Vector Test Candidate", email="vector@example.com")
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)

    # 2. Mock 768-dimensional embedding vector (Gemini text-embedding-004 format)
    vector_768 = [0.05] * 768

    chunk = DocumentChunk(
        document_type="resume",
        document_id=101,
        candidate_id=candidate.id,
        section="experience",
        page_number=2,
        content="Led migration from legacy monolith to FastAPI microservices on AWS.",
        content_hash="hash-abc-123",
        embedding=vector_768,
    )
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(chunk)

    assert chunk.id is not None
    assert chunk.candidate_id == candidate.id
    assert chunk.page_number == 2
    assert chunk.section == "experience"
    assert len(chunk.embedding) == 768
    assert chunk.embedding[0] == 0.05

    # 3. Retrieve chunks by candidate and section
    retrieved = (
        db_session.query(DocumentChunk)
        .filter(
            DocumentChunk.candidate_id == candidate.id,
            DocumentChunk.section == "experience",
        )
        .first()
    )
    assert retrieved is not None
    assert "FastAPI" in retrieved.content


def test_vector_cosine_similarity():
    # Verify cosine distance calculation matches expectations
    vec_a = [1.0 if i % 2 == 0 else 0.0 for i in range(768)]
    vec_b = [1.0 if i % 2 == 0 else 0.0 for i in range(768)]
    vec_orthogonal = [0.0 if i % 2 == 0 else 1.0 for i in range(768)]

    # Identical vectors -> similarity 1.0
    assert abs(cosine_similarity(vec_a, vec_b) - 1.0) < 1e-6
    # Orthogonal vectors -> similarity 0.0
    assert abs(cosine_similarity(vec_a, vec_orthogonal) - 0.0) < 1e-6


def test_chunk_cascade_deletion(db_session):
    job = Job(title="DevOps Engineer", description="Kubernetes and Terraform")
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    chunk = DocumentChunk(
        document_type="job_description",
        document_id=1,
        job_id=job.id,
        section="requirements",
        content="Must have 3+ years experience with Kubernetes.",
        embedding=[0.01] * 768,
    )
    db_session.add(chunk)
    db_session.commit()

    # Verify chunk exists
    assert db_session.query(DocumentChunk).filter(DocumentChunk.job_id == job.id).count() == 1

    # Delete parent job
    db_session.delete(job)
    db_session.commit()

    # Cascade deletes chunk
    assert db_session.query(DocumentChunk).filter(DocumentChunk.job_id == job.id).count() == 0
