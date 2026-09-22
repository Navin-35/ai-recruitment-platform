def test_create_and_get_job(client):
    payload = {
        "title": "Senior AI Engineer",
        "company_name": "Apex AI",
        "description": "Develop high-throughput RAG systems with Gemini and FastAPI.",
        "location": "San Francisco, CA",
    }
    response = client.post("/jobs/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["company_name"] == payload["company_name"]
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data

    job_id = data["id"]
    get_res = client.get(f"/jobs/{job_id}")
    assert get_res.status_code == 200
    job_detail = get_res.json()
    assert job_detail["id"] == job_id
    assert job_detail["requirements"] == []


def test_list_jobs_and_filter(client):
    client.post("/jobs/", json={
        "title": "Backend Developer",
        "company_name": "Tech Corp",
        "description": "Python, FastAPI",
    })
    client.post("/jobs/", json={
        "title": "Frontend Engineer",
        "company_name": "Web Co",
        "description": "React, TypeScript",
    })

    # List all
    res = client.get("/jobs/")
    assert res.status_code == 200
    assert len(res.json()) == 2

    # Search query
    res_search = client.get("/jobs/?search=Frontend")
    assert res_search.status_code == 200
    results = res_search.json()
    assert len(results) == 1
    assert results[0]["title"] == "Frontend Engineer"


def test_update_and_delete_job(client):
    res = client.post("/jobs/", json={
        "title": "ML Engineer",
        "company_name": "OpenSource Lab",
        "description": "PyTorch, LangChain",
    })
    job_id = res.json()["id"]

    # Update job
    update_res = client.put(f"/jobs/{job_id}", json={
        "title": "Lead ML Engineer",
        "status": "closed",
    })
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["title"] == "Lead ML Engineer"
    assert updated_data["status"] == "closed"

    # Delete job
    del_res = client.delete(f"/jobs/{job_id}")
    assert del_res.status_code == 204

    # 404 after deletion
    get_res = client.get(f"/jobs/{job_id}")
    assert get_res.status_code == 404


def test_job_not_found(client):
    assert client.get("/jobs/9999").status_code == 404
    assert client.put("/jobs/9999", json={"title": "None"}).status_code == 404
    assert client.delete("/jobs/9999").status_code == 404
