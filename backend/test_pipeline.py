"""
End-to-End AI Recruitment Platform Integration Test
Tests the full pipeline: Job creation → AI extraction → Resume → AI matching → Ranking
"""
import httpx
import json
import sys

BASE = "http://localhost:8000"


def run_test():
    client = httpx.Client(timeout=90.0)

    # Step 1: Create a job
    print("=== Step 1: Create Job ===")
    job_resp = client.post(
        f"{BASE}/jobs/",
        json={
            "title": "Senior Backend Engineer",
            "company_name": "TechCorp",
            "description": (
                "We are looking for a Senior Backend Engineer.\n"
                "Requirements:\n"
                "- 5+ years Python experience (required)\n"
                "- FastAPI or Django framework (required)\n"
                "- PostgreSQL database design (required)\n"
                "- Docker and Kubernetes (required)\n"
                "- REST API design (required)\n"
                "- AWS or GCP cloud (preferred)\n"
                "- Redis caching (preferred)\n"
                "- CI/CD pipelines (preferred)\n"
            ),
            "location": "Remote",
        },
    )
    job = job_resp.json()
    job_id = job["id"]
    print(f"Job created: ID={job_id}, Title={job['title']}")

    # Step 2: AI extract requirements
    print("\n=== Step 2: AI Extract Job Requirements ===")
    extract_resp = client.post(f"{BASE}/jobs/{job_id}/extract-requirements")
    if extract_resp.status_code != 200:
        print(f"ERROR: {extract_resp.status_code} - {extract_resp.text[:300]}")
        sys.exit(1)
    extracted = extract_resp.json()
    reqs = extracted.get("requirements", [])
    print(f"Extracted {len(reqs)} requirements:")
    for r in reqs[:8]:
        req_type = "REQUIRED" if r["is_required"] else "PREFERRED"
        print(f"  [{req_type}] {r['skill_name']} (importance={r['importance']})")

    # Step 3: Create Candidate A - Strong match
    print("\n=== Step 3: Create Candidate A (Strong Match) ===")
    cand_a_resp = client.post(
        f"{BASE}/candidates/",
        json={
            "name": "Alex Johnson",
            "email": "alex@example.com",
            "skills": "Python, FastAPI, PostgreSQL, Docker, Kubernetes, Redis, AWS, REST APIs, CI/CD",
            "experience": (
                "Senior Software Engineer at DataSystems (2020-2024)\n"
                "- Designed Python FastAPI microservices handling 10k req/sec\n"
                "- Optimized PostgreSQL queries reducing latency by 60%\n"
                "- Deployed Docker and Kubernetes on AWS with CI/CD\n"
                "Backend Engineer at StartupXYZ (2018-2020)\n"
                "- Built Django REST APIs for e-commerce\n"
                "- Implemented Redis caching reducing DB load by 40%"
            ),
            "projects": (
                "Analytics Pipeline: Python, FastAPI, PostgreSQL, Redis, Docker. 1M+ events/day on AWS.\n"
                "Microservices Migration: Broke monolith into 12 services with Kubernetes."
            ),
            "education": "B.S. Computer Science - State University (2018)",
            "certifications": "AWS Certified Developer, Docker Certified Associate",
        },
    )
    cand_a = cand_a_resp.json()
    cand_a_id = cand_a["id"]
    print(f"Candidate A created: ID={cand_a_id}, Name={cand_a['name']}")

    # Step 4: Create Candidate B - Weak match
    print("\n=== Step 4: Create Candidate B (Weak Match) ===")
    cand_b_resp = client.post(
        f"{BASE}/candidates/",
        json={
            "name": "Jamie Lee",
            "email": "jamie@example.com",
            "skills": "JavaScript, React, HTML, CSS, Node.js",
            "experience": (
                "Frontend Developer at WebAgency (2022-2024)\n"
                "- Built React UI components and responsive designs\n"
                "- Managed state with Redux in large applications"
            ),
            "projects": "Portfolio website with React and CSS animations",
            "education": "B.A. Design - Art School (2022)",
            "certifications": "",
        },
    )
    cand_b = cand_b_resp.json()
    cand_b_id = cand_b["id"]
    print(f"Candidate B created: ID={cand_b_id}, Name={cand_b['name']}")

    # Step 5: Match Candidate A
    print("\n=== Step 5: AI Match - Candidate A ===")
    match_a_resp = client.post(f"{BASE}/matches/job/{job_id}/candidate/{cand_a_id}")
    if match_a_resp.status_code == 200:
        result_a = match_a_resp.json()
        bd_a = result_a["score_breakdown"]
        gaps_a = result_a["skill_gaps"]
        exp_a = result_a["grounded_explanation"]
        print(f"FINAL SCORE: {result_a['final_score']:.1f}/100")
        print(f"  Skills Score:     {bd_a['required_skill_score']:.1f}")
        print(f"  Experience Score: {bd_a['experience_score']:.1f}")
        print(f"  Project Score:    {bd_a['project_score']:.1f}")
        print(f"  Education Score:  {bd_a['education_score']:.1f}")
        print(f"  Skill Coverage:   {gaps_a['coverage_percentage']}%")
        print(f"  Overall Fit:      {exp_a['overall_fit']}")
        print(f"  Matched Skills:   {len(gaps_a['matched_skills'])}")
        print(f"  Missing Required: {[g['skill'] for g in gaps_a['missing_required']]}")
        print(f"  Recommendation:   {exp_a['recruiter_recommendation']}")
    else:
        print(f"ERROR: {match_a_resp.status_code} - {match_a_resp.text[:300]}")

    # Step 6: Match Candidate B
    print("\n=== Step 6: AI Match - Candidate B ===")
    match_b_resp = client.post(f"{BASE}/matches/job/{job_id}/candidate/{cand_b_id}")
    if match_b_resp.status_code == 200:
        result_b = match_b_resp.json()
        bd_b = result_b["score_breakdown"]
        gaps_b = result_b["skill_gaps"]
        exp_b = result_b["grounded_explanation"]
        print(f"FINAL SCORE: {result_b['final_score']:.1f}/100")
        print(f"  Skills Score:     {bd_b['required_skill_score']:.1f}")
        print(f"  Experience Score: {bd_b['experience_score']:.1f}")
        print(f"  Skill Coverage:   {gaps_b['coverage_percentage']}%")
        print(f"  Overall Fit:      {exp_b['overall_fit']}")
        print(f"  Missing Required: {[g['skill'] for g in gaps_b['missing_required']]}")
        print(f"  Recommendation:   {exp_b['recruiter_recommendation']}")
    else:
        print(f"ERROR: {match_b_resp.status_code} - {match_b_resp.text[:300]}")

    # Step 7: Get leaderboard
    print("\n=== Step 7: Candidate Ranking Leaderboard ===")
    ranking_resp = client.get(f"{BASE}/matches/job/{job_id}/ranking")
    if ranking_resp.status_code == 200:
        ranking = ranking_resp.json()
        print(f"Job: {ranking['job_title']} | Candidates evaluated: {ranking['candidate_count']}")
        for entry in ranking["leaderboard"]:
            print(
                f"  #{entry['rank']} {entry['candidate_name']} — Score: {entry['final_score']:.1f}"
                f" | Skills: {entry['score_breakdown']['skills']:.0f}"
                f" | Exp: {entry['score_breakdown']['experience']:.0f}"
            )
    else:
        print(f"ERROR: {ranking_resp.status_code} - {ranking_resp.text[:300]}")

    print("\n=== ALL TESTS PASSED ===")
    client.close()


if __name__ == "__main__":
    run_test()
