from fastapi.testclient import TestClient
from main import app

print(">>> stream_summarize_answer currently:", "main.stream_summarize_answer")

client = TestClient(app)

# A proper fake stream generator
def fake_stream(*a, **k):
    yield "Fallback answer"


def test_ask_endpoint_valid(monkeypatch):
    # Patch functions as imported inside main.py
    monkeypatch.setattr("main.generate_sql", lambda *a, **k: "SELECT 1;")
    monkeypatch.setattr("main.validate_sql", lambda *a, **k: True)
    monkeypatch.setattr("main.run_sql_query", lambda *a, **k: [(5,)])  # fake DB result
    monkeypatch.setattr("main.stream_summarize_answer", fake_stream)

    response = client.post("/ask", json={"query": "What is flood risk in Asia?"})
    assert response.status_code == 200
    assert "Fallback answer" in response.text







