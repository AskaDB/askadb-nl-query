from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_translate():
    response = client.post("/translate/", json={
        "user_input": "How many users signed up last week?",
        "table_schema": "CREATE TABLE users (id INT, name TEXT, created_at DATE);"
    })
    assert response.status_code == 200
    assert "SELECT" in response.json()["query"].upper()
