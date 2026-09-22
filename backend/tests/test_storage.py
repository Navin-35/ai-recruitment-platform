import io
from app.services.storage import StorageService, storage_service


def test_storage_service_upload_download_delete():
    service = StorageService()
    test_content = b"Candidate Resume PDF Binary Mock Content"
    filename = "test_resume_unique.pdf"

    # 1. Upload
    path = service.upload_file(
        bucket="resumes",
        destination_path=filename,
        file_bytes=test_content,
        content_type="application/pdf",
    )
    assert path is not None

    # 2. Signed URL
    signed_url = service.get_signed_url(bucket="resumes", file_path=filename)
    assert "resumes" in signed_url
    assert filename in signed_url

    # 3. Download
    downloaded = service.download_file(bucket="resumes", file_path=filename)
    assert downloaded == test_content

    # 4. Delete
    deleted = service.delete_file(bucket="resumes", file_path=filename)
    assert deleted is True


def test_resume_signed_url_endpoint(client):
    # Create candidate
    c_res = client.post("/candidates/", json={"name": "Signed URL Candidate"})
    candidate_id = c_res.json()["id"]

    # Upload resume
    pdf_content = b"%PDF-1.4 Mock Candidate Resume"
    files = {
        "file": ("signed_test.pdf", io.BytesIO(pdf_content), "application/pdf")
    }
    upload_res = client.post("/resumes/", data={"candidate_id": candidate_id}, files=files)
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["id"]

    # Request signed URL
    signed_res = client.get(f"/resumes/{resume_id}/signed-url?expires_in=1800")
    assert signed_res.status_code == 200
    signed_data = signed_res.json()
    assert signed_data["resume_id"] == resume_id
    assert signed_data["expires_in_seconds"] == 1800
    assert "signed_url" in signed_data
    assert len(signed_data["signed_url"]) > 0

    # 404 for non-existent resume
    assert client.get("/resumes/99999/signed-url").status_code == 404
