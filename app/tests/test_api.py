import os
import pytest
from fastapi.testclient import TestClient
from app.api.app import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns the expected message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Daily Meditation API"}

def test_available_moods_endpoint():
    """Test the available-moods endpoint returns a list of moods."""
    response = client.get("/available-moods")
    assert response.status_code == 200
    assert "moods" in response.json()
    assert isinstance(response.json()["moods"], list)
    assert len(response.json()["moods"]) > 0

def test_generate_meditation_endpoint():
    """Test the generate-meditation endpoint with a simple request."""
    # Skip this test if no OpenAI API key is available (for CI environments)
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("Skipping test: No OpenAI API key available")
    
    response = client.post("/generate-meditation", json={"mood": "calm"})
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/mpeg"
    assert "Content-Disposition" in response.headers
    assert "meditation_calm.mp3" in response.headers["Content-Disposition"] 