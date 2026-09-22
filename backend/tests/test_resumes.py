import io
from pathlib import Path


def test_upload_resume_pdf(client):
    # 1. Create a candidate
    c_res = client.post("/candidates/", json={"name": "Alex Resume Tester"})
    candidate_id = c_res.json()["id"]

    # 2. Upload dummy PDF
    pdf_content = b"%PDF-1.5 fake resume document content"
    files = {
        "file": ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")
    }
    data = {"candidate_id": candidate_id}

    response = client.post("/resumes/", data=data, files=files)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["filename"] == "resume.pdf"
    assert res_data["file_type"] == "pdf"
    assert res_data["processing_status"] == "pending"
    assert res_data["candidate_id"] == candidate_id

    resume_id = res_data["id"]
    file_path = res_data["file_path"]
    assert Path(file_path).exists()

    # 3. Retrieve single resume
    get_res = client.get(f"/resumes/{resume_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == resume_id

    # 4. Retrieve resumes by candidate
    by_c_res = client.get(f"/resumes/candidate/{candidate_id}")
    assert by_c_res.status_code == 200
    assert len(by_c_res.json()) == 1

    # 5. Delete resume
    del_res = client.delete(f"/resumes/{resume_id}")
    assert del_res.status_code == 204
    assert not Path(file_path).exists()


def test_upload_resume_docx(client):
    c_res = client.post("/candidates/", json={"name": "Docx Candidate"})
    candidate_id = c_res.json()["id"]

    docx_content = b"PK\x03\x04 fake docx binary data"
    files = {
        "file": ("cv.docx", io.BytesIO(docx_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }
    data = {"candidate_id": candidate_id}

    response = client.post("/resumes/", data=data, files=files)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["file_type"] == "docx"

    # Clean up file
    client.delete(f"/resumes/{res_data['id']}")


def test_upload_resume_invalid_format(client):
    c_res = client.post("/candidates/", json={"name": "Format Tester"})
    candidate_id = c_res.json()["id"]

    files = {
        "file": ("notes.txt", io.BytesIO(b"Just plain text"), "text/plain")
    }
    data = {"candidate_id": candidate_id}

    response = client.post("/resumes/", data=data, files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_resume_empty_file(client):
    c_res = client.post("/candidates/", json={"name": "Empty File Tester"})
    candidate_id = c_res.json()["id"]

    files = {
        "file": ("empty.pdf", io.BytesIO(b""), "application/pdf")
    }
    data = {"candidate_id": candidate_id}

    response = client.post("/resumes/", data=data, files=files)
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["detail"]


def test_upload_resume_nonexistent_candidate(client):
    files = {
        "file": ("resume.pdf", io.BytesIO(b"dummy data"), "application/pdf")
    }
    data = {"candidate_id": 9999}
    response = client.post("/resumes/", data=data, files=files)
    assert response.status_code == 404
