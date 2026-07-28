import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities(self, client):
        """Test retrieving all activities."""
        # Arrange - no setup needed, activities already exist in app
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
    def test_activity_has_required_fields(self, client):
        """Test that activities have all required fields."""
        # Arrange - define expected fields
        expected_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            assert expected_fields.issubset(set(activity_data.keys())), \
                f"{activity_name} missing required fields"
            assert isinstance(activity_data["participants"], list)

    def test_activity_participants_are_strings(self, client):
        """Test that participants are stored as strings (emails)."""
        # Arrange - prepare email validation
        def is_email(value):
            return isinstance(value, str) and "@" in value
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            for participant in activity_data["participants"]:
                assert is_email(participant), \
                    f"Invalid email format: {participant} in {activity_name}"


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_participant(self, client):
        """Test signing up a new participant for an activity."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert email in data["message"]
        
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]

    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signups are rejected."""
        # Arrange
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a nonexistent activity."""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities."""
        # Arrange
        email = "multiplesports@mergington.edu"
        activities_to_join = ["Basketball", "Tennis Club"]
        
        # Act
        responses = [
            client.post(f"/activities/{activity}/signup", params={"email": email})
            for activity in activities_to_join
        ]
        verify_response = client.get("/activities")
        
        # Assert
        for response in responses:
            assert response.status_code == 200
        
        activities_data = verify_response.json()
        for activity in activities_to_join:
            assert email in activities_data[activity]["participants"]


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant."""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        activities_before = client.get("/activities").json()
        assert email in activities_before[activity]["participants"], \
            "Test setup failed: participant not found"
        
        # Act
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        activities_after = client.get("/activities").json()
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email not in activities_after[activity]["participants"]

    def test_unregister_nonparticipant(self, client):
        """Test unregistering someone not signed up."""
        # Arrange
        email = "neverSignedUp@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from a nonexistent activity."""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_and_signup_again(self, client):
        """Test that a participant can unregister and sign up again."""
        # Arrange
        email = "changingmind@mergington.edu"
        activity = "Chess Club"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Act - Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Act - Sign up again
        signup_again_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert signup_response.status_code == 200
        assert unregister_response.status_code == 200
        assert signup_again_response.status_code == 200


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_index(self, client):
        """Test that root URL redirects to index.html."""
        # Arrange - no setup needed
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]
