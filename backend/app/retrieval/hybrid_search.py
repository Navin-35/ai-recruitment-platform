import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.ai.embedding_client import embedding_client
from app.models.chunk import DocumentChunk

logger = logging.getLogger(__name__)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity between two float vectors."""
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def tokenize(text: str) -> List[str]:
    """Tokenizes text into lowercase alphanumeric words."""
    return re.findall(r"\b[a-zA-Z0-9+#\.]+\b", text.lower())


class HybridRetrievalEngine:
    """
    Enterprise Hybrid Search Engine combining:
    1. Dense Vector Retrieval (PostgreSQL pgvector ANN <=> distance or local cosine)
    2. Full-Text Lexical Search (PostgreSQL FTS ts_rank or token-overlap BM25)
    3. Reciprocal Rank Fusion (RRF) with degraded mode observability.
    """

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    def _is_postgresql(self, db: Session) -> bool:
        """Detects if the database dialect is PostgreSQL."""
        try:
            return bool(db.bind and db.bind.dialect.name == "postgresql")
        except Exception:
            return False

    def retrieve_evidence(
        self,
        query: str,
        db: Session,
        candidate_id: Optional[int] = None,
        job_id: Optional[int] = None,
        document_type: Optional[str] = "resume",
        section: Optional[str] = None,
        top_k: int = 5,
        expanded_keywords: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval over DocumentChunks in the database:
        - When on PostgreSQL: generates real pgvector `<=>` ANN + FTS ts_rank queries
        - When on SQLite/test runner: uses vectorized cosine + token frequency with RRF
        - Accurately tracks degraded mode if embeddings are offline.
        """
        is_pg = self._is_postgresql(db)
        embedding_online = embedding_client.is_available()

        # If PostgreSQL is active, perform native database hybrid retrieval
        if is_pg:
            try:
                return self._retrieve_postgresql(
                    query=query,
                    db=db,
                    candidate_id=candidate_id,
                    job_id=job_id,
                    document_type=document_type,
                    section=section,
                    top_k=top_k,
                    expanded_keywords=expanded_keywords,
                    embedding_online=embedding_online,
                )
            except Exception as e:
                logger.warning(f"PostgreSQL native hybrid search failed, falling back: {e}")

        # Python / SQLite hybrid fallback
        return self._retrieve_sqlite_fallback(
            query=query,
            db=db,
            candidate_id=candidate_id,
            job_id=job_id,
            document_type=document_type,
            section=section,
            top_k=top_k,
            expanded_keywords=expanded_keywords,
            embedding_online=embedding_online,
        )

    def _retrieve_postgresql(
        self,
        query: str,
        db: Session,
        candidate_id: Optional[int],
        job_id: Optional[int],
        document_type: Optional[str],
        section: Optional[str],
        top_k: int,
        expanded_keywords: Optional[List[str]],
        embedding_online: bool,
    ) -> List[Dict[str, Any]]:
        """Native PostgreSQL pgvector ANN + FTS tsvector search with RRF."""
        where_clauses = ["1=1"]
        params: Dict[str, Any] = {"query": query, "top_k": top_k * 3}

        if document_type:
            where_clauses.append("document_type = :doc_type")
            params["doc_type"] = document_type
        if candidate_id is not None:
            where_clauses.append("candidate_id = :candidate_id")
            params["candidate_id"] = candidate_id
        if job_id is not None:
            where_clauses.append("job_id = :job_id")
            params["job_id"] = job_id
        if section:
            where_clauses.append("section = :section")
            params["section"] = section

        filter_sql = " AND ".join(where_clauses)

        # 1. PostgreSQL Full Text Search (FTS)
        fts_sql = f"""
            SELECT id, section, page_number, content,
                   ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) as lexical_score
            FROM document_chunks
            WHERE {filter_sql} AND to_tsvector('english', content) @@ plainto_tsquery('english', :query)
            ORDER BY lexical_score DESC
            LIMIT :top_k
        """
        fts_rows = db.execute(sql_text(fts_sql), params).fetchall()

        # 2. pgvector ANN distance search (if embedding available)
        vec_rows = []
        if embedding_online:
            query_vec = embedding_client.embed_text(query)
            params["query_vec"] = str(query_vec)
            vec_sql = f"""
                SELECT id, section, page_number, content,
                       (embedding <=> (:query_vec)::vector) as distance
                FROM document_chunks
                WHERE {filter_sql} AND embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT :top_k
            """
            vec_rows = db.execute(sql_text(vec_sql), params).fetchall()

        # Build chunks and RRF
        fts_ranks = {row.id: idx + 1 for idx, row in enumerate(fts_rows)}
        vec_ranks = {row.id: idx + 1 for idx, row in enumerate(vec_rows)}

        all_ids = set(fts_ranks.keys()).union(vec_ranks.keys())
        if not all_ids:
            return self._retrieve_sqlite_fallback(
                query, db, candidate_id, job_id, document_type, section, top_k, expanded_keywords, embedding_online
            )

        fused = []
        chunks_map = {c.id: c for c in db.query(DocumentChunk).filter(DocumentChunk.id.in_(all_ids)).all()}

        for cid in all_ids:
            chunk = chunks_map.get(cid)
            if not chunk:
                continue
            r_vec = vec_ranks.get(cid, 999)
            r_fts = fts_ranks.get(cid, 999)
            rrf = (1.0 / (self.rrf_k + r_vec)) + (1.0 / (self.rrf_k + r_fts))
            fused.append({
                "chunk": chunk,
                "chunk_id": chunk.id,
                "section": chunk.section,
                "page_number": chunk.page_number,
                "content": chunk.content,
                "semantic_score": round(1.0 / (1.0 + r_vec), 4) if r_vec != 999 else 0.0,
                "lexical_score": round(1.0 / (1.0 + r_fts), 4) if r_fts != 999 else 0.0,
                "rrf_score": round(rrf, 5),
                "retrieval_mode": "pgvector_fts_rrf" if embedding_online else "lexical_fallback",
            })

        fused.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused[:top_k]

    def _retrieve_sqlite_fallback(
        self,
        query: str,
        db: Session,
        candidate_id: Optional[int],
        job_id: Optional[int],
        document_type: Optional[str],
        section: Optional[str],
        top_k: int,
        expanded_keywords: Optional[List[str]],
        embedding_online: bool,
    ) -> List[Dict[str, Any]]:
        """Fallback in-memory hybrid retrieval engine for SQLite development."""
        db_query = db.query(DocumentChunk)
        if document_type:
            db_query = db_query.filter(DocumentChunk.document_type == document_type)
        if candidate_id is not None:
            db_query = db_query.filter(DocumentChunk.candidate_id == candidate_id)
        if job_id is not None:
            db_query = db_query.filter(DocumentChunk.job_id == job_id)
        if section:
            db_query = db_query.filter(DocumentChunk.section == section)

        candidate_chunks = db_query.all()
        if not candidate_chunks:
            return []

        # 1. Semantic Retrieval
        semantic_scores: List[Tuple[DocumentChunk, float]] = []
        if embedding_online:
            query_vector = embedding_client.embed_text(query)
            for chunk in candidate_chunks:
                chunk_vec = chunk.embedding
                if chunk_vec and len(chunk_vec) == len(query_vector):
                    sim = cosine_similarity(query_vector, chunk_vec)
                else:
                    sim = 0.0
                semantic_scores.append((chunk, sim))
        else:
            # Degraded mode: no fake semantic scores
            for chunk in candidate_chunks:
                semantic_scores.append((chunk, 0.0))

        semantic_scores.sort(key=lambda x: x[1], reverse=True)

        # 2. Lexical Keyword Retrieval
        query_tokens = set(tokenize(query))
        if expanded_keywords:
            for kw in expanded_keywords:
                query_tokens.update(tokenize(kw))

        lexical_scores: List[Tuple[DocumentChunk, float]] = []
        for chunk in candidate_chunks:
            chunk_tokens = tokenize(chunk.content)
            if not chunk_tokens or not query_tokens:
                lexical_scores.append((chunk, 0.0))
                continue

            match_count = sum(1 for t in chunk_tokens if t in query_tokens)
            score = match_count / math.sqrt(len(chunk_tokens) + 1)
            lexical_scores.append((chunk, score))

        lexical_scores.sort(key=lambda x: x[1], reverse=True)

        # 3. Reciprocal Rank Fusion
        chunk_ranks_semantic = {chunk.id: rank + 1 for rank, (chunk, _) in enumerate(semantic_scores)}
        chunk_ranks_lexical = {chunk.id: rank + 1 for rank, (chunk, _) in enumerate(lexical_scores)}
        chunk_sim_map = {chunk.id: sim for chunk, sim in semantic_scores}
        chunk_lex_map = {chunk.id: score for chunk, score in lexical_scores}

        fused_scores: List[Dict[str, Any]] = []
        for chunk in candidate_chunks:
            rank_sem = chunk_ranks_semantic.get(chunk.id, 999) if embedding_online else 999
            rank_lex = chunk_ranks_lexical.get(chunk.id, 999)

            if embedding_online:
                rrf_score = (1.0 / (self.rrf_k + rank_sem)) + (1.0 / (self.rrf_k + rank_lex))
            else:
                # In degraded mode, RRF prioritizes lexical ranking
                rrf_score = 1.0 / (self.rrf_k + rank_lex)

            fused_scores.append(
                {
                    "chunk": chunk,
                    "chunk_id": chunk.id,
                    "section": chunk.section,
                    "page_number": chunk.page_number,
                    "content": chunk.content,
                    "semantic_score": chunk_sim_map.get(chunk.id, 0.0),
                    "lexical_score": chunk_lex_map.get(chunk.id, 0.0),
                    "rrf_score": rrf_score,
                    "retrieval_mode": "hybrid_semantic" if embedding_online else "lexical_fallback",
                }
            )

        fused_scores.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused_scores[:top_k]


hybrid_retrieval_engine = HybridRetrievalEngine()
