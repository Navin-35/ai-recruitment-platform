def test_skills_crud(client):
    # 1. Create skill
    res = client.post("/skills/", json={
        "name": "Python",
        "category": "Backend",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Python"
    assert data["category"] == "Backend"
    skill_id = data["id"]

    # 2. Duplicate skill creation returns 400
    dup_res = client.post("/skills/", json={
        "name": "python",
        "category": "Programming Language",
    })
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Create second skill
    client.post("/skills/", json={
        "name": "Docker",
        "category": "DevOps",
    })

    # 4. List and filter
    list_res = client.get("/skills/?category=Backend")
    assert list_res.status_code == 200
    skills = list_res.json()
    assert len(skills) == 1
    assert skills[0]["name"] == "Python"

    # Search
    search_res = client.get("/skills/?search=dock")
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1

    # 5. Update skill
    up_res = client.put(f"/skills/{skill_id}", json={"category": "Core Engineering"})
    assert up_res.status_code == 200
    assert up_res.json()["category"] == "Core Engineering"

    # 6. Delete skill
    del_res = client.delete(f"/skills/{skill_id}")
    assert del_res.status_code == 204
    assert client.get(f"/skills/{skill_id}").status_code == 404


def test_job_requirements_crud_and_cascade(client):
    # 1. Create job
    j_res = client.post("/jobs/", json={
        "title": "Full Stack Lead",
        "description": "TypeScript and Python lead",
    })
    job_id = j_res.json()["id"]

    # 2. Add requirements
    req1_res = client.post(f"/jobs/{job_id}/requirements/", json={
        "skill_name": "FastAPI",
        "is_required": True,
        "importance": "high",
    })
    assert req1_res.status_code == 201
    req1_id = req1_res.json()["id"]

    req2_res = client.post(f"/jobs/{job_id}/requirements/", json={
        "skill_name": "React",
        "is_required": False,
        "importance": "medium",
    })
    assert req2_res.status_code == 201

    # 3. List requirements for job
    reqs_res = client.get(f"/jobs/{job_id}/requirements/")
    assert reqs_res.status_code == 200
    assert len(reqs_res.json()) == 2

    # 4. Also verify requirements show up in JobDetailResponse
    job_res = client.get(f"/jobs/{job_id}")
    assert job_res.status_code == 200
    assert len(job_res.json()["requirements"]) == 2

    # 5. Update requirement
    up_req = client.put(f"/jobs/{job_id}/requirements/{req1_id}", json={
        "importance": "critical",
    })
    assert up_req.status_code == 200
    assert up_req.json()["importance"] == "critical"

    # 6. Delete requirement
    del_req = client.delete(f"/jobs/{job_id}/requirements/{req1_id}")
    assert del_req.status_code == 204

    reqs_after = client.get(f"/jobs/{job_id}/requirements/")
    assert len(reqs_after.json()) == 1

    # 7. Verify cascade deletion on job delete
    del_job = client.delete(f"/jobs/{job_id}")
    assert del_job.status_code == 204
    # Trying to get requirements for deleted job returns 404
    assert client.get(f"/jobs/{job_id}/requirements/").status_code == 404
