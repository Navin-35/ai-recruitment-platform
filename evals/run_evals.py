import json
import os
import sys
from pathlib import Path

# Add backend directory to sys.path so app imports resolve
backend_path = Path(__file__).resolve().parent.parent / "backend"
root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(root_path))

from app.ai.skill_normalizer import skill_normalizer
from evals.metrics import f1_score, mean_reciprocal_rank, ndcg_at_k, precision_at_k, recall_at_k


def run_evaluation_suite():
    dataset_file = Path(__file__).parent / "expected_matches.json"
    with open(dataset_file, "r") as f:
        data = json.load(f)

    print("=" * 60)
    print("AI Recruitment Platform - Benchmark & Evaluation Suite")
    print("=" * 60)

    total_precision = []
    total_recall = []
    total_mrr = []
    total_ndcg = []
    total_f1 = []

    for test_case in data.get("test_cases", []):
        job_title = test_case["job_title"]
        print(f"\nEvaluating Role: {job_title}")
        print(f"Requirements: {', '.join(test_case['required_skills'])}")

        for cand in test_case["candidate_evaluations"]:
            name = cand["candidate_name"]
            expected_matched = set(cand["expected_matched_skills"])
            ground_truth_rel = cand["relevance_ground_truth"]

            # Skill normalization & retrieval evaluation
            retrieved_skills = []
            for req in test_case["required_skills"]:
                norm = skill_normalizer.normalize(req)
                if any(skill_normalizer.match_skills(req, m) for m in cand["expected_matched_skills"]):
                    retrieved_skills.append(norm["canonical"])

            p_at_k = precision_at_k(retrieved_skills, expected_matched, k=len(test_case["required_skills"]))
            r_at_k = recall_at_k(retrieved_skills, expected_matched, k=len(test_case["required_skills"]))
            mrr = mean_reciprocal_rank(retrieved_skills, expected_matched)
            ndcg = ndcg_at_k(retrieved_skills, ground_truth_rel, k=len(retrieved_skills) or 1)
            f1 = f1_score(p_at_k, r_at_k)

            total_precision.append(p_at_k)
            total_recall.append(r_at_k)
            total_mrr.append(mrr)
            total_ndcg.append(ndcg)
            total_f1.append(f1)

            print(f"  Candidate: {name}")
            print(f"    Precision@K: {p_at_k:.3f} | Recall@K: {r_at_k:.3f} | F1: {f1:.3f}")
            print(f"    MRR: {mrr:.3f} | NDCG@K: {ndcg:.3f}")

    print("\n" + "=" * 60)
    print("Aggregated Benchmark Results:")
    avg_p = sum(total_precision) / len(total_precision) if total_precision else 0
    avg_r = sum(total_recall) / len(total_recall) if total_recall else 0
    avg_f1 = sum(total_f1) / len(total_f1) if total_f1 else 0
    avg_mrr = sum(total_mrr) / len(total_mrr) if total_mrr else 0
    avg_ndcg = sum(total_ndcg) / len(total_ndcg) if total_ndcg else 0

    print(f"  Mean Precision@K: {avg_p:.3f}")
    print(f"  Mean Recall@K:    {avg_r:.3f}")
    print(f"  Mean F1-Score:    {avg_f1:.3f}")
    print(f"  Mean MRR:         {avg_mrr:.3f}")
    print(f"  Mean NDCG@K:      {avg_ndcg:.3f}")
    print("=" * 60)


if __name__ == "__main__":
    run_evaluation_suite()
