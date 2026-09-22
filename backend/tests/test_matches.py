def test_candidate_matches_crud(client):
    # 1. Create a job
    j_res = client.post("/jobs/", json={
        "title": "Data Scientist",
        "description": "Python, Statistics, Machine Learning",
    })
    job_id = j_res.json()["id"]

    # 2. Create two candidates
    c1_res = client.post("/candidates/", json={"name": "Alice ML"})
    cand1_id = c1_res.json()["id"]

    c2_res = client.post("/candidates/", json={"name": "Bob Data"})
    cand2_id = c2_res.json()["id"]

    # 3. Record match for candidate 1
    m1_res = client.post("/matches/", json={
        "job_id": job_id,
        "candidate_id": cand1_id,
        "semantic_score": 92.5,
        "skill_score": 88.0,
        "experience_score": 85.0,
        "project_score": 90.0,
        "education_score": 95.0,
        "final_score": 89.8,
        "matching_skills": "Python, Machine Learning",
        "missing_skills": "Deep Learning",
        "explanation": "Alice ML matches 4/5 key requirements with strong projects.",
    })
    assert m1_res.status_code == 201
    m1_data = m1_res.json()
    assert m1_data["final_score"] == 89.8
    match1_id = m1_data["id"]

    # 4. Record match for candidate 2 (lower score)
    m2_res = client.post("/matches/", json={
        "job_id": job_id,
        "candidate_id": cand2_id,
        "semantic_score": 75.0,
        "skill_score": 70.0,
        "experience_score": 65.0,
        "project_score": 80.0,
        "education_score": 80.0,
        "final_score": 73.5,
        "matching_skills": "Python",
        "missing_skills": "Statistics, Machine Learning",
        "explanation": "Bob Data meets basic Python requirements.",
    })
    assert m2_res.status_code == 201

    # 5. Query ranked matches for job (should return candidate 1 first, then candidate 2)
    ranked_res = client.get(f"/matches/job/{job_id}")
    assert ranked_res.status_code == 200
    matches = ranked_res.json()
    assert len(matches) == 2
    assert matches[0]["candidate_id"] == cand1_id
    assert matches[0]["final_score"] == 89.8
    assert matches[1]["candidate_id"] == cand2_id
    assert matches[1]["final_score"] == 73.5

    # 6. Upsert: Re-submitting for candidate 1 updates score without creating a duplicate
    up_m1 = client.post("/matches/", json={
        "job_id": job_id,
        "candidate_id": cand1_id,
        "semantic_score": 95.0,
        "skill_score": 95.0,
        "experience_score": 90.0,
        "project_score": 90.0,
        "education_score": 95.0,
        "final_score": 93.5,
        "matching_skills": "Python, Machine Learning, Deep Learning",
        "missing_skills": "",
        "explanation": "Alice ML re-evaluated with updated resume.",
    })
    assert up_m1.status_code == 201
    assert up_m1.json()["id"] == match1_id
    assert up_m1.json()["final_score"] == 93.5

    # Verify count is still 2
    matches_after = client.get(f"/matches/job/{job_id}").json()
    assert len(matches_after) == 2

    # 7. Get single match
    single_res = client.get(f"/matches/{match1_id}")
    assert single_res.status_code == 200
    assert single_res.json()["final_score"] == 93.5

    # 8. Delete match
    del_res = client.delete(f"/matches/{match1_id}")
    assert del_res.status_code == 204
    assert client.get(f"/matches/{match1_id}").status_code == 404


def test_matches_invalid_references(client):
    res = client.post("/matches/", json={
        "job_id": 9999,
        "candidate_id": 9999,
        "final_score": 50.0,
    })
    assert res.status_code == 404
