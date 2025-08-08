import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.services import llm_service

client = TestClient(app)

class DummyLLM:
    def generate_query(self, request):
        return {
            "query": "SELECT * FROM sales LIMIT 1",
            "confidence": 0.99,
            "explanation": "ok",
            "suggested_visualizations": ["table"],
            "suggested_follow_up_questions": ["more?"]
        }

def test_translate_ok(monkeypatch):
    monkeypatch.setattr(llm_service, "LLMService", lambda: DummyLLM())

    resp = client.post("/translate/", json={"question": "vendas?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"].lower().startswith("select")
    assert data["confidence"] > 0.5
    assert isinstance(data["suggested_visualizations"], list)
