from llm import stream_summarize_answer

class FakeDelta:
    def __init__(self, content):
        self.content = content

class FakeChoice:
    def __init__(self, content):
        self.delta = FakeDelta(content)

class FakeChunk:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


def test_summary_low_risk(monkeypatch):
    fake_output = iter([FakeChunk("### Boston\n- **Flood Risk:** Low\n")])
    monkeypatch.setattr("llm.client.chat.completions.create", lambda *a, **k: fake_output)

    chunks = list(
        stream_summarize_answer("Flood risk in Boston?", [(2, "Boston")], "SELECT ...", "db_context")
    )
    output = "".join(chunks)

    assert "Flood Risk" in output
    assert "Boston" in output
