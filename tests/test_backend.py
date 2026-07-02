import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from backend.main import app
import backend.history_logger as history_logger

# Use fastapi TestClient for synchronous API testing
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def setup_temp_storage(tmp_path):
    """
    Redirects history.json and feedback.json to a temporary folder
    for the duration of each test to avoid writing to development logs.
    """
    temp_history = tmp_path / "history.json"
    temp_feedback = tmp_path / "feedback.json"
    
    with patch("backend.history_logger.HISTORY_FILE", str(temp_history)), \
         patch("backend.history_logger.FEEDBACK_FILE", str(temp_feedback)):
        history_logger.init_storage()
        yield

# Test 1: Analyze Event Route
@patch("backend.main.extract_themes")
def test_analyze_event_route(mock_extract_themes, client):
    # Set mock behavior
    mock_extract_themes.return_value = ["AI", "Sustainability"]
    
    payload = {
        "event_description": "AI for Sustainable Cities",
        "interests": ["climate change", "urban planning"]
    }
    response = client.post("/analyze-event", json=payload)
    
    assert response.status_code == 200
    assert "themes" in response.json()
    assert response.json()["themes"] == ["AI", "Sustainability"]
    
    # Check validation error for empty event description
    bad_payload = {
        "event_description": "",
        "interests": ["climate change"]
    }
    response = client.post("/analyze-event", json=bad_payload)
    assert response.status_code == 400

# Test 2: Generate Conversation Route
@patch("backend.main.generate_starters")
def test_generate_conversation_route(mock_generate_starters, client):
    mock_generate_starters.return_value = [
        "How does AI optimize transit systems?",
        "What's your take on green smart grids?"
    ]
    
    payload = {
        "event_description": "AI for Sustainable Cities",
        "themes": ["AI", "Sustainability"],
        "interests": ["climate change", "urban planning"]
    }
    response = client.post("/generate-conversation", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "starters" in data
    assert len(data["starters"]) == 2
    assert data["starters"][0]["text"] == "How does AI optimize transit systems?"
    assert data["starters"][0]["feedback"] is None
    
    # Verify that the conversation is written to the history file
    history = history_logger.get_history()
    assert len(history) == 1
    assert history[0]["event_description"] == "AI for Sustainable Cities"
    assert len(history[0]["starters"]) == 2

# Test 3: Fact-Checking Route
@patch("backend.main.get_fact_check")
def test_fact_check_route(mock_get_fact_check, client):
    mock_get_fact_check.return_value = {
        "query": "blockchain in healthcare",
        "title": "Blockchain",
        "summary": "A blockchain is a distributed ledger...",
        "url": "https://en.wikipedia.org/wiki/Blockchain",
        "success": True
    }
    
    payload = {"query": "blockchain in healthcare"}
    response = client.post("/fact-check", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["title"] == "Blockchain"
    assert data["summary"] == "A blockchain is a distributed ledger..."
    
    # Test error handling when search fails
    mock_get_fact_check.return_value = {
        "query": "asdfghjkl",
        "success": False,
        "error": "Could not find a Wikipedia page matching 'asdfghjkl'."
    }
    response = client.post("/fact-check", json={"query": "asdfghjkl"})
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "error" in response.json()

# Test 4: History Retrieval Route
def test_get_history_route(client):
    # Ensure history starts empty
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json() == []
    
    # Save a mock conversation directly via logger
    history_logger.save_conversation(
        event_description="Test Event",
        interests=["test"],
        themes=["test"],
        starters=["Test starter text"]
    )
    
    response = client.get("/history")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["event_description"] == "Test Event"

# Test 5: Feedback Route
def test_submit_feedback_route(client):
    # Save a conversation first to establish a valid starter ID
    entry = history_logger.save_conversation(
        event_description="Test Event",
        interests=["test"],
        themes=["test"],
        starters=["Test starter text"]
    )
    starter_id = entry["starters"][0]["id"]
    
    payload = {
        "starter_id": starter_id,
        "feedback": "up"
    }
    response = client.post("/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify feedback was saved in history
    history = history_logger.get_history()
    assert history[0]["starters"][0]["feedback"] == "up"
    
    # Verify feedback was written to feedback logs
    feedbacks = history_logger.get_feedback()
    assert len(feedbacks) == 1
    assert feedbacks[0]["starter_id"] == starter_id
    assert feedbacks[0]["feedback"] == "up"
    
    # Validation error for invalid feedback value
    bad_payload = {
        "starter_id": starter_id,
        "feedback": "invalid_val"
    }
    response = client.post("/feedback", json=bad_payload)
    assert response.status_code == 422 # FastAPI Pydantic validation error
