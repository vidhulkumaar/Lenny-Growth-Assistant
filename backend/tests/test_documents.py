import pytest
import io
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_invalid_file(db):
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", io.BytesIO(b"Hello world"), "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]

def test_list_and_delete_documents(db):
    # Just test that the endpoints are up and returning expected formats
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    invalid_id = str(uuid.uuid4())
    del_response = client.delete(f"/api/v1/documents/{invalid_id}")
    assert del_response.status_code == 404
