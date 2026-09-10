import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import app, activities


client = TestClient(app)


def test_unregister_participant_removes_email():
    activities["Chess Club"]["participants"] = [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]

    response = client.delete(
        "/activities/Chess Club/participants?email=daniel@mergington.edu"
    )

    assert response.status_code == 200
    assert "daniel@mergington.edu" not in activities["Chess Club"]["participants"]
    assert response.json()["message"] == (
        "Unregistered daniel@mergington.edu from Chess Club"
    )


def test_unregister_participant_rejects_missing_email():
    activities["Chess Club"]["participants"] = [
        "michael@mergington.edu",
    ]

    response = client.delete(
        "/activities/Chess Club/participants?email=daniel@mergington.edu"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
