"""Multi-model local suite: routing, fallback, R1 reasoning handling, smoke runner.

Ollama is never contacted: LiteLLM's ``acompletion`` and the smoke script's
HTTP calls are replaced with fakes, so this runs in CI without a GPU or server.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from app.agents.llm import LLMClient, LLMUnavailable, split_reasoning
from app.core.config import Settings

SUITE = {
    "OLLAMA_MODEL": "ollama/qwen2.5:3b",
    "OLLAMA_EXTRACTION_MODEL": "llama3.2:3b",  # bare tag is normalised
    "OLLAMA_REASONING_MODEL": "ollama/deepseek-r1:1.5b",
    "OLLAMA_TRIAGE_MODEL": "ollama/gemma2:2b",
}
VALID_JSON = '{"summary": "x", "jurisdiction": "EU", "severity": "high", "obligations": [{"action": "a", "deadline": "d"}]}'


def _client(**values: object) -> LLMClient:
    client = LLMClient()
    client.settings = Settings(_env_file=None, **values)  # pyright: ignore[reportCallIssue]
    return client


def _local_suite_client(**extra: object) -> LLMClient:
    values: dict[str, object] = {
        "llm_mode": "live",
        "ollama_enabled": True,
        "llm_local_only": True,
        **{k.lower(): v for k, v in SUITE.items()},
    }
    values.update(extra)
    return _client(**values)


def _response(content: str, reasoning: str | None = None) -> SimpleNamespace:
    message = SimpleNamespace(content=content, reasoning_content=reasoning)
    usage = SimpleNamespace(prompt_tokens=11, completion_tokens=7)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


@pytest.fixture
def fake_litellm(monkeypatch: pytest.MonkeyPatch):
    """Install a fake ``litellm.acompletion`` scripted per model."""
    calls: list[dict[str, Any]] = []
    script: dict[str, Any] = {}

    async def acompletion(**kwargs: Any) -> SimpleNamespace:
        calls.append(kwargs)
        outcome = script.get(kwargs["model"], VALID_JSON)
        if isinstance(outcome, Exception):
            raise outcome
        if isinstance(outcome, SimpleNamespace):
            return outcome
        return _response(outcome)

    import litellm

    monkeypatch.setattr(litellm, "acompletion", acompletion)
    return SimpleNamespace(calls=calls, script=script)


# --- configuration -------------------------------------------------------


def test_default_suite_lists_four_local_models() -> None:
    settings = Settings(_env_file=None)  # pyright: ignore[reportCallIssue]
    assert settings.ollama_model_suite_list == [
        "ollama/qwen2.5:3b",
        "ollama/llama3.2:3b",
        "ollama/deepseek-r1:1.5b",
        "ollama/gemma2:2b",
    ]


def test_role_models_default_to_ollama_model_for_single_model_setups() -> None:
    settings = Settings(_env_file=None, ollama_model="ollama/qwen2.5:7b")  # pyright: ignore[reportCallIssue]
    assert set(settings.ollama_role_models.values()) == {"ollama/qwen2.5:7b"}


def test_role_models_are_normalised_to_litellm_ids() -> None:
    client = _local_suite_client()
    assert client.settings.ollama_role_models == {
        "extraction": "ollama/llama3.2:3b",
        "reasoning": "ollama/deepseek-r1:1.5b",
        "triage": "ollama/gemma2:2b",
    }


# --- routing -------------------------------------------------------------


@pytest.mark.parametrize(
    ("purpose", "expected"),
    [
        ("extraction", "ollama/llama3.2:3b"),
        ("verification", "ollama/deepseek-r1:1.5b"),
        ("report", "ollama/deepseek-r1:1.5b"),
        ("rationale", "ollama/gemma2:2b"),
        ("classification", "ollama/gemma2:2b"),
        ("unknown-purpose", "ollama/llama3.2:3b"),
    ],
)
def test_each_agent_purpose_routes_to_its_local_model(purpose: str, expected: str) -> None:
    assert _local_suite_client().model_for_purpose(purpose) == expected


def test_local_fallback_walks_the_rest_of_the_suite_and_never_cloud() -> None:
    client = _local_suite_client(gemini_api_key="k", groq_api_key="k")
    assert client.fallback_models("ollama/deepseek-r1:1.5b") == [
        "ollama/qwen2.5:3b",
        "ollama/llama3.2:3b",
        "ollama/gemma2:2b",
    ]


def test_prefer_local_tries_local_suite_before_cloud() -> None:
    client = _local_suite_client(llm_local_only=False, gemini_api_key="k")
    chain = client.fallback_models("ollama/gemma2:2b")
    assert chain[:3] == ["ollama/qwen2.5:3b", "ollama/llama3.2:3b", "ollama/deepseek-r1:1.5b"]
    assert chain[3] == client.settings.gemini_flash_model


def test_cloud_primary_keeps_local_suite_as_last_resort() -> None:
    client = _local_suite_client(llm_local_only=False, gemini_api_key="k")
    client.settings.llm_prefer_local = False
    chain = client.fallback_models(client.settings.gemini_flash_model)
    assert chain[0] != client.settings.gemini_flash_model
    assert chain[-4:] == client.local_models()


# --- completions through the (mocked) runtime ---------------------------


async def test_local_completion_sends_ollama_api_base_and_json_mode(fake_litellm) -> None:
    client = _local_suite_client()
    payload, result = await client.complete_json(system="s", user="u", purpose="extraction")
    call = fake_litellm.calls[0]
    assert call["model"] == "ollama/llama3.2:3b"
    assert call["api_base"] == client.settings.ollama_base_url
    assert call["response_format"] == {"type": "json_object"}
    assert "api_key" not in call
    assert payload["severity"] == "high"
    assert (result.provider, result.fallback_used) == ("ollama", False)
    assert (result.prompt_tokens, result.completion_tokens) == (11, 7)


async def test_deepseek_r1_think_block_is_stripped_before_json_parse(fake_litellm) -> None:
    fake_litellm.script["ollama/deepseek-r1:1.5b"] = (
        "<think>\nThe notice sets a deadline, so severity is high.\n</think>\n" + VALID_JSON
    )
    client = _local_suite_client()
    payload, result = await client.complete_json(system="s", user="u", purpose="verification")
    assert payload["jurisdiction"] == "EU"
    assert result.model == "ollama/deepseek-r1:1.5b"
    assert "<think>" not in result.content
    assert result.metadata["reasoning_chars"] > 0


async def test_provider_reasoning_content_is_recorded(fake_litellm) -> None:
    fake_litellm.script["ollama/deepseek-r1:1.5b"] = _response(VALID_JSON, reasoning="chain")
    _payload, result = await _local_suite_client().complete_json(
        system="s", user="u", purpose="verification"
    )
    assert result.metadata == {"reasoning_chars": len("chain")}


async def test_unpulled_model_falls_back_without_blocking_the_runtime(fake_litellm) -> None:
    fake_litellm.script["ollama/gemma2:2b"] = RuntimeError("model 'gemma2:2b' not found")
    client = _local_suite_client()
    _payload, result = await client.complete_json(system="s", user="u", purpose="rationale")
    assert result.model == "ollama/qwen2.5:3b"
    assert result.fallback_used is True
    # Only the failing model cools down; the next call still reaches the suite.
    assert client._is_cooling("ollama/gemma2:2b") is True
    assert client._is_cooling("ollama/qwen2.5:3b") is False


async def test_all_local_models_failing_raises_unavailable(fake_litellm) -> None:
    for model in _local_suite_client().local_models():
        fake_litellm.script[model] = ConnectionError("refused")
    with pytest.raises(LLMUnavailable):
        await _local_suite_client().complete(system="s", user="u", purpose="extraction")


def test_split_reasoning_handles_unterminated_think() -> None:
    assert split_reasoning("<think>still thinking") == ("", "still thinking")
    assert split_reasoning('{"a": 1}') == ('{"a": 1}', "")


# --- smoke runner script -------------------------------------------------


def _load_smoke_script():
    path = Path(__file__).resolve().parents[3] / "scripts" / "smoke_local_models.py"
    spec = importlib.util.spec_from_file_location("smoke_local_models", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_smoke_runner_reports_pass_fail_and_missing_models(monkeypatch, tmp_path) -> None:
    smoke = _load_smoke_script()

    def fake_request(base_url: str, path: str, body: dict | None, timeout: float) -> dict:
        if path == "/api/tags":
            return {
                "models": [
                    {"name": "qwen2.5:3b"},
                    {"name": "deepseek-r1:1.5b"},
                    {"name": "llama3.2:3b"},
                ]
            }
        if path == "/api/version":
            return {"version": "0.0-test"}
        assert body is not None and body["format"] == "json"
        content = {
            "qwen2.5:3b": VALID_JSON,
            "deepseek-r1:1.5b": "<think>reason</think>" + VALID_JSON,
            "llama3.2:3b": '{"summary": "missing keys"}',
        }[body["model"]]
        return {
            "message": {"content": content},
            "prompt_eval_count": 40,
            "eval_count": 20,
            "eval_duration": 2_000_000_000,
        }

    monkeypatch.setattr(smoke, "_request", fake_request)
    out = tmp_path / "bench.md"
    code = smoke.main(
        ["--models", "ollama/qwen2.5:3b,deepseek-r1:1.5b,llama3.2:3b,gemma2:2b", "--out", str(out)]
    )
    log = out.read_text()
    assert code == 1  # gemma2 not pulled, llama3.2 failed the schema
    assert "**2/4 models passed**" in log
    assert "| `deepseek-r1:1.5b` | yes | yes |" in log
    assert "not pulled (ollama pull gemma2:2b)" in log
    assert "| 10.0 |" in log  # 20 tokens / 2 s


def test_smoke_runner_exits_cleanly_when_ollama_is_down(monkeypatch, tmp_path) -> None:
    smoke = _load_smoke_script()

    def refused(*_args: Any, **_kwargs: Any) -> dict:
        raise OSError("connection refused")

    monkeypatch.setattr(smoke, "_request", refused)
    with pytest.raises(SystemExit, match="ollama serve"):
        smoke.main(["--out", str(tmp_path / "x.md")])


def test_smoke_runner_schema_check() -> None:
    smoke = _load_smoke_script()
    assert smoke.validate(json.loads(VALID_JSON)) is True
    assert smoke.validate({**json.loads(VALID_JSON), "severity": "urgent"}) is False
    assert smoke.validate({**json.loads(VALID_JSON), "obligations": []}) is False
