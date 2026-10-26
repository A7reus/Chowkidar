from __future__ import annotations

from app.agents.llm import LLMClient
from app.core.config import Settings


def _client(**values: object) -> LLMClient:
    client = LLMClient()
    client.settings = Settings(_env_file=None, **values)  # pyright: ignore[reportCallIssue]
    return client


def test_fallback_chain_skips_providers_without_credentials() -> None:
    client = _client(llm_mode="hybrid", groq_api_key="key")
    primary = client.model_for_purpose("extraction")
    assert primary == client.settings.gemini_flash_model
    assert client.is_configured(primary) is False
    assert client.fallback_models(primary) == [client.settings.groq_model]


def test_ollama_joins_the_fallback_chain_only_when_enabled() -> None:
    disabled = _client(llm_mode="hybrid", gemini_api_key="key")
    assert disabled.settings.ollama_model not in disabled.fallback_models("x")

    enabled = _client(llm_mode="hybrid", gemini_api_key="key", ollama_enabled=True)
    assert enabled.fallback_models(enabled.settings.gemini_flash_model) == [
        enabled.settings.ollama_model
    ]


def test_prefer_local_routes_every_purpose_to_ollama() -> None:
    client = _client(llm_mode="live", ollama_enabled=True, llm_prefer_local=True)
    assert client.live_enabled is True
    for purpose in ("extraction", "rationale", "verification", "classification"):
        assert client.model_for_purpose(purpose) == client.settings.ollama_model
    assert client.fallback_models(client.settings.ollama_model) == []


def test_prefer_local_is_ignored_when_ollama_is_disabled() -> None:
    client = _client(llm_mode="live", gemini_api_key="key", llm_prefer_local=True)
    assert client.model_for_purpose("extraction") == client.settings.gemini_flash_model
