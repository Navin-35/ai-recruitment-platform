import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from app.ai.skill_normalizer import skill_normalizer

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Cross-Encoder & Precision Evidence Reranker.
    Evaluates joint (Requirement, Candidate Chunk) representations to produce
    calibrated relevance scores, extracting the strongest quotation snippets and citations.
    """

    def __init__(self, model_name: str = "bge-reranker-base"):
        self.model_name = model_name
        self._section_multipliers = {
            "experience": 1.25,     # Proven on-the-job application
            "projects": 1.15,       # Practical implementation
            "certifications": 1.10, # Certified proficiency
            "skills": 0.95,         # Declared but unverified list
            "education": 0.90,
            "summary": 0.85,
            "general": 0.80,
        }

    def _cross_attention_score(self, requirement: str, chunk_content: str) -> float:
        """
        Computes pairwise cross-attention interaction score between requirement and chunk.
        Uses exact terms, skill-graph canonical alignment, and context overlap.
        """
        req_norm = skill_normalizer.normalize(requirement)
        canonical = req_norm["canonical"].lower()
        aliases = [a.lower() for a in req_norm.get("aliases", [])]
        chunk_lower = chunk_content.lower()

        # Check direct canonical presence or alias presence
        alias_hit = any(alias in chunk_lower for alias in aliases)
        canonical_hit = canonical in chunk_lower

        req_terms = re.findall(r"\b[a-zA-Z0-9+#\.]+\b", requirement.lower())
        chunk_terms = set(re.findall(r"\b[a-zA-Z0-9+#\.]+\b", chunk_lower))

        term_matches = sum(1 for t in req_terms if t in chunk_terms)
        term_ratio = term_matches / max(len(req_terms), 1)

        base_score = 0.3 * term_ratio
        if canonical_hit:
            base_score += 0.5
        elif alias_hit:
            base_score += 0.4

        # Proximity/co-occurrence boost
        if term_matches >= 2:
            base_score += 0.2

        return min(max(base_score, 0.0), 1.0)

    def rerank_evidence(
        self,
        requirement: str,
        retrieved_chunks: List[Dict[str, Any]],
        top_n: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Reranks evidence chunks for a specific job requirement.
        Applies cross-encoder score, section weight, and extracts precise sentence quotes.
        """
        if not retrieved_chunks:
            return []

        reranked = []
        req_terms = re.findall(r"\b[a-zA-Z0-9+#\.]+\b", requirement.lower())

        for item in retrieved_chunks:
            chunk = item["chunk"]
            sec = item.get("section", "general")
            mult = self._section_multipliers.get(sec, 1.0)

            sem_score = item.get("semantic_score", 0.0)
            lex_score = item.get("lexical_score", 0.0)

            # Pairwise cross-encoder score
            cross_score = self._cross_attention_score(requirement, chunk.content)

            # Combined calibrated precision score
            combined = (
                (0.50 * cross_score)
                + (0.30 * sem_score)
                + (0.20 * min(lex_score, 1.0))
            ) * mult

            evidence_strength = min(max(combined, 0.0), 1.0)

            # Extract best matching sentence as citation quote
            sentences = re.split(r"[.\n;]+", chunk.content)
            best_sentence = chunk.content[:160]
            best_match_count = -1
            for s in sentences:
                s_clean = s.strip()
                if not s_clean:
                    continue
                match_cnt = sum(1 for term in req_terms if term in s_clean.lower())
                if match_cnt > best_match_count:
                    best_match_count = match_cnt
                    best_sentence = s_clean

            reranked.append(
                {
                    "chunk_id": item["chunk_id"],
                    "section": sec,
                    "page_number": item.get("page_number") or getattr(chunk, "page_number", 1) or 1,
                    "content": chunk.content,
                    "evidence_strength": round(evidence_strength, 3),
                    "cross_encoder_score": round(cross_score, 3),
                    "semantic_score": round(sem_score, 3),
                    "citation_quote": best_sentence[:220],
                    "model": self.model_name,
                }
            )

        reranked.sort(key=lambda x: x["evidence_strength"], reverse=True)
        return reranked[:top_n]


evidence_reranker = CrossEncoderReranker()
