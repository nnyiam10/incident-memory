import pytest

from agent.policies import models


def test_openrouter_is_default_provider(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    client = models.model_client()
    assert str(client.base_url) == "https://openrouter.ai/api/v1/"
    assert models.EMBEDDING_MODEL == "openai/text-embedding-3-small"


def test_openrouter_key_is_required(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        models.model_client()
