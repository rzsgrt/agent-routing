"""Simple tests for the AI Agent Backend API."""

import requests
import time
import pytest

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10


def wait_for_server():
    """Wait for the server to be ready."""
    for _ in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(1)
    return False


@pytest.fixture(scope="session", autouse=True)
def ensure_server():
    """Ensure the server is running before tests."""
    if not wait_for_server():
        pytest.skip("Server not running at http://localhost:8000")


def test_health_endpoint():
    """Test the health check endpoint."""
    response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert len(data) == 1  # Clean response


def test_root_endpoint():
    """Test the root endpoint returns API information."""
    response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "description" in data
    assert "endpoints" in data
    assert data["name"] == "AI Agent Backend"
    assert data["version"] == "1.0.0"


def test_math_tool():
    """Test math tool functionality."""
    response = requests.post(
        f"{BASE_URL}/query", json={"query": "what is 5 + 3?"}, timeout=TIMEOUT
    )
    assert response.status_code == 200

    data = response.json()

    # Verify structure
    assert "query" in data
    assert "tool_used" in data
    assert "result" in data

    # Verify content
    assert data["query"] == "what is 5 + 3?"
    assert data["tool_used"] == "math"
    assert "8" in data["result"]


def test_general_tool():
    """Test general tool functionality."""
    response = requests.post(
        f"{BASE_URL}/query", json={"query": "What is AI?"}, timeout=TIMEOUT
    )
    assert response.status_code == 200

    data = response.json()

    # Verify clean structure
    assert set(data.keys()) == {"query", "tool_used", "result"}

    assert data["query"] == "What is AI?"
    assert data["tool_used"] == "general"
    assert isinstance(data["result"], str)
    assert len(data["result"]) > 0


def test_weather_tool():
    """Test weather tool functionality."""
    response = requests.post(
        f"{BASE_URL}/query",
        json={"query": "What is the weather in Tokyo?"},
        timeout=TIMEOUT,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "What is the weather in Tokyo?"
    assert data["tool_used"] == "weather"
    assert isinstance(data["result"], str)


def test_input_validation():
    """Test input validation."""
    # Empty query
    response = requests.post(
        f"{BASE_URL}/query", json={"query": ""}, timeout=TIMEOUT
    )
    assert response.status_code == 422

    # Missing query field
    response = requests.post(
        f"{BASE_URL}/query", json={"wrong_field": "test"}, timeout=TIMEOUT
    )
    assert response.status_code == 422


def test_routing_accuracy():
    """Test that queries are routed to correct tools."""
    test_cases = [
        {"query": "calculate 42 * 7", "expected_tool": "math"},
        {"query": "what is 10 + 15?", "expected_tool": "math"},
        {"query": "tell me a joke", "expected_tool": "general"},
        {"query": "who is the president?", "expected_tool": "general"},
    ]

    for test_case in test_cases:
        response = requests.post(
            f"{BASE_URL}/query",
            json={"query": test_case["query"]},
            timeout=TIMEOUT,
        )
        assert response.status_code == 200

        data = response.json()
        actual = data["tool_used"]
        expected = test_case["expected_tool"]

        assert actual == expected, (
            f"Query '{test_case['query']}' routed to {actual}, "
            f"expected {expected}"
        )


def test_mixed_content_routing():
    """Test routing with mixed content."""
    response = requests.post(
        f"{BASE_URL}/query",
        json={"query": "I need to calculate 15 + 27 for my homework"},
        timeout=TIMEOUT,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["tool_used"] == "math"
    assert "42" in data["result"]


def test_404_handling():
    """Test 404 error handling."""
    response = requests.get(f"{BASE_URL}/nonexistent", timeout=TIMEOUT)
    assert response.status_code == 404


def test_response_consistency():
    """Test that all responses have consistent structure."""
    queries = ["what is 2 + 2?", "tell me about space"]

    for query in queries:
        response = requests.post(
            f"{BASE_URL}/query", json={"query": query}, timeout=TIMEOUT
        )
        assert response.status_code == 200

        data = response.json()

        # Verify exact structure
        assert set(data.keys()) == {"query", "tool_used", "result"}

        # Verify types
        assert isinstance(data["query"], str)
        assert isinstance(data["tool_used"], str)
        assert isinstance(data["result"], str)

        # Verify non-empty
        assert len(data["query"]) > 0
        assert len(data["tool_used"]) > 0
        assert len(data["result"]) > 0
