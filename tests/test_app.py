import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_participants():
    original_participants = {
        activity_name: activity["participants"][:]
        for activity_name, activity in activities.items()
    }
    yield
    for activity_name, participants in original_participants.items():
        activities[activity_name]["participants"][:] = participants


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
    assert "new.student@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_returns_404_for_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}