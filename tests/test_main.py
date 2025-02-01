# Description: This file contains the test cases for the main.py file.
# The test cases are written to test the endpoints of the FastAPI application.

from fastapi.testclient import TestClient
from main import app, API_KEY

# Create a FastAPI test client
client = TestClient(app)


def test_reindex_endpoint_with_valid_api_key():
    response = client.post(
        "/reindex",
        headers={
            "X-API-Key": "d15d7c21-1870-48ec-a230-89ac1dfe0f5a",
            "index":  "prbnew"
        }
    )
    assert response.status_code == 200
    assert response.json() == {"status": "indexing started"}


def test_reindex_endpoint_with_invalid_api_key():
    response = client.post("/reindex", headers={"X-API-Key": "invalid-key"})
    assert response.status_code == 403
    assert response.json() == {"message": "Forbidden: Invalid or missing API key"}


def test_nonexistant_endpoint():
    response = client.post("/nonexistant")
    assert response.status_code == 403
    assert response.json() == {'message': 'Forbidden: Invalid or missing API key'}


def test_reindex_endpoint_rate_limit_exceeded():
    for _ in range(5):
        client.post("/reindex", headers={"X-API-Key": API_KEY, "index": "all"})
    response = client.post("/reindex", headers={"X-API-Key": API_KEY, "index": "all"})
    assert response.status_code == 429
    assert response.json() == {"detail": "5 per 1 minute"}


def test_reindex_endpoint_missing_index():
    response = client.post("/reindex", headers={"X-API-Key": API_KEY})
    assert response.status_code == 666
    assert response.json() == {'message': 'Missing index in request'}
