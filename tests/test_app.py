import pytest
from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_app_state(tmp_path, monkeypatch):
    original_participants = {
        activity_name: activity["participants"][:]
        for activity_name, activity in app_module.activities.items()
    }
    monkeypatch.setattr(app_module, "UPLOAD_DIR", tmp_path / "uploads")
    yield
    for activity_name, participants in original_participants.items():
        app_module.activities[activity_name]["participants"][:] = participants


def test_list_activities_returns_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    result = response.json()
    assert "Chess Club" in result
    assert result["Chess Club"]["description"]
    assert result["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_student_to_activity():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new.student@mergington.edu for Chess Club"
    }
    assert "new.student@mergington.edu" in app_module.activities["Chess Club"]["participants"]


def test_signup_returns_404_for_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def upload_sample_file(filename="notes.txt", content=b"hello from upload"):
    return client.post("/files", files={"file": (filename, content, "text/plain")})


def test_upload_file_returns_metadata():
    response = upload_sample_file()

    assert response.status_code == 201
    assert response.json()["filename"] == "notes.txt"
    assert response.json()["size"] == len(b"hello from upload")
    assert response.json()["id"]


def test_list_files_includes_uploaded_file():
    uploaded_file = upload_sample_file().json()

    response = client.get("/files")

    assert response.status_code == 200
    assert response.json() == {"files": [uploaded_file]}


def test_download_file_returns_uploaded_contents():
    uploaded_file = upload_sample_file().json()

    response = client.get(f"/files/{uploaded_file['id']}")

    assert response.status_code == 200
    assert response.content == b"hello from upload"
    assert 'filename="notes.txt"' in response.headers["content-disposition"]


def test_upload_file_reduces_path_to_filename():
    response = upload_sample_file("../../notes.txt")

    assert response.status_code == 201
    assert response.json()["filename"] == "notes.txt"


def test_download_unknown_file_returns_404():
    response = client.get("/files/not-a-uuid")

    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}