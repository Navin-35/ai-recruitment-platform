import io


def test_api_extract_job_requirements(client):
    job_res = client.post(
        "/jobs/",
        json={
            "title": "Backend Architect",
            "company_name": "CloudScale",
            "description": "We need an experienced Python and FastAPI architect with PostgreSQL and Docker skills.",
            "location": "Remote",
        },
    )
    assert job_res.status_code == 201
    job_id = job_res.json()["id"]

    # Trigger AI requirements extraction
    ext_res = client.post(f"/jobs/{job_id}/extract-requirements")
    assert ext_res.status_code == 200
    ext_data = ext_res.json()
    assert len(ext_data["requirements"]) >= 1
    req_names = [r["skill_name"] for r in ext_data["requirements"]]
    assert any("Python" in r or "FastAPI" in r for r in req_names)


def test_api_process_resume(client):
    # Create candidate
    c_res = client.post("/candidates/", json={"name": "Devin Coder"})
    cand_id = c_res.json()["id"]

    # Upload resume
    content = b"Devin Coder\nEmail: devin@example.com\nSkills: Python, FastAPI, Docker\nExperience: Built microservices at Apex Corp for 2 years."
    files = {"file": ("devin_resume.pdf", io.BytesIO(content), "application/pdf")}
    res = client.post("/resumes/", data={"candidate_id": cand_id}, files=files)
    assert res.status_code == 201
    resume_id = res.json()["id"]

    # Trigger processing
    proc_res = client.post(f"/resumes/{resume_id}/process")
    assert proc_res.status_code == 200
    assert proc_res.json()["processing_status"] == "completed"

    # Verify candidate profile was populated
    cand_check = client.get(f"/candidates/{cand_id}")
    assert cand_check.status_code == 200
    assert "Python" in cand_check.json()["skills"]


def test_api_matching_and_ranking_flow(client):
    # 1. Create Job
    job_res = client.post(
        "/jobs/",
        json={
            "title": "Full Stack Engineer",
            "company_name": "Innovate Inc",
            "description": "Seeking Full Stack Engineer with Python, React, and PostgreSQL.",
        },
    )
    job_id = job_res.json()["id"]
    client.post(f"/jobs/{job_id}/extract-requirements")

    # 2. Create Candidate
    cand_res = client.post(
        "/candidates/",
        json={
            "name": "Sarah Connor",
            "skills": "Python, React, PostgreSQL",
            "experience": "3 years building web apps with Python, React, and PostgreSQL.",
            "education": "B.S. Computer Science",
        },
    )
    cand_id = cand_res.json()["id"]

    # 3. Single match endpoint
    match_res = client.post(f"/matches/job/{job_id}/candidate/{cand_id}")
    assert match_res.status_code == 200
    match_data = match_res.json()
    assert match_data["final_score"] > 0
    assert "score_breakdown" in match_data
    assert "skill_gaps" in match_data
    assert "grounded_explanation" in match_data

    # 4. Run-all ranking endpoint
    run_all_res = client.post(f"/matches/job/{job_id}/run-all")
    assert run_all_res.status_code == 200
    assert run_all_res.json()["total_candidates_evaluated"] >= 1

    # 5. Get ranking leaderboard
    rank_res = client.get(f"/matches/job/{job_id}/ranking")
    assert rank_res.status_code == 200
    rank_data = rank_res.json()
    assert rank_data["candidate_count"] >= 1
    assert rank_data["leaderboard"][0]["candidate_id"] == cand_id
    assert rank_data["leaderboard"][0]["rank"] == 1

    # 6. Detailed candidate report
    rep_res = client.get(f"/matches/job/{job_id}/candidate/{cand_id}/report")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert "grounded_explanation" in rep_data
    assert rep_data["grounded_explanation"]["summary"] is not None
