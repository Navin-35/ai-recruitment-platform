import math
from typing import List, Set


def precision_at_k(retrieved: List[str], ground_truth: Set[str], k: int) -> float:
    """Computes Precision@K."""
    if k <= 0 or not retrieved:
        return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for item in top_k if item in ground_truth)
    return hits / k


def recall_at_k(retrieved: List[str], ground_truth: Set[str], k: int) -> float:
    """Computes Recall@K."""
    if not ground_truth:
        return 1.0
    top_k = retrieved[:k]
    hits = sum(1 for item in top_k if item in ground_truth)
    return hits / len(ground_truth)


def mean_reciprocal_rank(retrieved: List[str], relevant_items: Set[str]) -> float:
    """Computes MRR (Mean Reciprocal Rank)."""
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant_items:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: List[str], relevance_scores: dict[str, float], k: int) -> float:
    """Computes Normalized Discounted Cumulative Gain (NDCG@K)."""
    top_k = retrieved[:k]
    dcg = 0.0
    for i, item in enumerate(top_k):
        rel = relevance_scores.get(item, 0.0)
        dcg += (2**rel - 1) / math.log2(i + 2)

    # Ideal DCG
    ideal_scores = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = sum((2**rel - 1) / math.log2(i + 2) for i, rel in enumerate(ideal_scores))
    if idcg == 0:
        return 0.0
    return dcg / idcg


def f1_score(precision: float, recall: float) -> float:
    """Computes F1-score harmonic mean."""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)
