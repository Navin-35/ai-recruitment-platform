def test_create_and_get_candidate(client):
    payload = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+1 555-0199",
        "skills": "Python, FastAPI, Postgres, Docker",
        "experience": "5 years at Cloud Systems building APIs",
        "education": "BS Computer Science, Stanford",
    }
    response = client.post("/candidates/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert "id" in data

    candidate_id = data["id"]
    get_res = client.get(f"/candidates/{candidate_id}")
    assert get_res.status_code == 200
    candidate_detail = get_res.json()
    assert candidate_detail["id"] == candidate_id
    assert candidate_detail["resumes"] == []


def test_list_candidates_and_search(client):
    client.post("/candidates/", json={
        "name": "Alice Smith",
        "email": "alice@example.com",
        "skills": "React, TypeScript, CSS",
    })
    client.post("/candidates/", json={
        "name": "Bob Jones",
        "email": "bob@example.com",
        "skills": "Python, Go, Kubernetes",
    })

    # List all
    res = client.get("/candidates/")
    assert res.status_code == 200
    assert len(res.json()) == 2

    # Search by skill
    res_search = client.get("/candidates/?search=Kubernetes")
    assert res_search.status_code == 200
    results = res_search.json()
    assert len(results) == 1
    assert results[0]["name"] == "Bob Jones"


def test_update_and_delete_candidate(client):
    res = client.post("/candidates/", json={
        "name": "Charlie Brown",
        "email": "charlie@example.com",
    })
    candidate_id = res.json()["id"]

    # Update candidate
    update_res = client.put(f"/candidates/{candidate_id}", json={
        "phone": "+1 555-9999",
        "skills": "Rust, C++",
    })
    assert update_res.status_code == 200
    assert update_res.json()["skills"] == "Rust, C++"
    assert update_res.json()["phone"] == "+1 555-9999"

    # Delete candidate
    del_res = client.delete(f"/candidates/{candidate_id}")
    assert del_res.status_code == 204

    # 404 after deletion
    get_res = client.get(f"/candidates/{candidate_id}")
    assert get_res.status_code == 404


def test_candidate_not_found(client):
    assert client.get("/candidates/9999").status_code == 404
    assert client.put("/candidates/9999", json={"name": "None"}).status_code == 404
    assert client.delete("/candidates/9999").status_code == 404
