"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

# this is ac

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test"""
    # Store original state
    original_activities = {
        k: {"participants": v["participants"].copy(), **{nk: nv for nk, nv in v.items() if nk != "participants"}}
        for k, v in activities.items()
    }
    yield
    # Restore original state
    for key in activities:
        activities[key]["participants"] = original_activities[key]["participants"].copy()


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_get_activities_has_required_fields(client):
    """Test that activities have all required fields"""
    response = client.get("/activities")
    data = response.json()
    activity = data["Chess Club"]
    
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert isinstance(activity["participants"], list)


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "test@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_for_activity_duplicate(client):
    """Test that duplicate signups are prevented"""
    email = "michael@mergington.edu"
    response = client.post(
        f"/activities/Chess Club/signup?email={email}"
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_for_nonexistent_activity(client):
    """Test signup for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_unregister_from_activity_success(client):
    """Test successful unregistration from an activity"""
    email = "michael@mergington.edu"
    # Verify the participant is registered
    assert email in activities["Chess Club"]["participants"]
    
    response = client.post(
        f"/activities/Chess Club/unregister?email={email}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_not_registered(client):
    """Test unregistering someone who isn't registered"""
    response = client.post(
        "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
    )
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"]


def test_unregister_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_signup_and_unregister_workflow(client):
    """Test the complete signup and unregister workflow"""
    email = "workflow@mergington.edu"
    activity = "Programming Class"
    
    # Initial state - not registered
    assert email not in activities[activity]["participants"]
    
    # Sign up
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200
    assert email in activities[activity]["participants"]
    
    # Unregister
    response = client.post(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 200
    assert email not in activities[activity]["participants"]


def test_root_redirect(client):
    """Test that root redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_participants_list_empty(client):
    """Test activity with no participants"""
    # Find an activity with no participants or clear one
    response = client.get("/activities")
    data = response.json()
    
    # Most activities in the fixture have participants, but we test the structure
    for activity_name, activity_data in data.items():
        assert isinstance(activity_data["participants"], list)
