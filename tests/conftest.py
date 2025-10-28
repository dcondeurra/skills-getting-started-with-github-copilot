"""
Test configuration and fixtures for the Mergington High School API tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_activities():
    """Return a sample of activities data for testing."""
    return {
        "Test Chess Club": {
            "description": "Test chess club for testing",
            "schedule": "Test schedule",
            "max_participants": 2,
            "participants": ["test1@mergington.edu"]
        },
        "Test Programming Class": {
            "description": "Test programming class",
            "schedule": "Test schedule",
            "max_participants": 3,
            "participants": []
        }
    }


@pytest.fixture
def reset_activities():
    """Reset activities to original state after each test."""
    # Store original activities
    original_activities = activities.copy()
    
    yield
    
    # Restore original activities
    activities.clear()
    activities.update(original_activities)