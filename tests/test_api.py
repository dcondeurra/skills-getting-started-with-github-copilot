"""
Tests for the Mergington High School API endpoints.
"""

import pytest
from fastapi import status
from src.app import activities


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check that we get a dictionary of activities
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check that each activity has required fields
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestSignupEndpoint:
    """Tests for the signup endpoint."""
    
    def test_successful_signup(self, client, reset_activities):
        """Test successful student signup for an activity."""
        # Use an existing activity
        activity_name = "Chess Club"
        email = "test@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify the participant was added
        assert email in activities[activity_name]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist."""
        response = client.post("/activities/Nonexistent Club/signup?email=test@mergington.edu")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_duplicate_signup(self, client, reset_activities):
        """Test that a student cannot sign up twice for the same activity."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up in the default data
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"
    
    def test_signup_when_activity_is_full(self, client, reset_activities):
        """Test signup when activity has reached max participants."""
        # First, fill up an activity to max capacity
        activity_name = "Chess Club"
        max_participants = activities[activity_name]["max_participants"]
        current_participants = len(activities[activity_name]["participants"])
        
        # Add participants until it's full
        for i in range(current_participants, max_participants):
            email = f"student{i}@mergington.edu"
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == status.HTTP_200_OK
        
        # Now try to add one more participant
        overflow_email = "overflow@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={overflow_email}")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"] == "Activity is full"
    
    def test_signup_with_special_characters_in_activity_name(self, client, reset_activities):
        """Test signup with URL encoding for activity names with special characters."""
        # Add a test activity with special characters
        special_activity = "Art & Crafts Club"
        activities[special_activity] = {
            "description": "Art and crafts activities",
            "schedule": "Mondays, 3:00 PM",
            "max_participants": 10,
            "participants": []
        }
        
        email = "test@mergington.edu"
        # URL encode the activity name
        encoded_activity = "Art%20%26%20Crafts%20Club"
        
        response = client.post(f"/activities/{encoded_activity}/signup?email={email}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Signed up {email} for {special_activity}"


class TestRemoveParticipantEndpoint:
    """Tests for the remove participant endpoint."""
    
    def test_successful_participant_removal(self, client, reset_activities):
        """Test successful removal of a participant from an activity."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up in default data
        
        # Verify participant is initially there
        assert email in activities[activity_name]["participants"]
        
        response = client.delete(f"/activities/{activity_name}/participants/{email}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Removed {email} from {activity_name}"
        
        # Verify the participant was removed
        assert email not in activities[activity_name]["participants"]
    
    def test_remove_participant_from_nonexistent_activity(self, client):
        """Test removing participant from an activity that doesn't exist."""
        response = client.delete("/activities/Nonexistent Club/participants/test@mergington.edu")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_remove_nonexistent_participant(self, client):
        """Test removing a participant who isn't signed up for the activity."""
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        
        response = client.delete(f"/activities/{activity_name}/participants/{email}")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"] == "Student is not signed up for this activity"
    
    def test_remove_participant_with_special_characters(self, client, reset_activities):
        """Test removing participant with URL encoding for special characters."""
        # Add a test activity and participant
        special_activity = "Art & Crafts Club"
        activities[special_activity] = {
            "description": "Art and crafts activities",
            "schedule": "Mondays, 3:00 PM",
            "max_participants": 10,
            "participants": ["test@mergington.edu"]
        }
        
        email = "test@mergington.edu"
        encoded_activity = "Art%20%26%20Crafts%20Club"
        encoded_email = "test%40mergington.edu"
        
        response = client.delete(f"/activities/{encoded_activity}/participants/{encoded_email}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Removed {email} from {special_activity}"


class TestIntegrationScenarios:
    """Integration tests for complete user workflows."""
    
    def test_complete_signup_and_removal_workflow(self, client, reset_activities):
        """Test a complete workflow of signing up and then removing a participant."""
        activity_name = "Programming Class"
        email = "workflow@mergington.edu"
        
        # Step 1: Sign up for activity
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == status.HTTP_200_OK
        assert email in activities[activity_name]["participants"]
        
        # Step 2: Verify activity list includes the participant
        activities_response = client.get("/activities")
        assert activities_response.status_code == status.HTTP_200_OK
        activity_data = activities_response.json()[activity_name]
        assert email in activity_data["participants"]
        
        # Step 3: Remove the participant
        remove_response = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert remove_response.status_code == status.HTTP_200_OK
        assert email not in activities[activity_name]["participants"]
        
        # Step 4: Verify activity list no longer includes the participant
        final_activities_response = client.get("/activities")
        assert final_activities_response.status_code == status.HTTP_200_OK
        final_activity_data = final_activities_response.json()[activity_name]
        assert email not in final_activity_data["participants"]