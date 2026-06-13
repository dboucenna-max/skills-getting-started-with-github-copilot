import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
    }
    
    activities.clear()
    activities.update(original_activities)
    yield
    activities.clear()
    activities.update(original_activities)


class TestRootEndpoint:
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html"""
        # Arrange
        expected_redirect = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert expected_redirect in response.headers["location"]


class TestGetActivities:
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test retrieving all activities"""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity in expected_activities:
            assert activity in data

    def test_get_activities_has_required_fields(self, client, reset_activities):
        """Test that activities have all required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        for activity_name, details in activities_data.items():
            for field in required_fields:
                assert field in details
            assert isinstance(details["participants"], list)

    def test_get_activities_participants_are_emails(self, client, reset_activities):
        """Test that participant entries are valid email strings"""
        # Arrange
        # (no setup needed, using fixture data)
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        for activity_name, details in activities_data.items():
            for participant in details["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant


class TestSignup:
    def test_signup_success_adds_participant(self, client, reset_activities):
        """Test successful signup for an activity"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert new_email in data["message"]
        assert activity_name in data["message"]

    def test_signup_duplicate_email_rejected(self, client, reset_activities):
        """Test that duplicate signup is rejected"""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test signup for non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_signup_persists_to_activity_participants(self, client, reset_activities):
        """Test that signup actually adds participant to the activity"""
        # Arrange
        activity_name = "Programming Class"
        new_email = "newperson@mergington.edu"
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        assert new_email in activities_data[activity_name]["participants"]


class TestUnregister:
    def test_unregister_success_removes_participant(self, client, reset_activities):
        """Test successful unregister from an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert email in data["message"]
        assert "Removed" in data["message"]

    def test_unregister_not_registered_returns_404(self, client, reset_activities):
        """Test unregister for participant not in activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test unregister from non-existent activity"""
        # Arrange
        activity_name = "Fake Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_unregister_persists_removal(self, client, reset_activities):
        """Test that unregister actually removes participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        assert email not in activities_data[activity_name]["participants"]
