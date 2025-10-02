from llm import generate_sql

class DummyLLM:
    def __init__(self, response):
        self.response = response

    def __call__(self, *args, **kwargs):
        return self.response

def test_city_query(monkeypatch):
    fake_response = 'SELECT ssp5_10yr AS risk_score, \'Boston\' AS city, \'Flood\' AS hazard FROM "FloodRisk" LIMIT 1;'
    monkeypatch.setattr("llm.call_llm", lambda *a, **k: fake_response)
    
    sql = generate_sql("Flood risk in Boston?", ["flood"], region=None)
    assert "FloodRisk" in sql
    assert "Boston" in sql

def test_region_query(monkeypatch):
    fake_response = 'SELECT AVG(ssp5_10yr) AS risk_score, \'Asia\' AS region, \'Flood\' AS hazard FROM "FloodRisk" WHERE region ILIKE \'%asia%\';'
    monkeypatch.setattr("llm.call_llm", lambda *a, **k: fake_response)

    sql = generate_sql("Flood risk in Asia?", ["flood"], region="asia")
    assert "AVG" in sql
    assert "asia" in sql.lower()
