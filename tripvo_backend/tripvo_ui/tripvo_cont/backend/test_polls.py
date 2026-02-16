import requests
import pytest

BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="module")
def poll():
    # Create a poll
    data = {
        "question": "Where should we go?",
        "options": ["Beach", "Mountains"]
    }
    r = requests.post(f"{BASE_URL}/polls", json=data)
    r.raise_for_status()
    return r.json()

def test_create_poll(poll):
    assert poll["question"] == "Where should we go?"
    assert len(poll["options"]) == 2

def test_vote_poll(poll):
    poll_id = poll["id"]
    option_id = poll["options"][0]["id"]
    vote_data = {"user_id": "testuser", "option_id": option_id}
    r = requests.post(f"{BASE_URL}/polls/{poll_id}/vote", json=vote_data)
    assert r.status_code == 200
    result = r.json()
    assert result["success"] is True
    assert result["poll"]["votes_by_user"]["testuser"] == option_id

def test_close_poll(poll):
    poll_id = poll["id"]
    r = requests.post(f"{BASE_URL}/polls/{poll_id}/close")
    assert r.status_code == 200
    result = r.json()
    assert result["success"] is True
    assert result["poll"]["is_closed"] is True
