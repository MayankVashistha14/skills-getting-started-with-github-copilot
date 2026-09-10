import copy
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import app, activities


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_page():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_static_index_page_is_served():
    # Arrange
    page_path = "/static/index.html"

    # Act
    response = client.get(page_path)

    # Assert
    assert response.status_code == 200
    assert "Mergington High School" in response.text


def test_get_activities_returns_activity_details():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activity = response.json()[expected_activity]
    assert {"description", "schedule", "max_participants", "participants"} <= set(activity)


def test_signup_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]
    assert activities[activity_name]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_requires_email():
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422


def test_unregister_participant_removes_email():
    # Arrange
    activities["Chess Club"]["participants"] = [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]

    # Act
    response = client.delete(
        "/activities/Chess Club/participants?email=daniel@mergington.edu"
    )

    # Assert
    assert response.status_code == 200
    assert "daniel@mergington.edu" not in activities["Chess Club"]["participants"]
    assert response.json()["message"] == (
        "Unregistered daniel@mergington.edu from Chess Club"
    )


def test_unregister_participant_rejects_missing_email():
    # Arrange
    activities["Chess Club"]["participants"] = [
        "michael@mergington.edu",
    ]

    # Act
    response = client.delete(
        "/activities/Chess Club/participants?email=daniel@mergington.edu"
    )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_unregister_participant_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
